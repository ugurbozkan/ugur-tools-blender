import bpy

import blf

import gpu

import math

from gpu_extras.batch import batch_for_shader

from mathutils import Vector

from bpy_extras.view3d_utils import (

    location_3d_to_region_2d as l3d2r2d,

    region_2d_to_origin_3d as r2d2o3d,

    region_2d_to_vector_3d as r2d2v3d,

    region_2d_to_location_3d as r2d2l3d,

)



# Each guide is a dict:

# {"origin", "direction", "dist", "edge_w1", "edge_w2", "perp_dir"}

_guides = []

_handle = None

_mesh_cache = {}



EDGE_THRESH  = 20.0

GUIDE_THRESH = 18.0   # guide origin click threshold (pixels)





def _mat_key(mat):

    return (mat[0][0], mat[0][1], mat[0][2], mat[0][3],

            mat[1][0], mat[1][1], mat[1][2], mat[1][3],

            mat[2][0], mat[2][1], mat[2][2], mat[2][3])





NUM_MAP = {

    'ZERO':'0','ONE':'1','TWO':'2','THREE':'3','FOUR':'4',

    'FIVE':'5','SIX':'6','SEVEN':'7','EIGHT':'8','NINE':'9',

    'NUMPAD_0':'0','NUMPAD_1':'1','NUMPAD_2':'2','NUMPAD_3':'3',

    'NUMPAD_4':'4','NUMPAD_5':'5','NUMPAD_6':'6','NUMPAD_7':'7',

    'NUMPAD_8':'8','NUMPAD_9':'9',

}





def _in_front(rv3d, wp):

    return (rv3d.view_matrix @ wp).z < 0





def _on_screen(region, sc):

    return sc is not None and 0 <= sc.x <= region.width and 0 <= sc.y <= region.height





def _ray_plane(ro, rd, pp, pn):

    denom = rd.dot(pn)

    if abs(denom) < 1e-6:

        return None

    t = (pp - ro).dot(pn) / denom

    if t < 0:

        return None

    return ro + rd * t





def _cam_forward(rv3d):

    return -Vector(rv3d.view_matrix[2][:3]).normalized()





def _find_edge(context, mx, my):

    region = context.region

    rv3d = context.region_data

    if not rv3d:

        return None

    coord = Vector((mx, my))

    depsgraph = context.evaluated_depsgraph_get()

    best_d = EDGE_THRESH

    best = None

    cam_fwd = _cam_forward(rv3d)

    visible_names = set()



    for obj in context.visible_objects:

        if obj.type != 'MESH':

            continue

        obj_ev = obj.evaluated_get(depsgraph)

        mat = obj_ev.matrix_world

        name = obj_ev.name

        visible_names.add(name)

        mk = _mat_key(mat)



        cached = _mesh_cache.get(name)

        if cached and cached[0] == mk:

            verts_world, edge_fn_candidates = cached[1], cached[2]

        else:

            mesh = obj_ev.data

            mat3 = mat.to_3x3()

            verts_world = [mat @ v.co for v in mesh.vertices]

            edge_fn_candidates = {}

            for poly in mesh.polygons:

                fn_world = (mat3 @ poly.normal).normalized()

                vlist = list(poly.vertices)

                pn = len(vlist)

                for i in range(pn):

                    v1, v2 = vlist[i], vlist[(i + 1) % pn]

                    k = (min(v1, v2), max(v1, v2))

                    if k not in edge_fn_candidates:

                        edge_fn_candidates[k] = []

                    edge_fn_candidates[k].append(fn_world)

            _mesh_cache[name] = (mk, verts_world, edge_fn_candidates)



        mesh = obj_ev.data

        for edge in mesh.edges:

            vi0, vi1 = edge.vertices[0], edge.vertices[1]

            w1, w2 = verts_world[vi0], verts_world[vi1]

            if not _in_front(rv3d, w1) or not _in_front(rv3d, w2):

                continue

            sc1 = l3d2r2d(region, rv3d, w1)

            sc2 = l3d2r2d(region, rv3d, w2)

            if sc1 is None or sc2 is None:

                continue

            if not _on_screen(region, sc1) and not _on_screen(region, sc2):

                continue

            k = (min(vi0, vi1), max(vi0, vi1))

            adj_normals = edge_fn_candidates.get(k, [])

            if adj_normals and not any(n.dot(cam_fwd) < 0.05 for n in adj_normals):

                continue

            ev = Vector(sc2) - Vector(sc1)

            el = ev.length

            if el < 0.001:

                continue

            t = max(0.0, min(1.0, (coord - Vector(sc1)).dot(ev) / (el * el)))

            closest = Vector(sc1) + t * ev

            d = (coord - closest).length

            if d < best_d:

                best_d = d

                normals_sorted = sorted(adj_normals, key=lambda n: n.dot(cam_fwd))

                best = (w1.copy(), w2.copy(), normals_sorted)



    for stale in [k for k in _mesh_cache if k not in visible_names]:

        del _mesh_cache[stale]

    return best





