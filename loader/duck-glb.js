/* 마음온 도반 오리 — Blender GLB 버전 로더 (three.js r128 + GLTFLoader)
 * 사용: const duck = new MaumDuckGLB('maumon-duck.glb' | ArrayBuffer | base64문자열, d => scene.add(d.root)); duck.setPose('hapjang'); duck.update(dt)
 * API는 duck.js(MaumDuck)와 같다: setPose(name, instant, onDone) / update(dt) / root / done
 * GLB 노드 이름: hips, torso, neck, wingL, wingR, legL, legR, eyeL, eyeR (Blender 계층 그대로)
 * 좌표: Blender(Z위, 얼굴 +Y) → glTF(Y위, 얼굴 -Z). root를 Y축 180° 돌려 duck.js처럼 +z를 보게 한다.
 */
(function (global) {
  const T = global.THREE;

  const POSES = {
    stand:   { rootY: 0,     torsoX: 0,    headX: 0,    wing: [-0.15, 0.1], leg: [0, 0],        eye: 1 },
    walk:    { rootY: 0,     torsoX: 0.05, headX: 0.05, wing: [-0.15, 0.15], leg: [0, 0],       eye: 1 },
    sit:     { rootY: -0.14, torsoX: 0.04, headX: 0.08, wing: [-0.6, 0.4],  leg: [-1.55, 0.9],  eye: 1 },
    breathe: { rootY: -0.18, torsoX: 0.02, headX: 0.12, wing: [-0.6, 0.4],  leg: [-1.55, 0.9],  eye: 0.12 },
    hands:   { rootY: 0,     torsoX: 0.03, headX: 0.14, wing: [-1.25, 1.0], leg: [0, 0],        eye: 0.6 },
    halfbow: { rootY: 0,     torsoX: 0.5,  headX: 0.49, wing: [-1.25, 1.0], leg: [0, 0],        eye: 0.3 },
    kneel:   { rootY: -0.14, torsoX: 0.15, headX: 0.1,  wing: [-0.4, 0.2],  leg: [-1.45, 0.15], eye: 1 },
    prostrate:{ rootY: -0.16, torsoX: 1.25, headX: 0.45, wing: [-1.7, 0.25], leg: [-1.45, 0.15], eye: 0.12 }
  };
  const SEQUENCES = {
    bow:     { loop: true,  steps: [['stand', 0.48], ['kneel', 0.72], ['prostrate', 1.2], ['kneel', 0.64], ['stand', 0.96]] },
    hapjang: { loop: false, steps: [['hands', 0.8], ['halfbow', 1.3], ['halfbow', 0.7], ['hands', 1.2]] }
  };
  const ease = x => x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
  const lerp = (a, b, k) => a + (b - a) * k;
  const mix = (a, b, k) => ({ rootY: lerp(a.rootY, b.rootY, k), torsoX: lerp(a.torsoX, b.torsoX, k), headX: lerp(a.headX, b.headX, k),
    wing: [lerp(a.wing[0], b.wing[0], k), lerp(a.wing[1], b.wing[1], k)], leg: [lerp(a.leg[0], b.leg[0], k), lerp(a.leg[1], b.leg[1], k)], eye: lerp(a.eye, b.eye, k) });

  function MaumDuckGLB(url, onLoad) {
    this.root = new T.Group(); this.root.rotation.y = Math.PI;
    this.t = 0; this.pose = 'stand'; this.blend = 1; this.cur = {}; this.from = POSES.stand; this.to = POSES.stand; this.ready = false;
    const self = this;
    const loader = new T.GLTFLoader();
    const onGltf = gltf => {
      const s = gltf.scene; self.root.add(s);
      const get = n => s.getObjectByName(n);
      self.hips = get('hips'); self.torso = get('torso'); self.neck = get('neck');
      self.wings = [get('wingL'), get('wingR')]; self.legs = [get('legL'), get('legR')]; self.eyes = [get('eyeL'), get('eyeR')];
      self.base = { hipsY: self.hips.position.y, eyeY: self.eyes[0].scale.y };
      s.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.geometry.computeVertexNormals(); } });
      self.ready = true; self.setPose(self.pose, true); if (onLoad) onLoad(self);
    };
    // url: 파일 경로, ArrayBuffer, 또는 base64 문자열(페이지에 내장한 GLB)
    if (url instanceof ArrayBuffer) loader.parse(url, '', onGltf);
    else if (typeof url === 'string' && !/[./]/.test(url.slice(0, 2)) && url.length > 1000) { const bin = atob(url), buf = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i); loader.parse(buf.buffer, '', onGltf); }
    else loader.load(url, onGltf);
  }
  MaumDuckGLB.POSES = POSES; MaumDuckGLB.SEQUENCES = SEQUENCES;

  MaumDuckGLB.prototype.setPose = function (name, instant, onDone) {
    this.pose = name; this.t = 0; this.done = false; this.onDone = onDone || null;
    const seq = SEQUENCES[name]; const target = seq ? POSES[seq.steps[0][0]] : POSES[name];
    this.from = this.cur.rootY === undefined ? target : Object.assign({}, this.cur);
    this.to = target; this.blend = instant ? 1 : 0;
  };

  MaumDuckGLB.prototype.apply = function (p, t) {
    if (!this.ready) return;
    const breathing = this.pose === 'breathe', period = breathing ? 8 : 4, br = Math.sin(t * Math.PI * 2 / period), amp = breathing ? 0.035 : 0.012;
    const walking = this.pose === 'walk', swing = walking ? Math.sin(t * Math.PI * 2 * 1.6) : 0;
    this.hips.position.y = this.base.hipsY + p.rootY + (walking ? Math.abs(swing) * 0.025 : 0);
    // glTF 로컬: 앞으로 숙임 = X 음수 (모델이 -Z를 봄)
    this.torso.rotation.x = -p.torsoX; this.torso.scale.set(1 - br * amp * 0.5, 1 + br * amp, 1 - br * amp * 0.5);
    this.neck.rotation.x = -(p.headX + br * 0.01); this.neck.rotation.y = walking ? Math.sin(t * Math.PI * 2 * 0.8) * 0.08 : 0;
    this.wings.forEach((w, i) => { const s = i === 0 ? -1 : 1;
      w.rotation.x = -(p.wing[0] + swing * -s * 0.35);   // 앞으로 = X 양수 (Blender +X)
      w.rotation.z = -s * p.wing[1]; });                   // 안쪽으로 (Blender Y → glTF -Z)
    this.legs.forEach((l, i) => { const s = i === 0 ? -1 : 1;
      l.rotation.x = -(p.leg[0] + swing * s * 0.55); l.rotation.z = s * p.leg[1]; });
    this.eyes.forEach(e => { e.scale.y = this.base.eyeY * p.eye; });
  };

  MaumDuckGLB.prototype.update = function (dt) {
    this.t += dt; let p;
    const seq = SEQUENCES[this.pose];
    if (seq) {
      const steps = seq.steps, total = steps.reduce((a, s) => a + s[1], 0);
      const u = seq.loop ? this.t % total : Math.min(this.t, total);
      let acc = 0, p0 = this.from, p1 = POSES[steps[0][0]], k = 1;
      for (let i = 0; i < steps.length; i++) { const [n, len] = steps[i];
        if (u < acc + len || i === steps.length - 1) { p0 = i === 0 ? (seq.loop ? POSES[steps[steps.length - 1][0]] : this.from) : POSES[steps[i - 1][0]]; p1 = POSES[n]; k = Math.min(1, (u - acc) / len); break; }
        acc += len; }
      p = mix(p0, p1, ease(Math.min(1, k * 1.25)));
      if (!seq.loop && !this.done && this.t >= total) { this.done = true; if (this.onDone) this.onDone(); }
    } else { this.blend = Math.min(1, this.blend + dt / 0.6); p = mix(this.from, this.to, ease(this.blend)); }
    this.cur = p; this.apply(p, this.t);
  };

  global.MaumDuckGLB = MaumDuckGLB;
})(window);
