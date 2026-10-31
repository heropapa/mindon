// 배포된 마음온이 제대로 도는지 확인: 화면 파일들 + 함께 있기(/ws) 두 명 접속
//   node tools/check_live.mjs https://maumon.<계정>.workers.dev
const base = (process.argv[2] || '').replace(/\/$/, '');
if (!/^https?:\/\//.test(base)) { console.error('주소를 주세요: node check_live.mjs https://...'); process.exit(2); }
let bad = 0;
const ok = (good, msg) => { console.log((good ? 'OK  ' : 'FAIL') + '  ' + msg); if (!good) bad++; };

for (const p of ['/', '/privacy.html', '/terms.html', '/credits.html', '/admin', '/stats', '/robots.txt', '/img/og.jpg',
  '/avatar/mindon-duck.gltf.json', '/avatar/mindon-duck-lite.gltf.json', '/avatar/mindon-duck-far.gltf.json',
  '/buddha/buddha-gilt.gltf.json', '/audio/jukbi-1.mp3']) {
  try { const r = await fetch(base + p, { method: p === '/' ? 'GET' : 'HEAD' });
    let extra = '';
    if (p === '/') { const t = await r.text(); extra = t.includes('maumon:ws') && t.includes('og:image') ? ' (head·meta 있음)' : ' (head 확인 필요)'; if (!t.includes('og:image')) bad++; }
    ok(r.status === 200, `${r.status} ${p}${extra}`);
  } catch (e) { ok(false, `${p} ${e.message}`); }
}
const html = await (await fetch(base + '/privacy.html')).text().catch(() => '');
ok(!html.includes('class="todo"'), '개인정보처리방침 빈칸 없음' + (html.includes('class="todo"') ? ' — make_pages.py --operator --email --date 로 채우기' : ''));

// 함께 있기: 두 명이 같은 방에 들어가 서로 보이는지
const wsUrl = base.replace(/^http/, 'ws') + '/ws';
const join = room => new Promise((res, rej) => {
  const w = new WebSocket(wsUrl + (room ? '?room=' + room : ''));
  const t = setTimeout(() => rej(new Error('8초 안에 답 없음')), 8000);
  w.onmessage = e => { const d = JSON.parse(e.data); if (d.t === 'hi') { clearTimeout(t); res({ w, d }); } };
  w.onerror = () => { clearTimeout(t); rej(new Error('연결 실패')); };
});
try {
  const a = await join('r99999'); ok(true, `/ws 접속 → 방 ${a.d.room} (점검 전용 방 — 운영 숫자에 안 섞임, 정원 ${a.d.cap})`);
  const b = await join(a.d.room);
  const seen = new Promise(res => { a.w.onmessage = e => { const d = JSON.parse(e.data); if (d.t === 's' && d.u[b.d.id]) res(true); }; setTimeout(() => res(false), 4000); });
  b.w.send(JSON.stringify({ t: 'p', x: 1, z: 2, f: 0, p: 'walk', m: 'walk' }));
  ok(await seen, '두 번째 사람의 위치가 첫 번째 사람에게 보임');
  a.w.close(); b.w.close();
} catch (e) { ok(false, '/ws ' + e.message); }

console.log(bad ? `\n문제 ${bad}개` : '\n모두 정상');
process.exit(bad ? 1 : 0);