def _find_guide_at(region, rv3d, mx, my):

    """Returns guide index near click position, otherwise None."""

    coord = Vector((mx, my))

    for i, g in enumerate(_guides):

        sc = l3d2r2d(region, rv3d, g["origin"])

        if sc and (coord - sc).length < GUIDE_THRESH:

            return i

    return None





def _click_face_normal(context, depsgraph, region, rv3d, mx, my):

    coord = Vector((mx, my))

    ro = r2d2o3d(region, rv3d, coord)

    rd = r2d2v3d(region, rv3d, coord).normalized()

    result, _loc, normal, _idx, _obj, _mat = context.scene.ray_cast(

        depsgraph, ro + rd * 1e-4, rd

    )

    return normal if result else None





def _compute_perp_dir(ew1, ew2, candidate_normals, rv3d):

    edge_dir = (ew2 - ew1).normalized()

    for fn in (candidate_normals or []):

        pd = edge_dir.cross(fn)

        if pd.length > 1e-6:

            return pd.normalized()

    view_up = rv3d.view_matrix.inverted().col[1].xyz.normalized()

    pd = edge_dir.cross(view_up)

    if pd.length > 1e-6:

        return pd.normalized()

    return None





def _get_mouse_offset(region, rv3d, ew1, ew2, perp_dir, mx, my):

    if perp_dir is None:

        return None, 0.0

    edge_mid = (ew1 + ew2) / 2.0

    mouse_3d = r2d2l3d(region, rv3d, Vector((mx, my)), edge_mid)

    if mouse_3d is None:

        return None, 0.0

    offset_dist = (mouse_3d - edge_mid).dot(perp_dir)

    if abs(offset_dist) < 1e-6:

        return None, 0.0

    direction = perp_dir if offset_dist > 0 else -perp_dir

    return direction, abs(offset_dist)





def _fmt_dist(dist_bu):

    us = bpy.context.scene.unit_settings

    if us.system == 'NONE':

        return "%.4f" % dist_bu

    dist_m = dist_bu * us.scale_length

    unit = us.length_unit

    if unit == 'MILLIMETERS':  return "%.2f mm"  % (dist_m * 1000)

    if unit == 'CENTIMETERS':  return "%.3f cm"  % (dist_m * 100)

    if unit == 'KILOMETERS':   return "%.6f km"  % (dist_m / 1000)

    if unit == 'FEET':         return "%.4f ft"  % (dist_m * 3.28084)

    if unit == 'INCHES':       return "%.3f in"  % (dist_m * 39.3701)

    if unit == 'MILES':        return "%.6f mi"  % (dist_m / 1609.34)

    if unit == 'ADAPTIVE':

        if dist_m >= 1.0:   return "%.4f m"  % dist_m

        if dist_m >= 0.01:  return "%.3f cm" % (dist_m * 100)

        return "%.2f mm" % (dist_m * 1000)

    return "%.4f m" % dist_m





