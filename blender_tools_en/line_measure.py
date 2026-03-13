import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bpy_extras import view3d_utils
import math
from . snap_utils import find_snap

_points = []
_handle = None


def get_world(pt):
    if pt["obj"] is not None:
        try:
            return pt["obj"].matrix_world @ pt["local"]
        except ReferenceError:
            return pt["world"]
    return pt["world"]


def compute_ticks(a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    length = math.sqrt(dx*dx + dy*dy)
    if length < 1:
        return []
    nx, ny = -dy/length*8, dx/length*8
    return [((p[0]+nx, p[1]+ny), (p[0]-nx, p[1]-ny)) for p in [a, b]]


def _fmt_dist(dist_bu):
    us = bpy.context.scene.unit_settings
    if us.system == 'NONE':
        return "%.4f" % dist_bu
    m = dist_bu * us.scale_length
    unit = us.length_unit
    if unit == 'MILLIMETERS': return "%.2f mm" % (m * 1000)
    if unit == 'CENTIMETERS': return "%.3f cm" % (m * 100)
    if unit == 'FEET':        return "%.4f ft" % (m * 3.28084)
    if unit == 'INCHES':      return "%.3f in" % (m * 39.3701)
    if unit == 'ADAPTIVE':
        if m >= 1.0:   return "%.4f m" % m
        if m >= 0.01:  return "%.3f cm" % (m * 100)
        return "%.2f mm" % (m * 1000)
    return "%.4f m" % m


def draw_label(sh, cx, cy, text):
    blf.size(0, 14)
    tw, th = blf.dimensions(0, text)
    px, py = 6, 4
    bx, by = cx - tw/2 - px, cy - th/2 - py
    bw, bh = tw + px*2, th + py*2
    sh.uniform_float("color", (1.0, 1.0, 1.0, 0.92))
    batch_for_shader(sh, 'TRI_FAN', {"pos": [
        (bx, by), (bx+bw, by), (bx+bw, by+bh), (bx, by+bh)]}).draw(sh)
    sh.uniform_float("color", (0.2, 0.2, 0.2, 1.0))
    gpu.state.line_width_set(1.0)
    batch_for_shader(sh, 'LINE_STRIP', {"pos": [
        (bx, by), (bx+bw, by), (bx+bw, by+bh), (bx, by+bh), (bx, by)]}).draw(sh)
    blf.color(0, 0.05, 0.05, 0.05, 1.0)
    blf.position(0, bx + px, by + py, 0)
    blf.draw(0, text)


def draw_cb():
    ctx = bpy.context
    region = ctx.region
    rv3d = ctx.region_data
    if not region or not rv3d or len(_points) == 0:
        return

    sh = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2.0)
    sh.bind()

    coords_2d = []
    for pt in _points:
        wc = get_world(pt)
        sc = view3d_utils.location_3d_to_region_2d(region, rv3d, wc)
        if sc:
            coords_2d.append((sc.x, sc.y))
        else:
            coords_2d.append((0, 0))

    sh.uniform_float("color", (0.3, 0.7, 1.0, 1.0))
    if len(coords_2d) > 1:
        batch_for_shader(sh, 'LINE_STRIP', {"pos": coords_2d}).draw(sh)

    for i, pt2d in enumerate(coords_2d):
        r = 5
        seg = 16
        angles = [2*3.14159*j/seg for j in range(seg)]
        circle = [(pt2d[0] + r*math.cos(a), pt2d[1] + r*math.sin(a)) for a in angles]
        sh.uniform_float("color", (1.0, 0.5, 0.1, 0.8))
        batch_for_shader(sh, 'LINE_LOOP', {"pos": circle}).draw(sh)

    if len(coords_2d) >= 2:
        dist_3d = (_points[-1]["world"] - _points[0]["world"]).length
        midpt = (coords_2d[0] + Vector(coords_2d[-1])) / 2
        sh.uniform_float("color", (1.0, 1.0, 1.0, 1.0))
        ticks = compute_ticks(coords_2d[0], coords_2d[-1])
        if ticks:
            for t_a, t_b in ticks:
                batch_for_shader(sh, 'LINES', {"pos": [t_a, t_b]}).draw(sh)
        draw_label(sh, midpt.x, midpt.y, _fmt_dist(dist_3d))

    gpu.state.blend_set('NONE')


class MEASURE_OT_LineMeasure(bpy.types.Operator):
    bl_idname = "measure.line_measure"
    bl_label = "Line Measure"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            region = context.region
            rv3d = context.region_data
            snap_res = find_snap(context, event.mouse_region_x, event.mouse_region_y)
            if snap_res:
                world_co = snap_res['co']
                local_co = snap_res['obj'].matrix_world.inverted() @ world_co if snap_res['obj'] else world_co
                _points.append({
                    "world": world_co,
                    "local": local_co,
                    "obj": snap_res['obj']
                })
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            global _handle
            if _handle:
                bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
                _handle = None
            _points.clear()
            context.area.tag_redraw()
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        global _handle
        _points.clear()
        _handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_cb, (), 'WINDOW', 'POST_PIXEL'
        )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class MEASURE_PT_LinePanel(bpy.types.Panel):
    bl_label = "Line"
    bl_idname = "MEASURE_PT_line_sub"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Measure"
    bl_parent_id = "MEASURE_PT_main"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        self.layout.operator("measure.line_measure", text="Line Measure")


def register():
    bpy.utils.register_class(MEASURE_OT_LineMeasure)


def unregister():
    global _handle
    if _handle:
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
    _points.clear()
    bpy.utils.unregister_class(MEASURE_OT_LineMeasure)
