"""마음온 도반 오리 — Blender(bpy) 모델링·렌더·GLB 내보내기.
실행: python3 build_duck.py <out_dir> [--no-render]
Z-up으로 만들고 GLB는 Y-up으로 내보낸다. 계층: root > hips > torso > neck / wingL,R / legL,R
"""
import sys, math, os
import bpy, bmesh
from mathutils import Vector, Euler

OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '/tmp/duck_out'
RENDER = '--no-render' not in sys.argv
os.makedirs(OUT, exist_ok=True)

# ───────── 색 (sRGB hex → linear)
def lin(h):
    r, g, b = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)
C = dict(cream='#f9e9b9', beak='#f0953f', beakDark='#d87a2a', cheek='#f2b1a8', ink='#1a1714',
         robe='#c2bdb3', lapel='#cbc6bc', lapelEdge='#b2ada3', dongjeong='#f4f1ea', sash='#8a6240', sashLight='#b08a5e',
         belt='#6b4a30', pack='#8a6240', packDark='#5a3f28', gilt='#c9a24f', lotus='#f08aa6', white='#ffffff')

# ───────── 씬 초기화
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
coll = bpy.context.collection

def mat_new(name, hex_color, rough=0.6, sheen=0.0, sss=0.0, weave=0.0, spec=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
    def setin(k, v):
        if k in bsdf.inputs: bsdf.inputs[k].default_value = v
    setin('Base Color', lin(hex_color)); setin('Roughness', rough); setin('Metallic', metal)
    setin('Specular IOR Level', spec)
    if sheen: setin('Sheen Weight', sheen); setin('Sheen Roughness', 0.6)
    if sss:
        setin('Subsurface Weight', sss); setin('Subsurface Radius', (0.4, 0.2, 0.1)); setin('Subsurface Scale', 0.05)
    if weave:  # 직조 결: 노이즈 → 범프
        noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 90; noise.inputs['Detail'].default_value = 4
        bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = weave; bump.inputs['Distance'].default_value = 0.01
        nt.links.new(noise.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return m

M = dict(
    cream=mat_new('cream', C['cream'], rough=0.55, sheen=0.15, sss=0.25, spec=0.4),
    beak=mat_new('beak', C['beak'], rough=0.45, sss=0.1),
    beakDark=mat_new('beakDark', C['beakDark'], rough=0.5),
    cheek=mat_new('cheek', C['cheek'], rough=0.7, sss=0.3),
    ink=mat_new('ink', C['ink'], rough=0.12, spec=0.9),
    white=mat_new('white', C['white'], rough=0.2),
    robe=mat_new('robe', C['robe'], rough=0.9, sheen=0.5, weave=0.12, spec=0.25),
    lapel=mat_new('lapel', C['lapel'], rough=0.9, sheen=0.5, weave=0.10, spec=0.25),
    lapelEdge=mat_new('lapelEdge', C['lapelEdge'], rough=0.9, sheen=0.3),
    dongjeong=mat_new('dongjeong', C['dongjeong'], rough=0.85, sheen=0.4, weave=0.08),
    sash=mat_new('sash', C['sash'], rough=0.85, sheen=0.35, weave=0.15, spec=0.3),
    sashLight=mat_new('sashLight', C['sashLight'], rough=0.85, sheen=0.35),
    belt=mat_new('belt', C['belt'], rough=0.8, sheen=0.3, weave=0.12),
    pack=mat_new('pack', C['pack'], rough=0.55, sheen=0.1, weave=0.06, spec=0.45),
    packDark=mat_new('packDark', C['packDark'], rough=0.5, spec=0.45),
    gilt=mat_new('gilt', C['gilt'], rough=0.35, metal=0.7),
    lotus=mat_new('lotus', C['lotus'], rough=0.4, sss=0.2),
)

# ───────── 헬퍼
def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); e.empty_display_size = 0.1; coll.objects.link(e)
    e.location = loc
    if parent: e.parent = parent
    return e

def finish(obj, mat, parent=None, smooth=True, subsurf=0):
    obj.data.materials.append(mat)
    if parent: obj.parent = parent
    if smooth:
        for p in obj.data.polygons: p.use_smooth = True
    if subsurf:
        m = obj.modifiers.new('subsurf', 'SUBSURF'); m.levels = subsurf; m.render_levels = subsurf
    return obj

def mesh_obj(name, verts, faces, mat, parent=None, loc=(0, 0, 0), smooth=True, subsurf=0):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o); o.location = loc
    return finish(o, mat, parent, smooth, subsurf)

