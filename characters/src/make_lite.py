"""duck.blend → 가벼운 GLB (다른 방문자용). 서브디비전을 낮추고 데시메이트해 정점 1.5~2만 목표.
실행: python3 make_lite.py <blend> <out.glb> [target_verts]
"""
import sys, bpy
blend, out = sys.argv[1], sys.argv[2]
target = int(sys.argv[3]) if len(sys.argv) > 3 else 18000
bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
skip = {'ground', 'key', 'fill', 'rim', 'cam', 'camTarget'}
meshes = [o for o in scene.objects if o.type == 'MESH' and o.name not in skip]

def evaluated_verts():
    dg = bpy.context.evaluated_depsgraph_get(); n = 0
    for o in meshes:
        n += len(o.evaluated_get(dg).data.vertices)
    return n

# 1) 서브디비전 1단계로
for o in meshes:
    for m in o.modifiers:
        if m.type == 'SUBSURF': m.levels = min(m.levels, 1); m.render_levels = m.levels
before = evaluated_verts()
# 2) 비율 데시메이트: 큰 메시(머리·몸·소매)만, 디테일 작은 것은 그대로
ratio = min(1.0, target / max(before, 1))
for o in meshes:
    dg = bpy.context.evaluated_depsgraph_get(); n = len(o.evaluated_get(dg).data.vertices)
    if n > 600:
        d = o.modifiers.new('decimate', 'DECIMATE'); d.ratio = max(0.15, ratio * 0.9); d.use_collapse_triangulate = True
after = evaluated_verts()
print('verts before %d → after %d (ratio %.2f)' % (before, after, ratio), flush=True)

bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
    if o.name not in skip: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
print('done', out)
