/* 마음온 도반 오리 (가칭 심덕) — three.js r128 아바타. 컨셉 보드 「심덕」 기준.
 * 사용: const duck = new MaumDuck(); scene.add(duck.root); duck.setPose('hapjang'); 매 프레임 duck.update(dt)
 * 단위: 씬 유닛. 발바닥 y=0, 머리 꼭대기 y≈1.56. 정면은 +z.
 * root = { rig(몸, 포즈에 따라 내려앉음), 좌복, 연잎 }. 이동·회전은 root 에.
 */
(function (global) {
  const T = global.THREE;

  const COLORS = {
    cream:   0xf9e9b9, // 몸·머리·손 (연노랑 크림)
    beak:    0xf0953f, // 부리·발 (주황)
    beakDark:0xd87a2a, // 부리 아래
    cheek:   0xf2b1a8, // 볼터치
    ink:     0x1a1714, // 눈
    robe:    0xd6d1c7, // 저고리·소매 (밝은 회색)
    lapel:   0xefebe3, // 깃 (저고리보다 밝게)
    lapelEdge:0xb9b3a7, // 깃 가장자리 선
    sash:    0x8a6240, // 가사 띠 (갈색)
    sashLight:0xb08a5e, // 가사 띠 위 밝은 줄
    gilt:    0xc9a24f, // 버클
    lotus:   0xf08aa6, // 가방 구슬 장식
    belt:    0x6b4a30, // 허리끈 (갈색)
    pack:    0x8a6240, // 걸망
    packDark:0x5a3f28, // 걸망 덮개·멜빵
    cushion: 0x4a4650, // 좌복 (회보라 방석)
    leaf:    0x6f9a5a  // 연잎
  };

  function mat(c, extra) { return new T.MeshStandardMaterial(Object.assign({ color: c, roughness: 0.7, metalness: 0 }, extra || {})); }
  function sphere(r, c, sx, sy, sz) { const m = new T.Mesh(new T.SphereGeometry(r, 40, 28), mat(c)); m.scale.set(sx || 1, sy || 1, sz || 1); return m; }
  // 회전체: [반지름, 세계 y] 목록 → torso 로컬(y-0.22)
  function lathe(profile, c, segs) { const pts = profile.map(p => new T.Vector2(p[0], p[1] - 0.22)); return new T.Mesh(new T.LatheGeometry(pts, segs || 48), mat(c)); }

  function MaumDuck() {
    this.root = new T.Group();
    this.t = 0; this.pose = 'stand'; this.blend = 1;
    this.cur = {}; this.from = {}; this.to = {};

    const rig = this.rig = new T.Group(); this.root.add(rig);
    const hips = this.hips = new T.Group(); rig.add(hips);

    // ── 다리·물갈퀴 발 (피벗: 고관절)
    this.legs = [-1, 1].map(side => {
      const p = new T.Group(); p.position.set(side * 0.13, 0.22, 0.02);
      const leg = new T.Mesh(new T.CylinderGeometry(0.04, 0.045, 0.20, 16), mat(COLORS.beak)); leg.position.y = -0.10; p.add(leg);
      const foot = sphere(1, COLORS.beak, 0.11, 0.035, 0.17); foot.position.set(0, -0.20, 0.06); p.add(foot);
      [-1, 0, 1].forEach(k => { const toe = sphere(1, COLORS.beak, 0.035, 0.03, 0.07); toe.position.set(k * 0.06, -0.20, 0.19); p.add(toe); });
      hips.add(p); return p;
    });

    // ── 몸통 (피벗 y 0.22). 저고리를 입은 몸 전체를 둥근 회전체 하나로
    const torso = this.torso = new T.Group(); torso.position.y = 0.22; hips.add(torso);
    const body = lathe([[0.40, 0.22], [0.45, 0.30], [0.46, 0.42], [0.43, 0.56], [0.36, 0.70], [0.26, 0.82], [0.14, 0.90], [0.0, 0.93]], COLORS.robe);
    torso.add(body);
    const hem = new T.Mesh(new T.TorusGeometry(0.40, 0.012, 8, 56), mat(COLORS.robe)); hem.rotation.x = Math.PI / 2; hem.position.y = 0.0; torso.add(hem);

    // ── 옷: 몸 표면을 따라 흐르는 납작한 띠(리본)로 깃·가사·허리끈·멜빵을 만든다
    const PROFILE = [[0.40, 0.22], [0.45, 0.30], [0.46, 0.42], [0.43, 0.56], [0.36, 0.70], [0.26, 0.82], [0.14, 0.90], [0.0, 0.93]];
    const surfaceR = y => { for (let i = 1; i < PROFILE.length; i++) { const [r0, y0] = PROFILE[i - 1], [r1, y1] = PROFILE[i]; if (y <= y1) { const k = (y - y0) / (y1 - y0); return r0 + (r1 - r0) * Math.max(0, Math.min(1, k)); } } return 0; };
    // 점: [θ(라디안, +z 가 0, x+ 로 양수), 세계 y]. 몸 표면에서 lift 만큼 띄운다
    const onBody = (th, y, lift) => { const r = surfaceR(y) + lift; return new T.Vector3(r * Math.sin(th), y - 0.22, r * Math.cos(th)); };
    function ribbon(pts, width, lift, color, closed, taper) {
      const curve = new T.CatmullRomCurve3(pts.map(p => onBody(p[0], p[1], lift)), !!closed, 'centripetal');
      const N = closed ? 64 : 40, pos = [], idx = [];
      for (let i = 0; i <= N; i++) { const u = i / N, P = curve.getPointAt(u), Tn = curve.getTangentAt(u);
        const nrm = new T.Vector3(P.x, 0, P.z).normalize(), side = new T.Vector3().crossVectors(Tn, nrm).normalize();
        const w = width * (taper ? (0.55 + 0.45 * Math.sin(u * Math.PI)) : 1) / 2;
        const a = P.clone().addScaledVector(side, w), b = P.clone().addScaledVector(side, -w);
        pos.push(a.x, a.y, a.z, b.x, b.y, b.z);
        if (i < N) { const k = i * 2; idx.push(k, k + 1, k + 2, k + 1, k + 3, k + 2); } }
      const g = new T.BufferGeometry(); g.setAttribute('position', new T.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
      const m = new T.Mesh(g, mat(color, { side: T.DoubleSide })); torso.add(m); return m;
    }
    // 속옷: V자 깃 사이로 보이는 크림색
    const inner = sphere(1, COLORS.cream, 0.13, 0.12, 0.04); inner.position.set(0, 0.60, 0.325); torso.add(inner);
    // V자 깃: 왼쪽 깃 위에 오른쪽 깃이 겹침
    ribbon([[-0.95, 0.90], [-0.55, 0.78], [-0.15, 0.62], [0.08, 0.50]], 0.085, 0.012, COLORS.lapel, false);
    ribbon([[-0.95, 0.90], [-0.55, 0.78], [-0.15, 0.62], [0.08, 0.50]], 0.012, 0.016, COLORS.lapelEdge, false);
    ribbon([[0.95, 0.90], [0.55, 0.78], [0.15, 0.62], [-0.08, 0.50]], 0.085, 0.022, COLORS.lapel, false);
    ribbon([[0.95, 0.90], [0.55, 0.78], [0.15, 0.62], [-0.08, 0.50]], 0.012, 0.026, COLORS.lapelEdge, false);
    // 가사 띠: 왼쪽 어깨 → 가슴 → 오른쪽 허리 → 등 → 왼쪽 어깨 (닫힌 고리), 위에 밝은 줄 하나
    const KASA = [[-1.05, 0.84], [-0.5, 0.74], [0.05, 0.62], [0.65, 0.48], [1.3, 0.38], [2.1, 0.36], [2.9, 0.46], [3.6, 0.62], [4.3, 0.76], [4.9, 0.85]];
    ribbon(KASA, 0.12, 0.014, COLORS.sash, true);
    ribbon(KASA, 0.03, 0.022, COLORS.sashLight, true);
    const kasaRing = new T.Mesh(new T.TorusGeometry(0.045, 0.014, 8, 24), mat(COLORS.belt)); kasaRing.position.copy(onBody(-1.05, 0.84, 0.03)); kasaRing.lookAt(0, 0.84 - 0.22, 0); torso.add(kasaRing);
    // 허리끈: 몸을 한 바퀴, 앞에 매듭
    const BELT = []; for (let i = 0; i < 12; i++) BELT.push([i / 12 * Math.PI * 2, 0.40 - 0.01 * Math.cos(i / 12 * Math.PI * 2)]);
    ribbon(BELT, 0.075, 0.014, COLORS.belt, true);
    const knotL = sphere(1, COLORS.belt, 0.055, 0.04, 0.035); knotL.position.copy(onBody(0.16, 0.40, 0.03)); torso.add(knotL);
    const knotR = sphere(1, COLORS.belt, 0.055, 0.04, 0.035); knotR.position.copy(onBody(-0.04, 0.40, 0.03)); torso.add(knotR);
    const knotTail = new T.Mesh(new T.BoxGeometry(0.03, 0.12, 0.01), mat(COLORS.belt)); knotTail.position.copy(onBody(0.06, 0.33, 0.03)); knotTail.rotation.z = 0.15; torso.add(knotTail);
    // 걸망: 모서리 둥근 가방 + 덮개 + 버클 + 멜빵
    const rrect = (w, h, r) => { const sh = new T.Shape(); sh.moveTo(-w / 2 + r, -h / 2); sh.lineTo(w / 2 - r, -h / 2); sh.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r); sh.lineTo(w / 2, h / 2 - r); sh.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2); sh.lineTo(-w / 2 + r, h / 2); sh.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r); sh.lineTo(-w / 2, -h / 2 + r); sh.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2); return sh; };
    const packGeo = new T.ExtrudeGeometry(rrect(0.30, 0.30, 0.07), { depth: 0.11, bevelEnabled: true, bevelThickness: 0.025, bevelSize: 0.025, bevelSegments: 4 });
    const pack = new T.Mesh(packGeo, mat(COLORS.pack)); pack.position.set(0, 0.40, -0.50); pack.rotation.x = 0.08; torso.add(pack);
    const flap = new T.Mesh(new T.ExtrudeGeometry(rrect(0.31, 0.15, 0.06), { depth: 0.022, bevelEnabled: true, bevelThickness: 0.01, bevelSize: 0.01, bevelSegments: 2 }), mat(COLORS.packDark));
    flap.position.set(0, 0.485, -0.555); flap.rotation.x = 0.08; torso.add(flap);
    const buckle = new T.Mesh(new T.TorusGeometry(0.028, 0.009, 8, 20), mat(COLORS.gilt)); buckle.position.set(0, 0.44, -0.58); torso.add(buckle);
    const bead = sphere(0.03, COLORS.lotus); bead.position.set(0.17, 0.33, -0.52); torso.add(bead);
    const beadStr = new T.Mesh(new T.CylinderGeometry(0.004, 0.004, 0.06, 6), mat(COLORS.packDark)); beadStr.position.set(0.17, 0.37, -0.52); torso.add(beadStr);
    [-1, 1].forEach(s => ribbon([[Math.PI - s * 0.45, 0.70], [Math.PI - s * 0.75, 0.84], [s * 0.85, 0.88], [s * 0.55, 0.74], [s * 0.42, 0.60]], 0.05, 0.016, COLORS.packDark, false));

    // ── 소매 + 손 (피벗: 어깨). 넓게 늘어지는 소매(회전체) 끝에 크림색 소맷단과 손
    this.wings = [-1, 1].map(side => {
      const p = new T.Group(); p.position.set(side * 0.36, 0.56, 0.10); p.userData.side = side;
      const sg = new T.LatheGeometry([[0.07, 0.03], [0.10, -0.05], [0.14, -0.16], [0.155, -0.26], [0.13, -0.28], [0.0, -0.28]].map(q => new T.Vector2(q[0], q[1])), 28);
      const sleeve = new T.Mesh(sg, mat(COLORS.robe, { side: T.DoubleSide })); p.add(sleeve);
      const cuff = new T.Mesh(new T.TorusGeometry(0.13, 0.018, 8, 32), mat(COLORS.lapel)); cuff.rotation.x = Math.PI / 2; cuff.position.y = -0.27; p.add(cuff);
      const hand = sphere(1, COLORS.cream, 0.085, 0.07, 0.095); hand.position.y = -0.31; p.add(hand);
      torso.add(p); return p;
    });

    // ── 머리 (피벗: 목, torso 로컬 y 0.66 = 세계 0.88). 머리가 몸 위에 겹쳐 앉음
    const neck = this.neck = new T.Group(); neck.position.y = 0.66; torso.add(neck);
    const head = sphere(0.44, COLORS.cream, 1.0, 0.96, 1.0); head.position.y = 0.26; neck.add(head);
    // 머리 위 잔털 세 가닥
    [[0, 0.68, 0.0, 0.15, 0.0], [-0.07, 0.67, 0.04, 0.35, 0.3], [0.06, 0.67, -0.03, -0.3, -0.25]].forEach(a => {
      const h = new T.Mesh(new T.ConeGeometry(0.022, 0.12, 8), mat(COLORS.cream)); h.position.set(a[0], a[1], a[2]); h.rotation.set(a[4], 0, a[3]); neck.add(h); });
    this.eyes = [-1, 1].map(s => {
      const e = sphere(0.065, COLORS.ink, 1, 1.25, 0.5); e.position.set(s * 0.17, 0.27, 0.405); neck.add(e);
      const hi = sphere(0.02, 0xffffff); hi.position.set(0.02, 0.03, 0.05); e.add(hi);
      const hi2 = sphere(0.01, 0xffffff); hi2.position.set(-0.025, -0.025, 0.05); e.add(hi2);
      const cheek = sphere(1, COLORS.cheek, 0.08, 0.055, 0.03); cheek.position.set(s * 0.31, 0.14, 0.30); neck.add(cheek);
      return e;
    });
    const beakU = sphere(1, COLORS.beak, 0.14, 0.075, 0.11); beakU.position.set(0, 0.15, 0.44); neck.add(beakU);
    const beakL = sphere(1, COLORS.beakDark, 0.11, 0.05, 0.09); beakL.position.set(0, 0.10, 0.43); neck.add(beakL);

    // ── 소품
    const cushion = new T.Mesh(new T.CylinderGeometry(0.58, 0.62, 0.10, 40), mat(COLORS.cushion)); cushion.position.y = 0.05; cushion.visible = false; this.root.add(cushion);
    const leaf = new T.Mesh(new T.CylinderGeometry(0.95, 0.92, 0.04, 48), mat(COLORS.leaf)); leaf.position.y = 0.02; leaf.visible = false; this.root.add(leaf);
    const vein = new T.Mesh(new T.TorusGeometry(0.6, 0.008, 6, 48), mat(0x5a8247)); vein.rotation.x = Math.PI / 2; vein.position.y = 0.045; leaf.add(vein);
    this.props = { cushion, leaf };

    this.root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    this.setPose('stand', true);
  }

  // 포즈 사전: 각도는 라디안. wing/leg 배열은 [앞으로, 안쪽/바깥쪽으로]
  const POSES = {
    stand:   { rootY: 0,     torsoX: 0,    headX: 0,    wing: [0.15, 0.1],  leg: [0, 0],        eye: 1,    prop: null },
    walk:    { rootY: 0,     torsoX: 0.05, headX: 0.05, wing: [0.15, 0.15], leg: [0, 0],        eye: 1,    prop: null },
    sit:     { rootY: -0.14, torsoX: 0.04, headX: 0.08, wing: [-0.6, 0.4],  leg: [-1.55, 0.9],  eye: 1,    prop: 'cushion' },
    breathe: { rootY: -0.18, torsoX: 0.02, headX: 0.12, wing: [-0.6, 0.4],  leg: [-1.55, 0.9],  eye: 0.12, prop: 'leaf' },
    hands:   { rootY: 0,     torsoX: 0.03, headX: 0.14, wing: [-1.25, 1.0], leg: [0, 0],        eye: 0.6,  prop: null }, // 합장: 손 모음
    halfbow: { rootY: 0,     torsoX: 0.5,  headX: 0.49, wing: [-1.25, 1.0], leg: [0, 0],        eye: 0.3,  prop: null }, // 합장: 반배로 숙임
    kneel:   { rootY: -0.14, torsoX: 0.15, headX: 0.1,  wing: [-0.4, 0.2],  leg: [-1.45, 0.15], eye: 1,    prop: 'cushion' },
    prostrate:{ rootY: -0.16, torsoX: 1.25, headX: 0.45, wing: [-1.7, 0.25], leg: [-1.45, 0.15], eye: 0.12, prop: 'cushion' }
  };
  // 시퀀스 동작: [포즈, 초]. loop=false 면 한 번 재생 후 마지막 포즈에 머문다 (duck.done 이 true, onDone 호출)
  const SEQUENCES = {
    bow:     { loop: true,  steps: [['stand', 0.48], ['kneel', 0.72], ['prostrate', 1.2], ['kneel', 0.64], ['stand', 0.96]] }, // 큰절 한 번 = 4초
    hapjang: { loop: false, steps: [['hands', 0.8], ['halfbow', 1.3], ['halfbow', 0.7], ['hands', 1.2]] }                    // 반배: 모으기→숙이기→머물기→일어나기
  };
  MaumDuck.POSES = POSES; MaumDuck.SEQUENCES = SEQUENCES; MaumDuck.COLORS = COLORS;

  const ease = x => x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
  const lerp = (a, b, k) => a + (b - a) * k;
  function mix(a, b, k) {
    return { rootY: lerp(a.rootY, b.rootY, k), torsoX: lerp(a.torsoX, b.torsoX, k), headX: lerp(a.headX, b.headX, k),
      wing: [lerp(a.wing[0], b.wing[0], k), lerp(a.wing[1], b.wing[1], k)], leg: [lerp(a.leg[0], b.leg[0], k), lerp(a.leg[1], b.leg[1], k)],
      eye: lerp(a.eye, b.eye, k), prop: k < 0.5 ? a.prop : b.prop };
  }

  MaumDuck.prototype.setPose = function (name, instant, onDone) {
    this.pose = name; this.t = 0; this.done = false; this.onDone = onDone || null;
    const seq = SEQUENCES[name];
    const target = seq ? POSES[seq.steps[0][0]] : POSES[name];
    this.from = this.cur.rootY === undefined ? target : Object.assign({}, this.cur);
    this.to = target; this.blend = instant ? 1 : 0;
  };

  MaumDuck.prototype.apply = function (p, t) {
    const breathing = this.pose === 'breathe';
    const period = breathing ? 8 : 4;
    const br = Math.sin(t * Math.PI * 2 / period);
    const amp = breathing ? 0.035 : 0.012;
    this.rig.position.y = p.rootY + (this.pose === 'walk' ? Math.abs(Math.sin(t * Math.PI * 2 * 1.6)) * 0.025 : 0);
    this.torso.rotation.x = p.torsoX;
    this.torso.scale.set(1 - br * amp * 0.5, 1 + br * amp, 1 - br * amp * 0.5);
    this.neck.rotation.x = p.headX + br * 0.01;
    this.neck.rotation.y = this.pose === 'walk' ? Math.sin(t * Math.PI * 2 * 0.8) * 0.08 : 0;
    const swing = this.pose === 'walk' ? Math.sin(t * Math.PI * 2 * 1.6) : 0;
    this.wings.forEach(w => { const s = w.userData.side;
      w.rotation.x = p.wing[0] + swing * -s * 0.35;
      w.rotation.z = -s * p.wing[1];
    });
    this.legs.forEach((l, i) => { const s = i === 0 ? -1 : 1;
      l.rotation.x = p.leg[0] + swing * s * 0.55;
      l.rotation.z = s * p.leg[1];
    });
    this.eyes.forEach(e => { e.scale.y = 1.25 * p.eye; });
    this.props.cushion.visible = p.prop === 'cushion';
    this.props.leaf.visible = p.prop === 'leaf';
  };

  MaumDuck.prototype.update = function (dt) {
    this.t += dt;
    let p;
    const seq = SEQUENCES[this.pose];
    if (seq) {
      const steps = seq.steps, total = steps.reduce((a, s) => a + s[1], 0);
      let u = seq.loop ? this.t % total : Math.min(this.t, total);
      let acc = 0, p0 = this.from, p1 = POSES[steps[0][0]], k = 1;
      for (let i = 0; i < steps.length; i++) { const [n, len] = steps[i];
        if (u < acc + len || i === steps.length - 1) {
          p0 = i === 0 ? (seq.loop ? POSES[steps[steps.length - 1][0]] : this.from) : POSES[steps[i - 1][0]];
          p1 = POSES[n]; k = Math.min(1, (u - acc) / len); break; }
        acc += len; }
      p = mix(p0, p1, ease(Math.min(1, k * 1.25)));
      if (!seq.loop && !this.done && this.t >= total) { this.done = true; if (this.onDone) this.onDone(); }
    } else {
      this.blend = Math.min(1, this.blend + dt / 0.6);
      p = mix(this.from, this.to, ease(this.blend));
    }
    this.cur = p; this.apply(p, this.t);
  };

  global.MaumDuck = MaumDuck;
})(window);