def sphere(name, r, mat, parent=None, loc=(0, 0, 0), scale=(1, 1, 1), seg=48, rings=32):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll.objects.link(o); o.location = loc; o.scale = scale
    return finish(o, mat, parent)

def lathe(name, profile, mat, parent=None, loc=(0, 0, 0), N=64, close_top=True, close_bottom=True, subsurf=1):
    """profile: [(r, z), ...] 아래→위. 회전축 z."""
    verts, faces = [], []
    for (r, z) in profile:
        for i in range(N):
            a = 2 * math.pi * i / N; verts.append((r * math.sin(a), r * math.cos(a), z))
    R = len(profile)
    for j in range(R - 1):
        for i in range(N):
            a, b = j * N + i, j * N + (i + 1) % N
            faces.append((a, b, b + N, a + N))
    if close_bottom:
        c = len(verts); verts.append((0, 0, profile[0][1])); faces += [(c, (i + 1) % N, i) for i in range(N)]
    if close_top:
        c = len(verts); base = (R - 1) * N; verts.append((0, 0, profile[-1][1])); faces += [(c, base + i, base + (i + 1) % N) for i in range(N)]
    return mesh_obj(name, verts, faces, mat, parent, loc, True, subsurf)

def cylinder(name, r0, r1, h, mat, parent=None, loc=(0, 0, 0), N=32):
    return lathe(name, [(r0, -h / 2), (r1, h / 2)], mat, parent, loc, N, subsurf=0)

def rounded_box(name, w, d, h, bevel, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), segs=6):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll.objects.link(o); o.location = loc; o.scale = (w, d, h); o.rotation_euler = Euler(rot)
    b = o.modifiers.new('bevel', 'BEVEL'); b.width = bevel; b.segments = segs; b.limit_method = 'NONE'
    return finish(o, mat, parent, True)

# 몸 회전체 프로필 (세계 z). 저고리를 입은 몸 전체
BODY = [(0.40, 0.22), (0.45, 0.30), (0.46, 0.42), (0.43, 0.56), (0.36, 0.70), (0.26, 0.82), (0.14, 0.90), (0.0, 0.93)]
def surface_r(z):
    for i in range(1, len(BODY)):
        (r0, z0), (r1, z1) = BODY[i - 1], BODY[i]
        if z <= z1:
            k = max(0.0, min(1.0, (z - z0) / (z1 - z0))); return r0 + (r1 - r0) * k
    return 0.0
def on_body(th, z, lift):
    r = surface_r(z) + lift; return Vector((r * math.sin(th), r * math.cos(th), z))

def catmull(pts, closed, n):
    """Catmull-Rom 샘플 (centripetal 근사: 균일)"""
    P = list(pts); out = []
    m = len(P)
    segs = m if closed else m - 1
    for s in range(segs):
        p0 = P[(s - 1) % m] if closed else P[max(s - 1, 0)]
        p1 = P[s]; p2 = P[(s + 1) % m]; p3 = P[(s + 2) % m] if closed else P[min(s + 2, m - 1)]
        for i in range(n):
            t = i / n; t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed: out.append(P[-1])
    return out

def ribbon(name, pts, width, lift, mat, parent, closed=False, thickness=0.012, taper=False, rows=6):
    """몸 표면(θ, z) 좌표계에서 띠를 펼친다: 중심선을 따라 접선의 수직 방향으로 폭만큼 벌려 표면 위에 놓는다.
    몸에서 뜨거나 꼬이지 않는다. 두께는 솔리디파이."""
    ctr = catmull([Vector((th, z, 0)) for th, z in pts], closed, 10)   # (θ, z) 평면의 중심선
    n = len(ctr); verts, faces = [], []
    for i, P in enumerate(ctr):
        nxt = ctr[(i + 1) % n] if closed else ctr[min(i + 1, n - 1)]
        prv = ctr[(i - 1) % n] if closed else ctr[max(i - 1, 0)]
        r = max(surface_r(P.y), 0.05)
        # 접선을 실제 거리 단위(θ·r, z)로 재서 수직 방향을 구한다
        T = Vector(((nxt.x - prv.x) * r, nxt.y - prv.y, 0)).normalized()
        Nn = Vector((-T.y, T.x, 0))
        u = i / n
        w = width * (0.55 + 0.45 * math.sin(u * math.pi)) if taper else width
        for k in range(rows + 1):
            d = (k / rows - 0.5) * w
            th = P.x + Nn.x * d / r; z = P.y + Nn.y * d
            verts.append(tuple(on_body(th, z, lift)))
    R = rows + 1
    for i in range(n if closed else n - 1):
        a = i * R; b = ((i + 1) % n) * R
        for k in range(rows):
            faces.append((a + k, a + k + 1, b + k + 1, b + k))
    o = mesh_obj(name, verts, faces, mat, parent, smooth=True)
    so = o.modifiers.new('solid', 'SOLIDIFY'); so.thickness = thickness; so.offset = 1.0
    return o