def _input_to_bu(value_str):

    """Converts user-entered value (in active units) to Blender Units."""

    try:

        val = float(value_str)

    except ValueError:

        return None

    us = bpy.context.scene.unit_settings

    if us.system == 'NONE':

        return val

    unit = us.length_unit

    # Convert to meters first

    to_m = {

        'MILLIMETERS': 0.001,

        'CENTIMETERS': 0.01,

        'METERS':      1.0,

        'KILOMETERS':  1000.0,

        'FEET':        0.3048,

        'INCHES':      0.0254,

        'MILES':       1609.344,

        'ADAPTIVE':    1.0,

    }

    val_m = val * to_m.get(unit, 1.0)

    # Meters → Blender Unit

    return val_m / us.scale_length





def _unit_suffix():

    us = bpy.context.scene.unit_settings

    if us.system == 'NONE':

        return ""

    return {

        'MILLIMETERS': 'mm', 'CENTIMETERS': 'cm', 'METERS': 'm',

        'KILOMETERS': 'km', 'FEET': 'ft', 'INCHES': 'in',

        'MILES': 'mi', 'ADAPTIVE': 'm',

    }.get(us.length_unit, 'm')





def _make_guide(ew1, ew2, offset_dir, dist):

    edge_dir = (ew2 - ew1).normalized()

    edge_mid = (ew1 + ew2) / 2.0

    origin = edge_mid + offset_dir * dist

    return {

        "origin":    origin.copy(),

        "direction": edge_dir.copy(),

        "dist":      dist,

        "edge_w1":   ew1.copy(),

        "edge_w2":   ew2.copy(),

        "perp_dir":  offset_dir.copy(),

    }





def _guide_screen_pts(region, rv3d, origin, direction):

    if not _in_front(rv3d, origin):

        return None, None

    sc_orig = l3d2r2d(region, rv3d, origin)

    if sc_orig is None:

        return None, None

    sc2 = None

    for step in (1.0, 5.0, 20.0, -1.0, -5.0, -20.0):

        p = origin + direction * step

        if not _in_front(rv3d, p):

            continue

        s = l3d2r2d(region, rv3d, p)

        if s is not None and (s - sc_orig).length > 0.5:

            sc2 = s

            break

    if sc2 is None:

        return None, None

    dx = sc2.x - sc_orig.x

    dy = sc2.y - sc_orig.y

    w, h = float(region.width), float(region.height)

    ts = []

    if abs(dx) > 1e-6:

        ts += [(0 - sc_orig.x) / dx, (w - sc_orig.x) / dx]

    if abs(dy) > 1e-6:

        ts += [(0 - sc_orig.y) / dy, (h - sc_orig.y) / dy]

    pts = []

    for t in ts:

        x = sc_orig.x + t * dx

        y = sc_orig.y + t * dy

        if -1 <= x <= w + 1 and -1 <= y <= h + 1:

            pts.append((x, y))

    if len(pts) < 2:

        return None, None

    return pts[0], pts[-1]





def _draw_dashed(sh, p1, p2, dash=12, gap=6):

    dx, dy = p2[0] - p1[0], p2[1] - p1[1]

    l = math.sqrt(dx * dx + dy * dy)

    if l < 1:

        return

    nx, ny = dx / l, dy / l

    coords = []

    t = 0.0

    while t < l:

        t2 = min(t + dash, l)

        coords += [(p1[0] + nx * t, p1[1] + ny * t),

                   (p1[0] + nx * t2, p1[1] + ny * t2)]

        t += dash + gap

    if coords:

        batch_for_shader(sh, 'LINES', {"pos": coords}).draw(sh)





