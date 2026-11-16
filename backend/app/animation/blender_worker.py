import re
import subprocess
from typing import Callable, Optional
from app.core.config import get_settings


def build_blender_python_script(
    output_mp4: str, scene_preset: str, title_text: str, duration_seconds: float,
    res_x: int, res_y: int, fps: int, samples: int, camera_motion: str,
) -> str:
    total_frames = max(24, int(duration_seconds * fps))
    safe_title = title_text.replace('"', '\\"')
    return f'''
import bpy, math
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES' if bpy.context.preferences.addons.get('cycles') else 'BLENDER_EEVEE'
if scene.render.engine == 'CYCLES':
    scene.cycles.samples = {samples}
else:
    scene.eevee.taa_render_samples = {samples}
scene.render.resolution_x = {res_x}
scene.render.resolution_y = {res_y}
scene.render.fps = {fps}
scene.frame_start = 1
scene.frame_end = {total_frames}
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.filepath = r"{output_mp4}"

world = bpy.data.worlds.new("NeuroflowWorld")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.03, 0.06, 1.0)

if "{scene_preset}" == "orbit_logo":
    bpy.ops.object.text_add(location=(0, 0, 0), rotation=(math.radians(90), 0, 0))
    obj = bpy.context.active_object
    obj.data.body = "{safe_title}"
    obj.data.extrude = 0.25
    obj.data.align_x = 'CENTER'
else:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.2, location=(0, 0, 1.2))
    obj = bpy.context.active_object
    obj.keyframe_insert(data_path="rotation_euler", frame=1)
    obj.rotation_euler[2] = math.radians(360)
    obj.keyframe_insert(data_path="rotation_euler", frame={total_frames})

mat = bpy.data.materials.new(name="AccentMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.54, 0.36, 0.96, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.75
obj.data.materials.append(mat)
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))
bpy.context.active_object.data.energy = 350

bpy.ops.object.camera_add(location=(0, -6.5, 2.2), rotation=(math.radians(78), 0, 0))
cam = bpy.context.active_object
scene.camera = cam
if "{camera_motion}" == "dolly_in":
    cam.keyframe_insert(data_path="location", frame=1)
    cam.location = (0, -3.6, 1.7)
    cam.keyframe_insert(data_path="location", frame={total_frames})
elif "{camera_motion}" == "pan":
    cam.location = (-2.5, -6.0, 2.0)
    cam.keyframe_insert(data_path="location", frame=1)
    cam.location = (2.5, -6.0, 2.0)
    cam.keyframe_insert(data_path="location", frame={total_frames})
else:
    bpy.ops.object.empty_add(location=(0, 0, 1.0))
    rig = bpy.context.active_object
    cam.parent = rig
    rig.keyframe_insert(data_path="rotation_euler", frame=1)
    rig.rotation_euler[2] = math.radians(45)
    rig.keyframe_insert(data_path="rotation_euler", frame={total_frames})
bpy.ops.render.render(animation=True)
'''


def run_blender_render(
    script_path: str, on_progress: Optional[Callable[[int, str], None]] = None, cancel_check: Optional[Callable[[], bool]] = None,
) -> str:
    proc = subprocess.Popen([get_settings().BLENDER_BINARY_PATH, "-b", "-P", script_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    logs = []
    assert proc.stdout is not None
    for line in proc.stdout:
        logs.append(line)
        if cancel_check and cancel_check():
            proc.terminate()
            raise InterruptedError("Blender render cancelled by user.")
        m = re.search(r"Fra:(\d+)", line)
        if m and on_progress:
            on_progress(int(m.group(1)), line.strip())
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"Blender exited with code {rc}:\n{''.join(logs)[-1000:]}")
    return "".join(logs)