# ───────── 계층
root = empty('root'); hips = empty('hips', root); torso = empty('torso', hips, (0, 0, 0.22)); neck = empty('neck', torso, (0, 0, 0.66))

# ───────── 몸 + 저고리 (회전체 → 서브디비전 → 주름 변위)
ROBE = lathe('robe', [(r, z - 0.22) for r, z in BODY], M['robe'], torso, subsurf=2)
tex = bpy.data.textures.new('folds', type='STUCCI'); tex.noise_scale = 0.22; tex.turbulence = 4.0; tex.noise_basis = 'IMPROVED_PERLIN'
dsp = ROBE.modifiers.new('folds', 'DISPLACE'); dsp.texture = tex; dsp.strength = 0.018; dsp.mid_level = 0.5; dsp.direction = 'NORMAL'
tex2 = bpy.data.textures.new('drape', type='CLOUDS'); tex2.noise_scale = 0.7; tex2.noise_depth = 2
dsp2 = ROBE.modifiers.new('drape', 'DISPLACE'); dsp2.texture = tex2; dsp2.strength = 0.03; dsp2.mid_level = 0.5; dsp2.direction = 'NORMAL'
# 밑단 두께
hem = lathe('hem', [(0.405, 0.0), (0.405, 0.02)], M['robe'], torso, N=64, close_top=False, close_bottom=False, subsurf=0)
# 가슴 속옷
sphere('inner', 1, M['cream'], torso, (0, 0.325, 0.38), (0.13, 0.04, 0.12))

# 깃 (V자, 오른쪽이 위)
LAP_L = [(-0.95, 0.90), (-0.55, 0.78), (-0.15, 0.62), (0.08, 0.50)]
LAP_R = [(0.95, 0.90), (0.55, 0.78), (0.15, 0.62), (-0.08, 0.50)]
ribbon('lapelL', LAP_L, 0.11, 0.006, M['lapel'], torso, thickness=0.008)
ribbon('lapelL_dj', [(th + 0.06, z) for th, z in LAP_L], 0.035, 0.012, M['dongjeong'], torso, thickness=0.003)
ribbon('lapelR', LAP_R, 0.11, 0.014, M['lapel'], torso, thickness=0.008)
ribbon('lapelR_dj', [(th - 0.06, z) for th, z in LAP_R], 0.035, 0.020, M['dongjeong'], torso, thickness=0.003)
# 사선 가방끈: 왼쪽 어깨 → 가슴 → 오른쪽 허리(걸망으로 이어짐). 보드의 기본 법복은 가사 없이 이 끈 하나다
STRAP = [(-1.0, 0.86), (-0.5, 0.74), (0.05, 0.62), (0.65, 0.48), (1.25, 0.40), (1.9, 0.40), (2.6, 0.52), (3.3, 0.70), (3.9, 0.84), (4.5, 0.90)]
ribbon('chestStrap', STRAP, 0.075, 0.030, M['sash'], torso, closed=True, thickness=0.014, rows=3)
sp = on_body(1.25, 0.40, 0.045)
sbk = lathe('strapBuckle', [(0.018, -0.006), (0.032, -0.006), (0.032, 0.006), (0.018, 0.006)], M['gilt'], torso, N=24, close_top=False, close_bottom=False, subsurf=1)
sbk.location = (sp.x, sp.y, sp.z - 0.22); sbk.rotation_euler = Euler((math.pi / 2, 0, -1.25))
# 허리끈 + 매듭
BELT = [(i / 12 * 2 * math.pi, 0.40 - 0.01 * math.cos(i / 12 * 2 * math.pi)) for i in range(12)]
ribbon('belt', BELT, 0.075, 0.012, M['belt'], torso, closed=True, thickness=0.016)
# 허리끈 매듭: 납작한 매듭 하나 + 납작한 끈 자락 두 가닥 (오른쪽 옆구리 쪽에, 둥근 형태 없음)
KNOT_TH = 0.55
kp = on_body(KNOT_TH, 0.40, 0.03)
knot = rounded_box('beltKnot', 0.06, 0.02, 0.04, 0.006, M['belt'], torso, (kp.x, kp.y, kp.z - 0.22), (0, 0, -KNOT_TH))
for k, (dth, dz, tilt, ln) in enumerate(((0.06, -0.02, 0.25, 0.16), (-0.03, -0.03, -0.18, 0.13))):
    tp = on_body(KNOT_TH + dth, 0.40 - ln / 2 + dz, 0.028)
    rounded_box('beltTail%d' % k, 0.028, 0.008, ln, 0.003, M['belt'], torso, (tp.x, tp.y, tp.z - 0.22), (0, tilt, -(KNOT_TH + dth)))