def _draw_label(sh, cx, cy, text):

    blf.size(0, 14)

    tw, th = blf.dimensions(0, text)

    px, py = 7, 4

    bx, by = cx - tw / 2 - px, cy + 14

    bw, bh = tw + px * 2, th + py * 2

    sh.bind()

    sh.uniform_float("color", (1.0, 1.0, 1.0, 0.95))

    batch_for_shader(sh, 'TRI_FAN', {"pos": [

        (bx, by), (bx + bw, by), (bx + bw, by + bh), (bx, by + bh)

    ]}).draw(sh)

    sh.bind()

    sh.uniform_float("color", (0.2, 0.2, 0.2, 1.0))

    gpu.state.line_width_set(1.0)

    batch_for_shader(sh, 'LINE_STRIP', {"pos": [

        (bx, by), (bx + bw, by), (bx + bw, by + bh), (bx, by + bh), (bx, by)

    ]}).draw(sh)

    blf.color(0, 0.05, 0.05, 0.05, 1.0)

    blf.position(0, bx + px, by + py, 0)

    blf.draw(0, text)





def _draw_guide_origin_marker(sh, sc, editing=False):

    """Draw small circle marker at guide origin."""

    r = 5.0

    segs = 12

    coords = [

        (sc.x + math.cos(2 * math.pi * i / segs) * r,

         sc.y + math.sin(2 * math.pi * i / segs) * r)

        for i in range(segs + 1)

    ]

    sh.bind()

    color = (0.0, 0.6, 1.0, 1.0) if editing else (0.3, 0.3, 0.3, 0.8)

    sh.uniform_float("color", color)

    gpu.state.line_width_set(1.5 if editing else 1.0)

    batch_for_shader(sh, 'LINE_STRIP', {"pos": coords}).draw(sh)





_shader = None





def _get_shader():

    global _shader

    if _shader is None:

        _shader = gpu.shader.from_builtin('UNIFORM_COLOR')

    return _shader





def draw_cb(op, _dummy):

    ctx = bpy.context

    if not ctx.scene.measure_visible:

        return

    region = ctx.region

    rv3d = ctx.region_data

    if not region or not rv3d:

        return



    gpu.state.blend_set('ALPHA')

    sh = _get_shader()



    edit_idx = getattr(op, '_edit_idx', None)



    # Saved guides

    for i, g in enumerate(_guides):

        is_editing = (edit_idx == i)

        origin    = g["origin"]

        direction = g["direction"]

        dist      = g["dist"]



        a, b = _guide_screen_pts(region, rv3d, origin, direction)

        if a and b:

            sh.bind()

            # Edited guide is blue, others are dark

            line_color = (0.0, 0.5, 1.0, 0.9) if is_editing else (0.1, 0.1, 0.1, 0.9)

            sh.uniform_float("color", line_color)

            gpu.state.line_width_set(2.0 if is_editing else 1.5)

            _draw_dashed(sh, a, b)



        sc = l3d2r2d(region, rv3d, origin)

        if sc and _on_screen(region, sc):

            _draw_guide_origin_marker(sh, sc, editing=is_editing)

            label = _fmt_dist(dist)

            _draw_label(sh, sc.x, sc.y, label)



    # Selected edge — blue

    if op._edge:

        def to2d(p):

            sc = l3d2r2d(region, rv3d, p)

            return (sc.x, sc.y) if sc else None

        a, b = to2d(op._edge[0]), to2d(op._edge[1])

        if a and b:

            sh.bind()

            sh.uniform_float("color", (0.0, 0.5, 1.0, 1.0))

            gpu.state.line_width_set(2.0)

            batch_for_shader(sh, 'LINES', {"pos": [a, b]}).draw(sh)



    # Preview guide

    if op._preview:

        orig, direc = op._preview["origin"], op._preview["direction"]

        dist        = op._preview["dist"]

        a, b = _guide_screen_pts(region, rv3d, orig, direc)

        if a and b:

            sh.bind()

            sh.uniform_float("color", (0.1, 0.1, 0.1, 0.5))

            gpu.state.line_width_set(1.5)

            _draw_dashed(sh, a, b)

            sc = l3d2r2d(region, rv3d, orig)

            if sc:

                label = (op._typed + " " + _unit_suffix()) if op._typed else _fmt_dist(dist)

                _draw_label(sh, sc.x, sc.y, label)



    gpu.state.blend_set('NONE')





