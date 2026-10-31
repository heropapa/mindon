"""마음온 불이문 풍경(風磬) — Blender(bpy) 모델링·렌더·GLB 내보내기.
실행: python3 build_pungyeong.py <out_dir> [--no-render]
단위 m. Blender Z-up(얼굴 +Y)으로 만들고 glTF Y-up(앞 -Z)으로 내보낸다.
노드: pung_bell (맨 위 고리가 피벗, 원점) → 자식 pung_fish (종 아래 고리가 피벗). 코드에서 둘을 다른 박자로 흔든다.
"""
import sys, math, os
import bpy, bmesh
from mathutils import Vector, Euler

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0] if args else '/tmp/pung_out'
RENDER = '--no-render' not in sys.argv
os.makedirs(OUT, exist_ok=True)

def lin(h):
    r, g, b = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene; coll = bpy.context.collection

def mat_new(name, hex_color, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(hex_color); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m
M = dict(
    bronze=mat_new('bronze', '#7a6442', rough=0.45, metal=0.75),     # 청동 (따뜻한 갈색 금속)
    verdigris=mat_new('verdigris', '#6f8a78', rough=0.7, metal=0.3), # 녹이 살짝 낀 청동 (테·고리)
    brass=mat_new('brass', '#b08d52', rough=0.4, metal=0.8),         # 물고기 바람판 (밝은 놋쇠)
    dark=mat_new('dark', '#3a3128', rough=0.6, metal=0.4),           # 추·끈
)

def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); e.empty_display_size = 0.05; coll.objects.link(e); e.location = loc
    if parent: e.parent = parent
    return e
def finish(o, mat, parent, smooth=True):
    o.data.materials.append(mat)
    if parent: o.parent = parent
    for p in o.data.polygons: p.use_smooth = smooth
    return o
def mesh_obj(name, verts, faces, mat, parent, loc=(0, 0, 0), smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o); o.location = loc
    return finish(o, mat, parent, smooth)
def lathe(name, profile, mat, parent, loc=(0, 0, 0), N=32, close_top=True, close_bottom=True):
    verts, faces = [], []
    for (r, z) in profile:
        for i in range(N):
            a = 2 * math.pi * i / N; verts.append((r * math.sin(a), r * math.cos(a), z))
    R = len(profile)
    for j in range(R - 1):
        for i in range(N):
            a, b = j * N + i, j * N + (i + 1) % N; faces.append((a, b, b + N, a + N))
    if close_bottom:
        c = len(verts); verts.append((0, 0, profile[0][1])); faces += [(c, (i + 1) % N, i) for i in range(N)]
    if close_top:
        c = len(verts); base = (R - 1) * N; verts.append((0, 0, profile[-1][1])); faces += [(c, base + i, base + (i + 1) % N) for i in range(N)]
    return mesh_obj(name, verts, faces, mat, parent, loc)
def torus(name, R_, r_, mat, parent, loc=(0, 0, 0), rot=(0, 0, 0), N=16, n=6):
    bm = bmesh.new(); bmesh.ops.create_uvsphere  # noqa (bmesh import kept)
    verts, faces = [], []
    for i in range(N):
        a = 2 * math.pi * i / N
        for j in range(n):
            b = 2 * math.pi * j / n
            verts.append(((R_ + r_ * math.cos(b)) * math.cos(a), (R_ + r_ * math.cos(b)) * math.sin(a), r_ * math.sin(b)))
    for i in range(N):
        for j in range(n):
            a0 = i * n + j; a1 = i * n + (j + 1) % n; b0 = ((i + 1) % N) * n + j; b1 = ((i + 1) % N) * n + (j + 1) % n
            faces.append((a0, b0, b1, a1))
    o = mesh_obj(name, verts, faces, mat, parent, loc); o.rotation_euler = Euler(rot); return o
def cylinder(name, r, h, mat, parent, loc, rot=(0, 0, 0), N=8):
    o = lathe(name, [(r, -h / 2), (r, h / 2)], mat, parent, loc, N=N); o.rotation_euler = Euler(rot); return o
