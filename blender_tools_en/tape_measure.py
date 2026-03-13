import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bpy_extras import view3d_utils
import math
from . snap_utils import find_snap

_pt1 = None
_snap_pt = None
_cursor = None
_handle = None


def get_world_from_item(item_pt):
    if item_pt.is_snapped:
        obj = bpy.data.objects.get(item_pt.obj_name)
        if obj:
            return obj.matrix_world @ Vector(item_pt.local)
    return Vector(item_pt.world)


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
    px, py = 8, 5
    bx = cx - tw/2 - px
    by = cy - th/2 - py
    bw, bh = tw+px*2, th+py*2
    sh.bind()
    sh.uniform_float("color", (1.0, 1.0, 1.0, 0.95))
    batch_for_shader(sh, 'TRI_FAN', {"pos": [(bx,by),(bx+bw,by),(bx+bw,by+bh),(bx,by+bh)]}).draw(sh)
    sh.bind()
    sh.uniform_float("color", (0.2, 0.2, 0.2, 1.0))
    gpu.state.line_width_set(1.0)
    batch_for_shader(sh, 'LINE_STRIP', {"pos": [(bx,by),(bx+bw,by),(bx+bw,by+bh),(bx,by+bh),(bx,by)]}).draw(sh)
    blf.color(0, 0.05, 0.05, 0.05, 1.0)
    blf.position(0, bx+px, by+py, 0)
    blf.draw(0, text)


def draw_cb():
    ctx = bpy.context
    if not ctx.scene.measure_visible:
        return
    region = ctx.region
    rv3d = ctx.region_data
    if not rv3d or not region:
        return

    gpu.state.blend_set('ALPHA')
    sh = gpu.shader.from_builtin('UNIFORM_COLOR')

    def to2d(p):
        sc = view3d_utils.location_3d_to_region_2d(region, rv3d, p)
        return (sc.x, sc.y) if sc else None

    def draw_segment(w1, w2, alpha=1.0):
        a, b = to2d(w1), to2d(w2)
        if not a or not b:
            return
        dist = (w2 - w1).length
        sh.bind()
        sh.uniform_float("color", (0.1, 0.1, 0.1, alpha))
        gpu.state.line_width_set(1.5)
        batch_for_shader(sh, 'LINES', {"pos": [a, b]}).draw(sh)
        for t1, t2 in compute_ticks(a, b):
            batch_for_shader(sh, 'LINES', {"pos": [t1, t2]}).draw(sh)
        draw_label(sh, (a[0]+b[0])/2, (a[1]+b[1])/2, _fmt_dist(dist))

    for item in ctx.scene.tape_measurements:
        w1 = get_world_from_item(item.pt1)
        w2 = get_world_from_item(item.pt2)
        if w1 and w2:
            draw_segment(w1, w2)

    if _snap_pt:
        wp = _snap_pt["obj"].matrix_world @ _snap_pt["local"] if _snap_pt["obj"] else _snap_pt["world"]
        sp = to2d(wp)
        if sp:
            x, y = sp
            snap_type = _snap_pt.get("snap_type", 'VERT')
            sh.bind()
            gpu.state.line_width_set(2.0)
            if snap_type == 'MID':
                d = 9.0
                sh.uniform_float("color", (0.0, 0.9, 0.85, 1.0))
                batch_for_shader(sh, 'LINE_STRIP', {"pos": [
                    (x, y+d), (x+d, y), (x, y-d), (x-d, y), (x, y+d)]}).draw(sh)
            else:
                s = 8.0 if snap_type == 'VERT' else 6.0
                sh.uniform_float("color", (0.0, 0.5, 1.0, 1.0))
                batch_for_shader(sh, 'LINE_STRIP', {"pos": [
                    (x-s,y-s),(x+s,y-s),(x+s,y+s),(x-s,y+s),(x-s,y-s)]}).draw(sh)

    if _pt1 is not None:
        w1 = _pt1["obj"].matrix_world @ _pt1["local"] if _pt1["obj"] else _pt1["world"]
        sp = to2d(w1)
        if sp:
            sh.bind()
            sh.uniform_float("color", (0.1, 0.1, 0.1, 1.0))
            gpu.state.point_size_set(8.0)
            batch_for_shader(sh, 'POINTS', {"pos": [sp]}).draw(sh)
        wcur = None
        if _snap_pt:
            wcur = _snap_pt["obj"].matrix_world @ _snap_pt["local"] if _snap_pt["obj"] else _snap_pt["world"]
        elif _cursor:
            wcur = _cursor
        if wcur:
            draw_segment(w1, wcur, 0.5)

    gpu.state.blend_set('NONE')