# ───────── 걸망 (모서리 둥근 가방, 덮개, 버클, 구슬, 멜빵)
rounded_box('pack', 0.30, 0.12, 0.30, 0.05, M['pack'], torso, (0, -0.50, 0.40), (0.08, 0, 0))
rounded_box('flap', 0.31, 0.035, 0.15, 0.015, M['packDark'], torso, (0, -0.56, 0.485), (0.08, 0, 0))
bk = lathe('buckle', [(0.02, -0.006), (0.034, -0.006), (0.034, 0.006), (0.02, 0.006)], M['gilt'], torso, N=24, close_top=False, close_bottom=False, subsurf=1)
bk.location = (0, -0.58, 0.44); bk.rotation_euler = Euler((math.pi / 2, 0, 0))
sphere('bead', 0.03, M['lotus'], torso, (0.17, -0.52, 0.33))
cylinder('beadStr', 0.004, 0.004, 0.06, M['packDark'], torso, (0.17, -0.52, 0.37))
for s, nm in ((-1, 'strapL'), (1, 'strapR')):
    ribbon(nm, [(math.pi - s * 0.45, 0.70), (math.pi - s * 0.75, 0.84), (s * 0.85, 0.88), (s * 0.55, 0.74), (s * 0.42, 0.60)], 0.05, 0.014, M['packDark'], torso, thickness=0.012)

# ───────── 소매 + 손
wings = {}
for s, nm in ((-1, 'wingL'), (1, 'wingR')):
    w = empty(nm, torso, (s * 0.41, 0.06, 0.60)); wings[nm] = w   # 몸 바깥, 어깨 높이
    sl = lathe('sleeve' + nm[-1], [(0.0, -0.29), (0.17, -0.29), (0.19, -0.27), (0.17, -0.18), (0.12, -0.08), (0.08, 0.02), (0.0, 0.05)], M['robe'], w, N=48, close_top=False, close_bottom=False, subsurf=2)
    d = sl.modifiers.new('folds', 'DISPLACE'); d.texture = tex; d.strength = 0.008
    cuff = lathe('cuff' + nm[-1], [(0.165, -0.295), (0.185, -0.275), (0.165, -0.255)], M['dongjeong'], w, N=48, close_top=False, close_bottom=False, subsurf=1)
    sphere('hand' + nm[-1], 1, M['cream'], w, (0, 0.03, -0.32), (0.085, 0.095, 0.07))

# ───────── 머리
HEAD = [(0.0, -0.40), (0.26, -0.37), (0.40, -0.25), (0.465, -0.08), (0.46, 0.08), (0.41, 0.24), (0.29, 0.36), (0.0, 0.42)]
head = lathe('head', HEAD, M['cream'], neck, (0, 0, 0.26), N=72, subsurf=2)
head.scale = (1.0, 0.92, 1.0)
for i, (x, z, y, rz, rx) in enumerate([(0, 0.67, 0.0, 0.15, 0.0), (-0.07, 0.66, 0.04, 0.35, 0.3), (0.06, 0.66, -0.03, -0.3, -0.25)]):
    t = lathe('tuft%d' % i, [(0.022, 0), (0.012, 0.07), (0.0, 0.12)], M['cream'], neck, (x, y, z), N=12, close_top=False)
    t.rotation_euler = Euler((rx, -rz, 0))
for s in (-1, 1):
    e = sphere('eye' + ('L' if s < 0 else 'R'), 0.068, M['ink'], neck, (s * 0.17, 0.395, 0.24), (1, 0.5, 1.25))
    # 자식 좌표는 부모 스케일(1, 0.5, 1.25)을 타므로 보정
    sphere('hi1' + ('L' if s < 0 else 'R'), 0.02, M['white'], e, (0.022, 0.11, 0.024), (1, 2, 0.8))
    sphere('hi2' + ('L' if s < 0 else 'R'), 0.011, M['white'], e, (-0.026, 0.11, -0.02), (1, 2, 0.8))
    sphere('cheek' + ('L' if s < 0 else 'R'), 1, M['cheek'], neck, (s * 0.33, 0.285, 0.12), (0.085, 0.03, 0.058))
