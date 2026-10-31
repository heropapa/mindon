/* 마음온 서버 — Cloudflare Worker 하나로
   ① dist/ 화면 파일(정적 자산)과 ② '함께 있기' 실시간 방을 함께 낸다.

   /ws?room=r3   → 그 방(Room DO)에 웹소켓으로 들어감. room 이 없거나 꽉 차면 안내소(Lobby DO)가 빈 방을 정해 줌.
                   &new=1 이 붙은 연결(마음 켜기로 들어온 첫 연결)은 안내소가 '오늘 들어온 사람'으로 셈.
   /stats        → 오늘 들어온 사람·지금 함께·오늘 최고 동시·최근 14일 (JSON, 숫자만 — 개인 정보 없음)
   그 밖의 주소   → dist/ 파일.

   방 하나 108명. 위치는 받는 즉시 보내지 않고 0.2초마다 한 번에 묶어 보낸다(초당 5번).
   나가는 메시지는 요금이 없고 들어오는 메시지는 20개를 1요청으로 센다 — 그래서 한 방에 많이 모아도 싸다. */

const CAP = 108;
const NAMES_N = 108;      // 익명 이름 108개(화면 index.html 의 NAMES) — 방 정원과 같아서 한 방 안에서는 안 겹치게 나눠 줌
const TICK_MS = 200;
const STALE_MS = 70000;   // 70초 동안 아무 소식이 없으면(폰 잠김·끊김) 나간 것으로
const POSES = ['stand', 'walk', 'sit', 'breathe', 'hapjang', 'bow'];
const MODES = ['walk', 'hall', 'pond'];
const ROOM_RE = /^r[1-9][0-9]{0,4}$/;
const kst = () => new Date(Date.now() + 9 * 3600e3).toISOString();      // 'YYYY-MM-DDTHH:MM…' 한국 시간
const kstDay = () => kst().slice(0, 10);
const STATS_SINCE = '2026-10-31 09:45';   // 집계를 시작한 때(배포 13d8bf9b, 한국 시간)
const TEST_ROOM = 'r99999';               // 배포 점검(tools/check_live.mjs) 전용 방 — 안내소가 세지도, 손님을 보내지도 않음
const SWEEP_MS = 60000;
const BOW_MIN_MS = 120000;                // 108배 '마침'은 한 사람에게 2분에 한 번만 받음(실제 108배는 약 11분) — 숫자 부풀리기 막기                   // 방마다 1분에 한 번 조용히 끊긴 손님을 정리(창을 그냥 닫은 경우 등)
const JSON_HEAD = { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'public, max-age=15', 'access-control-allow-origin': '*' };

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname === '/ws') {
      if (env.REALTIME === 'off') {                    // 비상 스위치: 함께 있기만 끔(혼자 걷기는 그대로). '마음 켜기' 횟수는 계속 셈
        if (url.searchParams.get('new') === '1') ctx.waitUntil(env.LOBBY.get(env.LOBBY.idFromName('lobby')).fetch('https://lobby/hit').catch(() => {}));
        return new Response('realtime paused', { status: 503 });
      }
      if (req.headers.get('Upgrade') !== 'websocket') return new Response('websocket only', { status: 426 });
      if (!originOk(req, env)) return new Response('forbidden', { status: 403 });
      let name = url.searchParams.get('room');
      const skip = url.searchParams.get('full'), isNew = url.searchParams.get('new') === '1';
      const lobby = env.LOBBY.get(env.LOBBY.idFromName('lobby'));
      const assign = async (full, count) => {
        const q = new URLSearchParams(); if (full && ROOM_RE.test(full)) q.set('full', full); if (count) q.set('new', '1');
        return (await lobby.fetch('https://lobby/assign?' + q)).text();
      };
      // 손님이 보낸 full= 은 믿지 않음(아무 방이나 '꽉 참'으로 적어 숫자를 부풀릴 수 있음) — full 은 아래 409 재시도만 보냄
      if (!name || !ROOM_RE.test(name) || name === skip) name = await assign(null, isNew);
      else if (isNew) await lobby.fetch('https://lobby/hit').catch(() => {});     // 초대 링크로 바로 방에 들어온 사람도 셈
      // 여럿이 동시에 들어오면 안내소 숫자가 잠깐 뒤처져 꽉 찬 방을 줄 수 있음 → 그 방은 409, 여기서 다음 방으로 (최대 6번)
      for (let i = 0; i < 6; i++) {
        const room = env.ROOM.get(env.ROOM.idFromName(name));
        const h = new Headers(req.headers); h.set('x-room', name);
        const r = await room.fetch(new Request(req.url, { headers: h }));
        if (r.status !== 409) return r;
        name = await assign(name, false);
      }
      return new Response('busy', { status: 503 });
    }
    if (url.pathname === '/stats') {
      const lobby = env.LOBBY.get(env.LOBBY.idFromName('lobby')), off = env.REALTIME === 'off';
      let j; try { j = await (await lobby.fetch('https://lobby/stats' + (off ? '?off=1' : ''))).json(); }
      catch { return new Response('{"error":"busy"}', { status: 503, headers: JSON_HEAD }); }   // 배포 직후 잠깐 등
      j.realtime = !off;                                   // 함께 있기 비상 스위치 상태 (관리 화면 표시용)
      // 숫자뿐이라 어디서나 읽게 둠 (관리 화면 /admin, 소개 홈페이지 mindontemple.com 의 '지금 함께 n명' 등)
      return new Response(JSON.stringify(j, null, 1), { headers: JSON_HEAD });
    }
    return env.ASSETS.fetch(req);
  },
};