class MEASURE_OT_Guide(bpy.types.Operator):

    bl_idname = "measure.guide"

    bl_label = "Guide Line"

    bl_options = {'REGISTER'}



    _edge       = None

    _perp_dir   = None

    _offset_dir = None

    _preview    = None   # guide dict (preview)

    _typed      = ""

    _dist       = 0.0

    _phase      = 'EDGE'   # 'EDGE' | 'OFFSET' | 'OFFSET_EDIT'

    _edit_idx   = None     # index of guide being edited



    def modal(self, context, event):

        if not context.area:

            return {'PASS_THROUGH'}



        rv3d   = context.region_data

        region = context.region

        mx, my = event.mouse_region_x, event.mouse_region_y



        if event.type == 'MOUSEMOVE':

            if rv3d:

                if self._phase == 'EDGE':

                    self._edge    = _find_edge(context, mx, my)

                    self._preview = None

                elif self._phase in ('OFFSET', 'OFFSET_EDIT') and not self._typed:

                    ew1, ew2 = self._edge[0], self._edge[1]

                    odir, dist = _get_mouse_offset(region, rv3d, ew1, ew2,

                                                   self._perp_dir, mx, my)

                    if odir:

                        self._offset_dir = odir

                        self._dist       = dist

                        self._preview    = _make_guide(ew1, ew2, odir, dist)

            context.area.tag_redraw()

            return {'PASS_THROUGH'}



        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            if not rv3d:

                return {'PASS_THROUGH'}



            if self._phase == 'EDGE':

                # First check if existing guide was clicked

                clicked_g = _find_guide_at(region, rv3d, mx, my)

                if clicked_g is not None:

                    g = _guides[clicked_g]

                    self._edit_idx   = clicked_g

                    self._edge       = (g["edge_w1"], g["edge_w2"], [])

                    self._perp_dir   = g["perp_dir"]

                    self._offset_dir = g["perp_dir"]

                    self._dist       = g["dist"]

                    self._typed      = ""

                    self._preview    = _make_guide(g["edge_w1"], g["edge_w2"],

                                                   g["perp_dir"], g["dist"])

                    self._phase      = 'OFFSET_EDIT'

                    self._update_header(context)

                elif self._edge:

                    ew1, ew2, normals = self._edge

                    depsgraph = context.evaluated_depsgraph_get()

                    click_fn  = _click_face_normal(context, depsgraph,

                                                   region, rv3d, mx, my)

                    all_normals     = ([click_fn] if click_fn else []) + normals

                    self._perp_dir   = _compute_perp_dir(ew1, ew2, all_normals, rv3d)

                    self._offset_dir = self._perp_dir   # so typing can start immediately

                    self._phase      = 'OFFSET'

                    self._typed      = ""

                    self._dist       = 0.0

                    self._preview    = None

                    self._update_header(context)

                else:

                    return {'PASS_THROUGH'}



            elif self._phase == 'OFFSET':

                if self._preview:

                    _guides.append(self._preview)

                self._reset_offset(context)



            elif self._phase == 'OFFSET_EDIT':

                if self._preview:

                    _guides[self._edit_idx] = self._preview

                self._reset_offset(context)



            context.area.tag_redraw()

            return {'RUNNING_MODAL'}



        elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':

            if self._phase in ('OFFSET', 'OFFSET_EDIT'):

                # If editing, preserve original guide

                self._reset_offset(context)

                context.area.tag_redraw()

                return {'RUNNING_MODAL'}

            elif _guides:

                _guides.pop()

                context.area.tag_redraw()

                return {'RUNNING_MODAL'}

            else:

                self._stop_modal(context)

                return {'FINISHED'}



        elif event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':

            if self._phase in ('OFFSET', 'OFFSET_EDIT') and self._typed and self._offset_dir:

                val_bu = _input_to_bu(self._typed)

                if val_bu is not None and val_bu > 0:

                    ew1, ew2 = self._edge[0], self._edge[1]

                    g = _make_guide(ew1, ew2, self._offset_dir, val_bu)

                    if self._phase == 'OFFSET_EDIT':

                        _guides[self._edit_idx] = g

                    else:

                        _guides.append(g)

                    self._reset_offset(context)

                    context.area.tag_redraw()

                    return {'RUNNING_MODAL'}

            return {'PASS_THROUGH'}



        elif event.type == 'ESC' and event.value == 'PRESS':

            self._stop_modal(context)

            return {'FINISHED'}



        elif self._phase in ('OFFSET', 'OFFSET_EDIT') and event.value in {'PRESS', 'REPEAT'}:

            if event.type == 'BACK_SPACE':

                self._typed = self._typed[:-1]

                self._update_preview()

                self._update_header(context)

                context.area.tag_redraw()

                return {'RUNNING_MODAL'}

            # Character input: event.unicode independent of keyboard layout

            ch = event.unicode

            if ch and ch in '0123456789':

                self._typed += ch

                self._update_preview()

                self._update_header(context)

                context.area.tag_redraw()

                return {'RUNNING_MODAL'}

            if ch == '.' and '.' not in self._typed:

                self._typed += '.'

                self._update_header(context)

                context.area.tag_redraw()

                return {'RUNNING_MODAL'}



        elif event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:

            return {'PASS_THROUGH'}



        return {'PASS_THROUGH'}



    def _update_preview(self):

        dir_ = self._offset_dir or self._perp_dir

        if self._edge and self._typed and dir_:

            val_bu = _input_to_bu(self._typed)

            if val_bu is not None and val_bu > 0:

                self._dist       = val_bu

                self._offset_dir = dir_

                ew1, ew2         = self._edge[0], self._edge[1]

                self._preview    = _make_guide(ew1, ew2, dir_, val_bu)



    def _update_header(self, context):

        if not context.area:

            return

        suffix = _unit_suffix()

        typed  = self._typed or "…"

        if self._phase == 'OFFSET_EDIT':

            context.area.header_text_set(

                f"Edit Guide — Distance: {typed} {suffix}  |  Enter: confirm  |  RMB / ESC: cancel"

            )

        else:

            context.area.header_text_set(

                f"Guide — Distance: {typed} {suffix}  |  Enter: confirm  |  RMB: cancel"

            )



    def _reset_offset(self, context=None):

        self._phase      = 'EDGE'

        self._edge       = None

        self._perp_dir   = None

        self._preview    = None

        self._offset_dir = None

        self._typed      = ""

        self._edit_idx   = None

        if context and context.area:

            context.area.header_text_set(

                "Guide — Hover over edge and click  |  Click existing guide: edit  |  ESC: exit"

            )



    def _stop_modal(self, context):

        self._reset_offset()

        if context.area:

            context.area.header_text_set(None)

            context.area.tag_redraw()



    def invoke(self, context, event):

        global _handle

        self._reset_offset()   # context not available yet, header set later

        self._dist = 0.0

        context.area.header_text_set(

            "Guide — Hover over edge and click  |  Click existing guide: edit  |  ESC: exit"

        )

        if _handle:

            bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')

        _handle = bpy.types.SpaceView3D.draw_handler_add(

            draw_cb, (self, None), 'WINDOW', 'POST_PIXEL'

        )

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}





def register():

    bpy.utils.register_class(MEASURE_OT_Guide)





def unregister():

    global _handle

    if _handle:

        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')

        _handle = None

    _guides.clear()

    bpy.utils.unregister_class(MEASURE_OT_Guide)