sphere('beakU', 1, M['beak'], neck, (0, 0.425, 0.13), (0.145, 0.11, 0.075))
sphere('beakL', 1, M['beakDark'], neck, (0, 0.415, 0.08), (0.115, 0.09, 0.05))

# ───────── 다리·물갈퀴 발
for s, nm in ((-1, 'legL'), (1, 'legR')):
    l = empty(nm, hips, (s * 0.13, 0.02, 0.22))
    cylinder('leg' + nm[-1], 0.045, 0.04, 0.20, M['beak'], l, (0, 0, -0.10))
    sphere('foot' + nm[-1], 1, M['beak'], l, (0, 0.06, -0.20), (0.11, 0.17, 0.035))
    for k in (-1, 0, 1):
        sphere('toe%s%d' % (nm[-1], k + 1), 1, M['beak'], l, (k * 0.06, 0.19, -0.20), (0.035, 0.07, 0.03))

# ───────── 바닥·조명·카메라·월드
ground = mesh_obj('ground', [(-6, -6, 0), (6, -6, 0), (6, 6, 0), (-6, 6, 0)], [(0, 1, 2, 3)], mat_new('ground', '#efe4d2', rough=1.0))
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs['Color'].default_value = lin('#fff1dc'); bg.inputs['Strength'].default_value = 0.7
def light(name, kind, loc, energy, color='#ffffff', size=2.0):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = lin(color)[:3]
    if kind == 'AREA': ld.size = size
    o = bpy.data.objects.new(name, ld); coll.objects.link(o); o.location = loc
    c = o.constraints.new('TRACK_TO'); c.target = root; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    return o
light('key', 'AREA', (2.5, -3.5, 4.0), 900, '#ffe9c4', 2.5)
light('fill', 'AREA', (-3.5, -2.0, 2.0), 250, '#ffffff', 3.0)
light('rim', 'AREA', (-1.5, 3.5, 3.0), 300, '#f2b8c6', 2.0)
tgt = empty('camTarget', None, (0, 0, 0.78))
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 60
cam = bpy.data.objects.new('cam', cam_d); coll.objects.link(cam); scene.camera = cam
cc = cam.constraints.new('TRACK_TO'); cc.target = tgt; cc.track_axis = 'TRACK_NEGATIVE_Z'; cc.up_axis = 'UP_Y'

scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = scene.render.resolution_y = 640; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
try: scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass

def set_cam(az_deg, el=0.18, dist=4.3):
    az = math.radians(az_deg)
    cam.location = (dist * math.sin(az) * math.cos(el), dist * math.cos(az) * math.cos(el), 0.78 + dist * math.sin(el))  # 얼굴이 +Y

def pose(name):
    hands = name in ('hapjang', 'halfbow')
    for nm, s in (('wingL', -1), ('wingR', 1)):
        # Blender: 소매는 -Z로 매달림. 앞(+Y)으로 = +X 회전, 안쪽으로 = Y 회전(왼쪽 음수)
        wings[nm].rotation_euler = Euler((0.85 if hands else -0.12, s * (0.95 if hands else -0.10), 0))  # 평소엔 살짝 바깥으로 벌어져 매달림
    torso.rotation_euler = Euler((-(0.5 if name == 'halfbow' else 0.03 if hands else 0), 0, 0))
    neck.rotation_euler = Euler((-(0.49 if name == 'halfbow' else 0.14 if hands else 0), 0, 0))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'duck.blend'))

if RENDER:
    VIEWS = [v for v in (('front', 0, 'stand'), ('side', 90, 'stand'), ('back', 180, 'stand'), ('hapjang', 25, 'hapjang'), ('halfbow', 60, 'halfbow')) if not os.environ.get('VIEWS') or v[0] in os.environ['VIEWS'].split(',')]
    for nm, az, ps in VIEWS:
        pose(ps); set_cam(az)
        scene.render.filepath = os.path.join(OUT, 'render_%s.png' % nm)
        bpy.ops.render.render(write_still=True)
        print('rendered', nm, flush=True)
    pose('stand')

# ───────── GLB
bpy.ops.object.select_all(action='DESELECT')
for o in coll.objects:
    if o.name not in ('ground', 'key', 'fill', 'rim', 'cam', 'camTarget'): o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'mindon-duck.glb'), export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
print('done', OUT)