function originOk(req, env) {
  const allow = (env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
  if (!allow.length) return true;
  const o = req.headers.get('Origin') || '';
  if (!o) return true; // 브라우저는 늘 Origin 을 보냄 — 없으면 점검 도구 등 (어차피 위조 가능해 막는 의미 없음)
  return allow.includes(o) || o === new URL(req.url).origin;
}

/* 안내소: 방마다 지금 몇 명인지 알고, 108명이 안 찬 방(사람 많은 방부터)을 알려 준다.
   방 인원은 저장소에도 적어 둔다 — 안내소는 몇 초 조용하면 메모리가 비워지는데, 그때 잊으면
   다음 손님이 꽉 찬 방들에 차례로 부딪히며 빈 방을 찾게 됨(2026-10-31 부하 시험에서 발견).
   숫자가 조금 틀려도 방이 꽉 찼으면 방이 409 → Worker 가 full= 을 달고 다시 물어 스스로 맞춰진다. */
export class Lobby {
  constructor(ctx) {
    this.ctx = ctx; this.counts = new Map();
    // 하루 집계: 바뀔 때마다 바로 저장(touch) — 안내소가 잠들거나 다시 떠도 안 잃음
    this.stats = { days: {} };
    ctx.blockConcurrencyWhile(async () => {
      this.stats = (await ctx.storage.get('stats')) || { days: {} };
      for (const [k, n] of await ctx.storage.list({ prefix: 'c:' })) this.counts.set(k.slice(2), n);
    });
  }
  setCount(room, n) {                                   // 메모리 + 저장소 (저장은 기다리지 않음 — 출력 게이트가 순서를 지켜 줌)
    if (n > 0) { this.counts.set(room, n); this.ctx.storage.put('c:' + room, n); }
    else { this.counts.delete(room); this.ctx.storage.delete('c:' + room); }
  }
  today() {
    const k = kstDay(), d = this.stats.days;
    if (!d[k]) { d[k] = { enters: 0, peak: 0, peakAt: '', hours: Array(24).fill(0) }; Object.keys(d).sort().slice(0, -30).forEach(o => delete d[o]); } // 30일만 보관
    if (!d[k].hours) d[k].hours = Array(24).fill(0);  // 시간대 집계를 넣기 전에 만든 날
    return d[k];
  }
  online() { let n = 0; for (const v of this.counts.values()) n += v; return n; }
  touch() { this.ctx.storage.put('stats', this.stats); }   // 기다리지 않음 — 출력 게이트가 답보다 저장을 먼저 끝냄
  async alarm() { await this.ctx.storage.put('stats', this.stats); }   // 예전 판이 걸어 둔 알람이 와도 문제없게
  async fetch(req) {
    const url = new URL(req.url);
    if (url.pathname === '/count') {
      const { room, n } = await req.json();
      if (room === TEST_ROOM) return new Response('ok');   // 배포 점검 방은 세지 않음
      if (ROOM_RE.test(room)) this.setCount(room, n);
      const t = this.today(), on = this.online();
      if (on > t.peak) { t.peak = on; t.peakAt = kst().slice(11, 16); this.touch(); }
      return new Response('ok');
    }
    if (url.pathname === '/stats') {
      const off = url.searchParams.get('off') === '1';   // 비상 스위치로 꺼 둔 동안: 지금 인원을 셀 수 없음(0), 최고에도 안 넣음
      const t = this.today(), on = off ? 0 : this.online();
      if (on > t.peak) { t.peak = on; t.peakAt = kst().slice(11, 16); this.touch(); }   // 자정 넘어 들고나는 사람이 없어도 오늘 최고에 반영
      // 최근 14일: 오늘부터 하루씩 거꾸로, 집계 시작 전 날은 빼고, 아무도 안 온 날은 0으로
      const days = [], end = Date.parse(kstDay() + 'T00:00:00Z');
      for (let i = 0; i < 14; i++) { const k = new Date(end - i * 864e5).toISOString().slice(0, 10); if (k < STATS_SINCE.slice(0, 10)) break; days.push(k); }
      return new Response(JSON.stringify({
        date: kstDay(), now_kst: kst().slice(0, 16).replace('T', ' '), since: STATS_SINCE,
        enters_today: t.enters, bows_today: t.bows || 0, peak_online_today: t.peak, peak_at_today: t.peakAt || '', hours_today: t.hours,
        online_now: on, rooms_now: off ? 0 : this.counts.size, room_capacity: CAP,
        last14: days.map(k => { const x = this.stats.days[k] || { enters: 0, peak: 0 }; return { date: k, enters: x.enters, bows: x.bows || 0, peak: x.peak, peakAt: x.peakAt || '' }; }),
        note: 'enters = 마음 켜기로 함께 있기에 들어온 횟수(같은 사람이 다시 들어오면 또 셈). 페이지 방문 수는 Cloudflare 대시보드 Analytics.',
      }, null, 1));
    }
    if (url.pathname === '/bow') { const t = this.today(); t.bows = (t.bows || 0) + 1; this.touch(); return new Response('ok'); }   // 108배 마침
    if (url.pathname === '/hit' || url.searchParams.get('new') === '1') { const t = this.today(); t.enters++; t.hours[+kst().slice(11, 13)]++; this.touch(); }
    if (url.pathname === '/hit') return new Response('ok');
    const full = url.searchParams.get('full');
    if (full) this.setCount(full, CAP);
    // 사람이 있는 방부터 채운다(빈 방에 혼자 있지 않게). 다 찼으면 새 방.
    let best = null;
    for (const [room, n] of this.counts) if (n < CAP && (!best || n > best.n)) best = { room, n };
    if (best) { this.setCount(best.room, best.n + 1); return new Response(best.room); }
    let i = 1; while (this.counts.has('r' + i)) i++;
    this.setCount('r' + i, 1);
    return new Response('r' + i);
  }
}

/* 방: 웹소켓 휴면(Hibernation) API — 아무도 안 움직이면 잠들어 요금이 거의 안 든다.
   잠들면 메모리가 지워지므로 사람마다의 마지막 위치는 소켓에 붙여(serializeAttachment) 둔다. */
export class Room {
  constructor(ctx, env) {
    this.ctx = ctx; this.env = env;
    this.dirty = new Set(); this.left = []; this.timer = null; this.name = null;
  }

  // 지금 있다고 볼 사람: 70초 안에 소식이 있었던 소켓 (조용히 끊긴 소켓은 빼고 셈)
  live(skip) { const now = Date.now(); let n = 0; for (const w of this.ctx.getWebSockets()) { if (w === skip) continue; const a = w.deserializeAttachment(); if (a && now - a.t <= STALE_MS) n++; } return n; }
  // 70초 넘게 소식 없는 소켓을 닫고 '나감'으로 알림. 닫은 수를 돌려줌
  sweep() {
    const now = Date.now(); let k = 0;
    for (const w of this.ctx.getWebSockets()) { const a = w.deserializeAttachment(); if (a && now - a.t > STALE_MS) { this.left.push(a.id); this.dirty.delete(a.id); try { w.close(4001, 'stale'); } catch {} k++; } }
    return k;
  }
  // 1분마다: 정리하고 안내소에 지금 인원을 알림. 배포로 방이 새로 떠도(알람은 남음) 남은 숫자를 바로잡음
  async alarm() {
    if (!this.name) this.name = await this.ctx.storage.get('name');
    if (this.sweep()) this.flush();
    this.report(this.live());
    if (this.ctx.getWebSockets().length) await this.ctx.storage.setAlarm(Date.now() + SWEEP_MS);
  }

  async fetch(req) {
    this.name = req.headers.get('x-room');
    if (this.name && !this.named) { this.named = true; this.ctx.storage.put('name', this.name); }   // 알람이 방 이름을 알도록
    if (!(await this.ctx.storage.getAlarm())) await this.ctx.storage.setAlarm(Date.now() + SWEEP_MS);
    const socks = this.ctx.getWebSockets();
    // 꽉 참: 연결을 받지 않고 409 — Worker 가 안내소에 다음 방을 물어 바로 다시 붙인다(손님은 모름)
    if (socks.length >= CAP) return new Response('full', { status: 409 });
    const [client, server] = Object.values(new WebSocketPair());
    const id = crypto.randomUUID().slice(0, 8);
    // 익명 이름: 손님이 원하는 번호(nm, 기기에 기억)가 이 방에서 비어 있으면 그대로, 아니면 빈 이름 중 하나
    const want = Number.parseInt(new URL(req.url).searchParams.get('nm'), 10), used = new Set();
    for (const ws of socks) { const a = ws.deserializeAttachment(); if (a && a.nm >= 0) used.add(a.nm); }
    let nm = want >= 0 && want < NAMES_N && !used.has(want) ? want : -1;
    if (nm < 0) { const free = []; for (let i = 0; i < NAMES_N; i++) if (!used.has(i)) free.push(i); nm = free.length ? free[Math.floor(Math.random() * free.length)] : Math.floor(Math.random() * NAMES_N); }
    this.ctx.acceptWebSocket(server);
    server.serializeAttachment({ id, room: this.name, s: null, n: 0, w: Date.now(), t: Date.now(), j: Date.now(), nm, c: null });
    // 들어온 사람에게: 내 번호 + 지금 있는 사람들 전부
    const all = {};
    for (const ws of socks) { const a = ws.deserializeAttachment(); if (a && a.s) all[a.id] = a.s.concat(a.nm ?? -1, a.c ?? 0); }
    server.send(JSON.stringify({ t: 'hi', id, room: this.name, cap: CAP, nm, u: all }));
    this.report(this.live());
    return new Response(null, { status: 101, webSocket: client });
  }

  webSocketMessage(ws, msg) {
    if (typeof msg !== 'string' || msg.length > 200) return;
    const a = ws.deserializeAttachment(); if (!a) return;
    // 초당 12번 넘게 보내면 그 1초는 무시
    const now = Date.now();
    if (now - a.w > 1000) { a.w = now; a.n = 0; }
    if (++a.n > 12) return;
    let d; try { d = JSON.parse(msg); } catch { return; }
    if (!d || d.t !== 'p') return;
    const s = clean(d);
    if (!s) return;
    // 108배 마친 횟수: 처음 받은 값은 기준, 그 뒤로는 1씩·2분 간격일 때만 올림 → 올라가면 안내소에 '마침' 하나
    const c = Number.isInteger(d.c) && d.c >= 0 && d.c <= 999 ? d.c : null;
    let bowed = false;
    if (c !== null) {
      if (a.c == null) a.c = c;
      else if (c === a.c + 1 && now - (a.cAt || a.j || 0) >= BOW_MIN_MS) { a.c = c; a.cAt = now; bowed = true; }
    }
    a.s = s; a.t = now; ws.serializeAttachment(a);
    this.dirty.add(a.id); this.schedule();
    if (bowed && (this.name || a.room) !== TEST_ROOM) {
      const lobby = this.env.LOBBY.get(this.env.LOBBY.idFromName('lobby'));
      this.ctx.waitUntil(lobby.fetch('https://lobby/bow', { method: 'POST' }).catch(() => {}));
    }
  }

  webSocketClose(ws) { this.gone(ws); }
  webSocketError(ws) { this.gone(ws); }

  gone(ws) {
    const a = ws.deserializeAttachment();
    if (a) { this.left.push(a.id); this.dirty.delete(a.id); }
    try { ws.close(1000, 'bye'); } catch {}
    this.schedule();
    this.report(this.live(ws), a && a.room);
  }

  schedule() {
    if (this.timer) return;
    this.timer = setTimeout(() => { this.timer = null; this.flush(); }, TICK_MS);
  }

  flush() {
    if (!this.dirty.size && !this.left.length) return;
    const u = {};
    this.sweep();
    const socks = this.ctx.getWebSockets();
    for (const ws of socks) {
      const a = ws.deserializeAttachment();
      if (a && this.dirty.has(a.id) && a.s) u[a.id] = a.s.concat(a.nm ?? -1, a.c ?? 0);   // [x,z,방향,동작,장소,이름번호,108배 마친 횟수]
    }
    const msg = JSON.stringify({ t: 's', u, l: this.left });
    this.dirty.clear(); this.left = [];
    for (const ws of socks) { try { ws.send(msg); } catch {} }
  }

  report(n, room) {
    const name = this.name || room;
    if (!name) return;
    const lobby = this.env.LOBBY.get(this.env.LOBBY.idFromName('lobby'));
    this.ctx.waitUntil(lobby.fetch('https://lobby/count', { method: 'POST', body: JSON.stringify({ room: name, n }) }).catch(() => {}));
  }
}

// 받은 위치는 믿지 않는다: 숫자 범위·동작 이름을 정해진 것으로만
function clean(d) {
  const num = (v, lo, hi) => (typeof v === 'number' && isFinite(v) ? Math.round(Math.max(lo, Math.min(hi, v)) * 100) / 100 : null);
  const x = num(d.x, -40, 40), z = num(d.z, -60, 45);
  const f = typeof d.f === 'number' && isFinite(d.f) ? Math.round(Math.atan2(Math.sin(d.f), Math.cos(d.f)) * 100) / 100 : 0; // 방향은 ±π 로 접음
  if (x === null || z === null) return null;
  return [x, z, f || 0, POSES.indexOf(d.p) < 0 ? 0 : POSES.indexOf(d.p), MODES.indexOf(d.m) < 0 ? 0 : MODES.indexOf(d.m)];
}