def extrude_shape(name, pts, thickness, mat, parent, loc=(0, 0, 0)):
    """XZ 평면의 2D 윤곽(pts: [(x, z)])을 Y 방향으로 thickness 만큼 두껍게. 앞면은 +Y."""
    n = len(pts); h = thickness / 2
    verts = [(x, -h, z) for x, z in pts] + [(x, h, z) for x, z in pts]
    faces = [tuple(range(n))[::-1], tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n; faces.append((i, j, n + j, n + i))
    return mesh_obj(name, verts, faces, mat, parent, loc, smooth=False)

# ───────── 계층: pung_bell (원점 = 맨 위 고리) → pung_fish
bell = empty('pung_bell')
# 맨 위 고리 (피벗 지점에 작은 고리)
torus('top_ring', 0.018, 0.004, M['verdigris'], bell, (0, 0, -0.005), (math.pi / 2, 0, 0), N=16, n=6)
# 고리 ↔ 종 꼭지 연결
cylinder('stem', 0.006, 0.03, M['dark'], bell, (0, 0, -0.035), N=8)
# 종: 꼭지 → 어깨 → 몸 → 벌어진 입 (지름 0.22, 높이 0.22). 속이 비도록 안쪽 면도 둘러서 되돌아옴
BELL = [(0.0, -0.05), (0.03, -0.05), (0.055, -0.07), (0.075, -0.11), (0.088, -0.17), (0.10, -0.23), (0.11, -0.27),   # 바깥
        (0.096, -0.27), (0.086, -0.235), (0.075, -0.18), (0.06, -0.12), (0.035, -0.08), (0.0, -0.075)]               # 안쪽
lathe('bell_body', BELL, M['bronze'], bell, N=32, close_top=True, close_bottom=False)
# 입 테두리 (녹이 낀 띠)
torus('bell_rim', 0.104, 0.006, M['verdigris'], bell, (0, 0, -0.27), N=32, n=6)
# 어깨 장식 띠
torus('bell_band', 0.078, 0.004, M['verdigris'], bell, (0, 0, -0.12), N=24, n=5)
# 추(혀): 종 안에서 내려오는 줄 + 작은 구슬
cylinder('clapper_rod', 0.004, 0.19, M['dark'], bell, (0, 0, -0.165), N=6)
ball = lathe('clapper', [(0.0, -0.022), (0.016, -0.014), (0.022, 0.0), (0.016, 0.014), (0.0, 0.022)], M['dark'], bell, (0, 0, -0.262), N=12)
# 종 아래 고리 (여기가 물고기 피벗)
torus('bottom_ring', 0.014, 0.0035, M['verdigris'], bell, (0, 0, -0.295), (math.pi / 2, 0, 0), N=12, n=5)

fish = empty('pung_fish', bell, (0, 0, -0.30))
# 고리 ↔ 물고기 사이 짧은 사슬 (고리 두 개)
torus('chain1', 0.012, 0.003, M['dark'], fish, (0, 0, -0.016), (0, math.pi / 2, 0), N=12, n=5)
torus('chain2', 0.012, 0.003, M['dark'], fish, (0, 0, -0.036), (math.pi / 2, 0, 0), N=12, n=5)
# 물고기 바람판: 납작한 놋쇠판. 머리가 위, 꼬리가 아래 (실제 풍경처럼 세로로 매달림). 전체 길이 0.26
FISH = [(0.0, -0.05), (0.028, -0.062), (0.05, -0.09), (0.058, -0.13), (0.052, -0.17), (0.036, -0.21), (0.016, -0.24),   # 오른쪽 옆구리
        (0.05, -0.275), (0.062, -0.31), (0.0, -0.285), (-0.062, -0.31), (-0.05, -0.275),                              # 꼬리 두 갈래
        (-0.016, -0.24), (-0.036, -0.21), (-0.052, -0.17), (-0.058, -0.13), (-0.05, -0.09), (-0.028, -0.062)]
extrude_shape('fish_plate', FISH, 0.006, M['brass'], fish)
# 눈 두 개와 지느러미 (앞뒤로 살짝 튀어나온 작은 조각)
for s in (-1, 1):
    torus('fish_eye%d' % (s + 1), 0.009, 0.003, M['dark'], fish, (0.022, s * 0.004, -0.095), (math.pi / 2, 0, 0), N=10, n=4)
    extrude_shape('fish_fin%d' % (s + 1), [(0.0, -0.15), (s * 0.075, -0.18), (0.0, -0.20)] if s > 0 else [(0.0, -0.15), (0.0, -0.20), (-0.075, -0.18)], 0.004, M['brass'], fish)
# 꼬리 끝 작은 구슬 (무게추)
lathe('fish_bead', [(0.0, -0.012), (0.009, -0.006), (0.012, 0.0), (0.009, 0.006), (0.0, 0.012)], M['dark'], fish, (0, 0, -0.31), N=10)

# ───────── 삼각형 수
tri = 0
for o in coll.objects:
    if o.type == 'MESH': tri += sum(len(p.vertices) - 2 for p in o.data.polygons)
print('triangles:', tri, flush=True)

# ───────── 렌더 (처마 느낌의 어두운 배경 + 따뜻한 빛)
world = bpy.data.worlds.new('w'); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs['Color'].default_value = lin('#f3e6cf'); bg.inputs['Strength'].default_value = 0.8
def light(name, loc, energy, color, size=1.0):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.color = lin(color)[:3]; ld.size = size
    o = bpy.data.objects.new(name, ld); coll.objects.link(o); o.location = loc
    c = o.constraints.new('TRACK_TO'); c.target = bell; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'; return o
light('key', (0.8, -1.0, 0.6), 80, '#ffe9c4', 0.8); light('fill', (-0.9, -0.6, -0.2), 25, '#ffffff', 1.0); light('rim', (-0.3, 1.0, 0.4), 40, '#f2b8c6', 0.6)
tgt = empty('camTarget', None, (0, 0, -0.3))
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 70
cam = bpy.data.objects.new('cam', cam_d); coll.objects.link(cam); scene.camera = cam
cc = cam.constraints.new('TRACK_TO'); cc.target = tgt; cc.track_axis = 'TRACK_NEGATIVE_Z'; cc.up_axis = 'UP_Y'
cam.location = (0.55, 1.25, 0.05)
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 64; scene.cycles.use_denoising = True
scene.render.resolution_x = 640; scene.render.resolution_y = 800; scene.render.image_settings.file_format = 'PNG'
try: scene.view_settings.view_transform = 'AgX'
except Exception: pass
# 살짝 흔들린 자세로 렌더 (코드가 줄 움직임의 예시)
bell.rotation_euler = Euler((0.06, 0.0, 0.0)); fish.rotation_euler = Euler((-0.12, 0.0, 0.25))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'pungyeong.blend'))
if RENDER:
    scene.render.filepath = os.path.join(OUT, 'pungyeong_render.png'); bpy.ops.render.render(write_still=True); print('rendered', flush=True)
bell.rotation_euler = Euler((0, 0, 0)); fish.rotation_euler = Euler((0, 0, 0))

# ───────── GLB
bpy.ops.object.select_all(action='DESELECT')
for o in coll.objects:
    if o.name not in ('key', 'fill', 'rim', 'cam', 'camTarget'): o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'mindon-pungyeong.glb'), export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
print('done', OUT)
