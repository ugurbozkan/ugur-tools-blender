import bpy

import gpu

import blf

from gpu_extras.batch import batch_for_shader

from mathutils import Vector

from bpy_extras.view3d_utils import location_3d_to_region_2d



_handle = None

_active = False





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





def draw_cb():

    ctx = bpy.context

    if not ctx.scene.measure_visible:

        return

    obj = ctx.active_object

    if not obj or obj.type != 'MESH':

        return

    region = ctx.region

    rv3d = ctx.region_data

    if not region or not rv3d:

        return



    mat = obj.matrix_world

    corners = [mat @ Vector(c) for c in obj.bound_box]



    screen_corners = []

    for c in corners:

        sc = location_3d_to_region_2d(region, rv3d, c)

        screen_corners.append((sc.x, sc.y) if sc else (0.0, 0.0))



    indices = [

        (0,1),(1,2),(2,3),(3,0),

        (4,5),(5,6),(6,7),(7,4),

        (0,4),(1,5),(2,6),(3,7),

    ]

    coords = []

    for a, b in indices:

        coords += [screen_corners[a], screen_corners[b]]



    shader = gpu.shader.from_builtin('UNIFORM_COLOR')

    gpu.state.blend_set('ALPHA')

    gpu.state.line_width_set(1.5)

    shader.bind()

    shader.uniform_float("color", (0.1, 0.1, 0.1, 0.8))

    batch_for_shader(shader, 'LINES', {"pos": coords}).draw(shader)



    xs = [c.x for c in corners]

    ys = [c.y for c in corners]

    zs = [c.z for c in corners]

    sx = max(xs) - min(xs)

    sy = max(ys) - min(ys)

    sz = max(zs) - min(zs)



    def label(pos, text):

        sc = location_3d_to_region_2d(region, rv3d, pos)

        if not sc:

            return

        blf.size(0, 14)

        tw, th = blf.dimensions(0, text)

        px, py = 6, 4

        bx = sc.x + 4

        by = sc.y + 4

        bw, bh = tw + px*2, th + py*2

        shader.bind()

        shader.uniform_float("color", (1.0, 1.0, 1.0, 0.92))

        batch_for_shader(shader, 'TRI_FAN', {"pos": [

            (bx, by), (bx+bw, by), (bx+bw, by+bh), (bx, by+bh)]}).draw(shader)

        shader.bind()

        shader.uniform_float("color", (0.2, 0.2, 0.2, 1.0))

        gpu.state.line_width_set(1.0)

        batch_for_shader(shader, 'LINE_STRIP', {"pos": [

            (bx, by), (bx+bw, by), (bx+bw, by+bh), (bx, by+bh), (bx, by)]}).draw(shader)

        blf.color(0, 0.05, 0.05, 0.05, 1.0)

        blf.position(0, bx + px, by + py, 0)

        blf.draw(0, text)



    label((corners[0] + corners[1]) / 2, "X: " + _fmt_dist(sx))

    label((corners[0] + corners[3]) / 2, "Y: " + _fmt_dist(sy))

    label((corners[0] + corners[4]) / 2, "Z: " + _fmt_dist(sz))



    gpu.state.blend_set('NONE')





class MEASURE_OT_BBoxMeasure(bpy.types.Operator):

    bl_idname = "measure.bbox_measure"

    bl_label = "BBox Measure"

    bl_options = {'REGISTER'}



    def execute(self, context):

        global _handle, _active

        if _active:

            if _handle:

                bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')

                _handle = None

            _active = False

        else:

            _handle = bpy.types.SpaceView3D.draw_handler_add(

                draw_cb, (), 'WINDOW', 'POST_PIXEL'

            )

            _active = True

        context.area.tag_redraw()

        return {'FINISHED'}





class MEASURE_PT_BBoxPanel(bpy.types.Panel):

    bl_label = "BBox"

    bl_idname = "MEASURE_PT_bbox_sub"

    bl_space_type = 'VIEW_3D'

    bl_region_type = 'UI'

    bl_category = "Measure"

    bl_parent_id = "MEASURE_PT_main"

    bl_options = {'HIDE_HEADER'}



    def draw(self, context):

        icon = 'RADIOBUT_ON' if _active else 'RADIOBUT_OFF'

        self.layout.operator("measure.bbox_measure", icon=icon, text="BBox Measure")





def register():

    bpy.utils.register_class(MEASURE_OT_BBoxMeasure)





def unregister():

    global _handle, _active

    if _handle:

        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')

        _handle = None

    _active = False

    bpy.utils.unregister_class(MEASURE_OT_BBoxMeasure)