def save_point(item_pt, pt_dict):
    if pt_dict["obj"] is not None:
        item_pt.is_snapped = True
        item_pt.obj_name = pt_dict["obj"].name
        item_pt.local = pt_dict["local"]
        item_pt.world = pt_dict["world"]
    else:
        item_pt.is_snapped = False
        item_pt.obj_name = ""
        item_pt.local = (0, 0, 0)
        item_pt.world = pt_dict["world"]


class TapeMeasurePoint(bpy.types.PropertyGroup):
    is_snapped: bpy.props.BoolProperty(default=False)
    obj_name: bpy.props.StringProperty()
    local: bpy.props.FloatVectorProperty(size=3)
    world: bpy.props.FloatVectorProperty(size=3)


class TapeMeasureItem(bpy.types.PropertyGroup):
    pt1: bpy.props.PointerProperty(type=TapeMeasurePoint)
    pt2: bpy.props.PointerProperty(type=TapeMeasurePoint)


class MEASURE_OT_TapeMeasure(bpy.types.Operator):
    bl_idname = "measure.tape_measure"
    bl_label = "Tape Measure"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        global _pt1, _snap_pt, _cursor

        rv3d = context.region_data
        mx, my = event.mouse_region_x, event.mouse_region_y
        win_region = next((r for r in context.area.regions if r.type == 'WINDOW'), None)
        region = win_region or context.region
        in_viewport = (rv3d is not None and win_region is not None and
                       win_region.x <= event.mouse_x <= win_region.x + win_region.width and
                       win_region.y <= event.mouse_y <= win_region.y + win_region.height)

        if event.type == 'MOUSEMOVE':
            if in_viewport:
                _snap_pt = find_snap(context, mx, my)
                if not _snap_pt:
                    depth = (_pt1["obj"].matrix_world @ _pt1["local"]
                             if _pt1 and _pt1["obj"] else
                             (_pt1["world"] if _pt1 else Vector((0,0,0))))
                    _cursor = view3d_utils.region_2d_to_location_3d(
                        region, rv3d, Vector((mx, my)), depth)
            context.area.tag_redraw()
            return {'PASS_THROUGH'}

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if not in_viewport:
                return {'PASS_THROUGH'}
            if not _snap_pt:
                return {'PASS_THROUGH'}

            if _pt1 is None:
                _pt1 = _snap_pt
            else:
                item = context.scene.tape_measurements.add()
                save_point(item.pt1, _pt1)
                save_point(item.pt2, _snap_pt)
                _pt1 = None
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}

        elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            if _pt1 is not None:
                _pt1 = None
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            else:
                _snap_pt = None
                _cursor = None
                return {'FINISHED'}

        elif event.type == 'ESC':
            _pt1 = None
            _snap_pt = None
            _cursor = None
            return {'FINISHED'}

        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        global _handle, _pt1, _snap_pt, _cursor
        _pt1 = None
        _snap_pt = None
        _cursor = None
        if not _handle:
            _handle = bpy.types.SpaceView3D.draw_handler_add(
                draw_cb, (), 'WINDOW', 'POST_PIXEL'
            )
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


@bpy.app.handlers.persistent
def load_handler(dummy):
    global _handle
    if not _handle:
        _handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_cb, (), 'WINDOW', 'POST_PIXEL'
        )


def register():
    bpy.utils.register_class(TapeMeasurePoint)
    bpy.utils.register_class(TapeMeasureItem)
    bpy.utils.register_class(MEASURE_OT_TapeMeasure)
    bpy.types.Scene.tape_measurements = bpy.props.CollectionProperty(type=TapeMeasureItem)
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)


def unregister():
    global _handle
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    if _handle:
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
    if hasattr(bpy.types.Scene, 'tape_measurements'):
        del bpy.types.Scene.tape_measurements
    bpy.utils.unregister_class(MEASURE_OT_TapeMeasure)
    bpy.utils.unregister_class(TapeMeasureItem)
    bpy.utils.unregister_class(TapeMeasurePoint)
