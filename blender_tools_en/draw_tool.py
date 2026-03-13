import bpy

import blf

import gpu

import bmesh

import math

from gpu_extras.batch import batch_for_shader

from mathutils import Vector

from bpy_extras.view3d_utils import (

    location_3d_to_region_2d as l3d2r2d,

    region_2d_to_origin_3d   as r2d2o3d,

    region_2d_to_vector_3d   as r2d2v3d,

    region_2d_to_location_3d as r2d2l3d,

)



# ── Constants ──────────────────────────────────────────────────────────────────



SNAP_VERT_PX = 15.0

SNAP_MID_PX  = 15.0

SNAP_EDGE_PX = 12.0



AXIS_COLORS = {

    0: (1.0, 0.25, 0.25, 1.0),   # X → red

    1: (0.25, 0.90, 0.25, 1.0),  # Y → green

    2: (0.25, 0.50, 1.00, 1.0),  # Z → blue

}

AXIS_NAMES = {0: 'X', 1: 'Y', 2: 'Z'}





# ── Unit helpers ───────────────────────────────────────────────────────────────



def _fmt_dist(dist_bu):

    us = bpy.context.scene.unit_settings

    if us.system == 'NONE':

        return "%.4f" % dist_bu

    m = dist_bu * us.scale_length

    unit = us.length_unit

    if unit == 'MILLIMETERS': return "%.2f mm"  % (m * 1000)

    if unit == 'CENTIMETERS': return "%.3f cm"  % (m * 100)

    if unit == 'FEET':        return "%.4f ft"  % (m * 3.28084)

    if unit == 'INCHES':      return "%.3f in"  % (m * 39.3701)

    if unit == 'ADAPTIVE':

        if m >= 1.0:   return "%.4f m"  % m

        if m >= 0.01:  return "%.3f cm" % (m * 100)

        return "%.2f mm" % (m * 1000)

    return "%.4f m" % m





def _unit_suffix():

    us = bpy.context.scene.unit_settings

    if us.system == 'NONE': return ""

    return {'MILLIMETERS':'mm','CENTIMETERS':'cm','METERS':'m',

            'KILOMETERS':'km','FEET':'ft','INCHES':'in',

            'MILES':'mi','ADAPTIVE':'m'}.get(us.length_unit, 'm')





def _input_to_bu(s):

    try:

        val = float(s)

    except (ValueError, TypeError):

        return None

    us = bpy.context.scene.unit_settings

    if us.system == 'NONE':

        return val

    to_m = {'MILLIMETERS': 0.001, 'CENTIMETERS': 0.01, 'METERS': 1.0,

            'KILOMETERS': 1000.0, 'FEET': 0.3048, 'INCHES': 0.0254,

            'MILES': 1609.344, 'ADAPTIVE': 1.0}

    return val * to_m.get(us.length_unit, 1.0) / us.scale_length





# ── Snap system (Edit Mode) ────────────────────────────────────────────────────



class SnapResult:

    __slots__ = ('world', 'local', 'type', 'edge', 'edge_t', 'face')



    def __init__(self, world, local, snap_type, edge=None, edge_t=0.0, face=None):

        self.world  = world       # Vector (world space)

        self.local  = local       # Vector (local space)

        self.type   = snap_type   # 'VERT' | 'MID' | 'EDGE' | 'FACE'

        self.edge   = edge        # BMEdge or None

        self.edge_t = edge_t      # parameter along edge (for EDGE type)

        self.face   = face        # BMFace or None (for FACE type)





def find_snap_edit(context, mx, my, obj, bm):

    """Edit mode snap: vert > mid > edge > face."""

    region = context.region

    rv3d   = context.region_data

    if not rv3d:

        return None



    coord   = Vector((mx, my))

    mat     = obj.matrix_world

    mat_inv = mat.inverted_safe()



    best_vert = None; best_vert_d = SNAP_VERT_PX

    best_mid  = None; best_mid_d  = SNAP_MID_PX

    best_edge = None; best_edge_d = SNAP_EDGE_PX



    bm.verts.ensure_lookup_table()

    bm.edges.ensure_lookup_table()



    # Vertex snap

    for v in bm.verts:

        wp = mat @ v.co

        sc = l3d2r2d(region, rv3d, wp)

        if sc is None:

            continue

        d = (coord - sc).length

        if d < best_vert_d:

            best_vert_d = d

            best_vert = SnapResult(wp.copy(), v.co.copy(), 'VERT')



    # Edge: midpoint + on-edge

    for edge in bm.edges:

        w1 = mat @ edge.verts[0].co

        w2 = mat @ edge.verts[1].co

        sc1 = l3d2r2d(region, rv3d, w1)

        sc2 = l3d2r2d(region, rv3d, w2)

        if sc1 is None or sc2 is None:

            continue



        # Midpoint snap

        wm  = (w1 + w2) * 0.5

        scm = l3d2r2d(region, rv3d, wm)

        if scm is not None:

            d = (coord - scm).length

            if d < best_mid_d:

                best_mid_d = d

                best_mid = SnapResult(wm.copy(), mat_inv @ wm, 'MID', edge, 0.5)



        # On-edge snap

        ev = Vector(sc2) - Vector(sc1)

        el = ev.length

        if el < 0.5:

            continue

        t = max(0.0, min(1.0, (coord - Vector(sc1)).dot(ev) / (el * el)))

        closest_sc = Vector(sc1) + t * ev

        d = (coord - closest_sc).length

        if d < best_edge_d:

            best_edge_d = d

            wp_e = w1.lerp(w2, t)

            best_edge = SnapResult(wp_e.copy(), mat_inv @ wp_e, 'EDGE', edge, t)



    if best_vert: return best_vert

    if best_mid:  return best_mid

    if best_edge: return best_edge



    # Face snap: raycast

    try:

        ro_local = mat_inv @ r2d2o3d(context.region, rv3d, coord)

        rd_local = (mat_inv.to_3x3() @ r2d2v3d(context.region, rv3d, coord)).normalized()

        result, loc, _normal, fi = obj.ray_cast(ro_local, rd_local)

        if result:

            wp = mat @ loc

            bm.faces.ensure_lookup_table()

            hit_face = bm.faces[fi] if 0 <= fi < len(bm.faces) else None

            return SnapResult(wp.copy(), loc.copy(), 'FACE', face=hit_face)

    except Exception:

        pass



    return None





def _intersect_ray_plane(ro, rd, plane_co, plane_no):

    """Ray-plane intersection (alternative to mathutils.geometry.intersect_ray_plane)."""

    denom = plane_no.dot(rd)

    if abs(denom) < 1e-8:

        return None

    t = (plane_co - ro).dot(plane_no) / denom

    return ro + rd * t





def mouse_to_world(context, mx, my, depth_point):

    """Project mouse to view-perpendicular plane passing through depth_point."""

    region = context.region

    rv3d   = context.region_data

    coord  = Vector((mx, my))

    ro = r2d2o3d(region, rv3d, coord)

    rd = r2d2v3d(region, rv3d, coord).normalized()

    view_n = -Vector(rv3d.view_matrix[2][:3]).normalized()

    hit = _intersect_ray_plane(ro, rd, depth_point, view_n)

    if hit is None:

        hit = r2d2l3d(region, rv3d, coord, depth_point)

    return hit





# ── GPU Draw ───────────────────────────────────────────────────────────────────



def _draw_snap_indicator(sh, sc, snap_type):

    x, y = sc.x, sc.y

    sh.bind()

    gpu.state.line_width_set(2.0)



    if snap_type == 'VERT':

        r, segs = 7.0, 12

        sh.uniform_float("color", (0.15, 0.95, 0.35, 1.0))

        pts = [(x + math.cos(2*math.pi*i/segs)*r,

                y + math.sin(2*math.pi*i/segs)*r) for i in range(segs+1)]

        batch_for_shader(sh, 'LINE_STRIP', {"pos": pts}).draw(sh)



    elif snap_type == 'MID':

        d = 8.0

        sh.uniform_float("color", (0.0, 0.9, 0.85, 1.0))

        batch_for_shader(sh, 'LINE_STRIP', {"pos": [

            (x, y+d),(x+d, y),(x, y-d),(x-d, y),(x, y+d)]}).draw(sh)



    elif snap_type == 'EDGE':

        s = 5.0

        sh.uniform_float("color", (1.0, 0.3, 0.1, 1.0))

        batch_for_shader(sh, 'LINE_STRIP', {"pos": [

            (x-s,y-s),(x+s,y-s),(x+s,y+s),(x-s,y+s),(x-s,y-s)]}).draw(sh)



    elif snap_type == 'FACE':

        d = 6.0

        sh.uniform_float("color", (0.25, 0.45, 1.0, 1.0))

        batch_for_shader(sh, 'LINE_STRIP', {"pos": [

            (x, y+d),(x+d, y),(x, y-d),(x-d, y),(x, y+d)]}).draw(sh)





def _draw_label(sh, cx, cy, text):

    blf.size(0, 13)

    tw, th = blf.dimensions(0, text)

    px, py = 6, 3

    bx, by = cx + 12, cy + 8

    bw, bh = tw + px*2, th + py*2

    sh.bind()

    sh.uniform_float("color", (1.0, 1.0, 1.0, 0.92))

    batch_for_shader(sh, 'TRI_FAN', {"pos": [

        (bx,by),(bx+bw,by),(bx+bw,by+bh),(bx,by+bh)]}).draw(sh)

    sh.bind()

    sh.uniform_float("color", (0.2, 0.2, 0.2, 1.0))

    gpu.state.line_width_set(1.0)

    batch_for_shader(sh, 'LINE_STRIP', {"pos": [

        (bx,by),(bx+bw,by),(bx+bw,by+bh),(bx,by+bh),(bx,by)]}).draw(sh)

    blf.color(0, 0.05, 0.05, 0.05, 1.0)

    blf.position(0, bx+px, by+py, 0)

    blf.draw(0, text)





def _draw_dashed_2d(sh, p1, p2, dash=8, gap=5):

    dx, dy = p2[0]-p1[0], p2[1]-p1[1]

    L = math.sqrt(dx*dx + dy*dy)

    if L < 1:

        return

    nx, ny = dx/L, dy/L

    coords = []

    t = 0.0

    while t < L:

        t2 = min(t+dash, L)

        coords += [(p1[0]+nx*t,  p1[1]+ny*t),

                   (p1[0]+nx*t2, p1[1]+ny*t2)]

        t += dash + gap

    if coords:

        batch_for_shader(sh, 'LINES', {"pos": coords}).draw(sh)





def draw_callback(op, context):

    region = context.region

    rv3d   = context.region_data

    if not region or not rv3d:

        return



    gpu.state.blend_set('ALPHA')

    sh = gpu.shader.from_builtin('UNIFORM_COLOR')



    def to2d(p):

        return l3d2r2d(region, rv3d, p)



    # Preview line ─────────────────────────────────────────────────

    if op._start_world and op._current_world:

        a = to2d(op._start_world)

        b = to2d(op._current_world)

        if a and b:

            if op._locked_axis is not None:

                color = AXIS_COLORS[op._locked_axis]

            else:

                color = (0.95, 0.85, 0.1, 0.95)

            sh.bind()

            sh.uniform_float("color", color)

            gpu.state.line_width_set(2.0)

            batch_for_shader(sh, 'LINES',

                             {"pos": [(a.x, a.y), (b.x, b.y)]}).draw(sh)



            dist  = (op._current_world - op._start_world).length

            label = (op._typed + " " + _unit_suffix()) if op._typed else _fmt_dist(dist)

            _draw_label(sh, (a.x+b.x)*0.5, (a.y+b.y)*0.5, label)



    # Axis constraint guide line ────────────────────────────────────

    if op._start_world and op._locked_axis is not None:

        ax_vec = Vector((0.0, 0.0, 0.0))

        ax_vec[op._locked_axis] = 1.0

        pa = to2d(op._start_world + ax_vec * 500.0)

        pb = to2d(op._start_world - ax_vec * 500.0)

        if pa and pb:

            faint = AXIS_COLORS[op._locked_axis][:3] + (0.30,)

            sh.bind()

            sh.uniform_float("color", faint)

            gpu.state.line_width_set(1.0)

            _draw_dashed_2d(sh, (pb.x, pb.y), (pa.x, pa.y))



    # Start point marker ────────────────────────────────────────────

    if op._start_world:

        sc = to2d(op._start_world)

        if sc:

            sh.bind()

            sh.uniform_float("color", (1.0, 0.6, 0.0, 1.0))

            gpu.state.point_size_set(8.0)

            batch_for_shader(sh, 'POINTS',

                             {"pos": [(sc.x, sc.y)]}).draw(sh)



    # Snap indicator ────────────────────────────────────────────────

    if op._snap:

        sc = to2d(op._snap.world)

        if sc:

            _draw_snap_indicator(sh, sc, op._snap.type)



    # HUD: axis name + typed value ──────────────────────────────────

    if op._locked_axis is not None:

        blf.size(0, 15)

        blf.color(0, *AXIS_COLORS[op._locked_axis])

        blf.position(0, region.width - 90, region.height - 30, 0)

        blf.draw(0, f"Axis: {AXIS_NAMES[op._locked_axis]}")



    if op._typed:

        blf.size(0, 14)

        blf.color(0, 0.95, 0.95, 0.95, 1.0)

        blf.position(0, region.width - 160, 15, 0)

        blf.draw(0, f"► {op._typed} {_unit_suffix()}")



    gpu.state.blend_set('NONE')





# ── Geometry helpers ───────────────────────────────────────────────────────────



def _find_or_create_vert(bm, local_co, thresh=1e-5):

    """Return existing vertex near coordinate, or create new one."""

    bm.verts.ensure_lookup_table()

    for v in bm.verts:

        if (v.co - local_co).length < thresh:

            return v, False

    v = bm.verts.new(local_co)

    return v, True





def _split_edge_at_t(bm, edge, t):

    """Split edge at parameter t (0-1), return new vertex."""

    v1 = edge.verts[0]

    _new_edge, new_vert = bmesh.utils.edge_split(edge, v1, t)

    return new_vert





def _find_cycles(bm, va, vb, max_len=20):

    """Find paths from va to vb excluding direct va-vb connection (BFS)."""

    from collections import deque

    direct = bm.edges.get([va, vb])



    results = []

    queue   = deque([(va, [va])])



    while queue:

        cur, path = queue.popleft()

        if len(path) >= max_len:

            continue

        for e in cur.link_edges:

            if direct and e == direct:

                continue

            nb = e.other_vert(cur)

            if nb == vb and len(path) >= 2:

                results.append(path + [vb])

                continue

            if nb not in path:

                queue.append((nb, path + [nb]))



    return results





def _is_coplanar(verts, eps=1e-4):

    if len(verts) < 3:

        return False

    if len(verts) == 3:

        return True

    v0 = verts[0].co

    n  = (verts[1].co - v0).cross(verts[2].co - v0)

    if n.length < 1e-10:

        return False

    n = n.normalized()

    for v in verts[3:]:

        if abs((v.co - v0).dot(n)) > eps:

            return False

    return True





def _line_seg_param(p1, d1, p2, d2):

    """Find intersection parameters of two 3D lines (p1+t*d1) and (p2+s*d2).

    Works for coplanar lines. Returns (t, s) or None."""

    cross = d1.cross(d2)

    denom = cross.dot(cross)

    if denom < 1e-16:

        return None

    diff = p2 - p1

    t = diff.cross(d2).dot(cross) / denom

    s = diff.cross(d1).dot(cross) / denom

    return t, s





def _try_split_face(bm, face, va, vb):

    """Split face with line va→vb. Try bmesh.utils.face_split, then manual method."""

    # Method 1: Blender API

    try:

        bmesh.utils.face_split(face, va, vb)

        return True

    except Exception:

        pass

    # Method 2: Manual split (fallback if face_split fails)

    verts = list(face.verts)

    try:

        ia, ib = verts.index(va), verts.index(vb)

    except ValueError:

        return False

    if ia == ib:

        return False

    if ia > ib:

        ia, ib = ib, ia

    h1 = verts[ia:ib + 1]

    h2 = verts[ib:] + verts[:ia + 1]

    if len(h1) < 3 or len(h2) < 3:

        return False

    try:

        bm.faces.remove(face)

        bm.faces.new(h1)

        bm.faces.new(h2)

        return True

    except Exception:

        return False





def _edge_valid(edge):

    """Check if BMEdge is still valid (may become invalid after split)."""

    try:

        return edge.is_valid

    except Exception:

        return False





def _knife_cut(bm, local_start, local_end, va, vb, va_new=False, vb_new=False):

    """Knife tool logic: move floating vertices to surface boundary.

    Projects line (and extension) onto coplanar face edges and places vertices

    at boundary points. Existing boundary vertices are unchanged.

    va_new/vb_new: True if vertex was newly created → can be deleted after moving."""

    dir_v = local_end - local_start

    if dir_v.length_squared < 1e-12:

        return va, vb



    va_boundary = len(list(va.link_faces)) > 0

    vb_boundary = len(list(vb.link_faces)) > 0

    if va_boundary and vb_boundary:

        return va, vb



    # Find coplanar faces with line

    # Tolerance: face normal dot distance < 5e-3 (for small float errors)

    bm.faces.ensure_lookup_table()

    faces_hit = []

    for face in bm.faces:

        n = face.normal

        if n.length < 1e-8:

            continue

        fc = face.verts[0].co

        if (abs((local_start - fc).dot(n)) < 5e-3 and

                abs((local_end - fc).dot(n)) < 5e-3):

            faces_hit.append(face)



    if not faces_hit:

        return va, vb



    # Compute intersection parameters with all face edges

    # t: line parameter (0=local_start, 1=local_end, outside = extended)

    # s: edge parameter (0..1)

    cuts = []  # [(t, edge, s), ...]

    seen_ids = set()

    for face in faces_hit:

        for edge in face.edges:

            eid = id(edge)

            if eid in seen_ids:

                continue

            seen_ids.add(eid)

            if not _edge_valid(edge):

                continue

            try:

                ev1 = edge.verts[0].co.copy()

                ev2 = edge.verts[1].co.copy()

            except Exception:

                continue

            ed = ev2 - ev1

            if ed.length_squared < 1e-12:

                continue

            res = _line_seg_param(local_start, dir_v, ev1, ed)

            if res is None:

                continue

            t, s = res

            # Not at edge endpoints (vertex snap already handles those)

            if s < 1e-4 or s > 1 - 1e-4:

                continue

            # Coplanar verification: are two parameter points at same location?

            if (local_start + dir_v * t - (ev1 + ed * s)).length > 5e-3:

                continue

            cuts.append((t, edge, s))



    if not cuts:

        return va, vb



    new_va, new_vb = va, vb

    used_eid = None



    # -- va floating: boundary point closest to t=0 --

    if not va_boundary:

        best = min(cuts, key=lambda x: abs(x[0]))

        t_b, edge_b, s_b = best

        used_eid = id(edge_b)

        if _edge_valid(edge_b):

            try:

                new_va = _split_edge_at_t(bm, edge_b, s_b)

                # Clean up original floating vertex (only if newly created)

                if va_new and va != new_va:

                    try:

                        if len(list(va.link_edges)) == 0:

                            bm.verts.remove(va)

                    except Exception:

                        pass

            except Exception:

                pass



    # -- vb floating: boundary point closest to t=1 (excluding va's edge) --

    if not vb_boundary:

        cuts_vb = []

        for c in cuts:

            if id(c[1]) == used_eid:

                continue

            if _edge_valid(c[1]):

                cuts_vb.append(c)

        # If no valid alternatives, pick from all (degenerate cases)

        if not cuts_vb:

            cuts_vb = [c for c in cuts if _edge_valid(c[1])]

        if cuts_vb:

            best = min(cuts_vb, key=lambda x: abs(x[0] - 1.0))

            t_b, edge_b, s_b = best

            if _edge_valid(edge_b):

                try:

                    new_vb = _split_edge_at_t(bm, edge_b, s_b)

                    if vb_new and vb != new_vb:

                        try:

                            if len(list(vb.link_edges)) == 0:

                                bm.verts.remove(vb)

                        except Exception:

                            pass

                except Exception:

                    pass



    return new_va, new_vb





def _try_make_faces(bm, va, vb):

    """Detect closed cycles via BFS → create faces (free edge case only)."""

    for cycle in _find_cycles(bm, va, vb, max_len=20):

        if len(cycle) < 3:

            continue

        if not _is_coplanar(cycle):

            continue

        try:

            if bm.faces.get(cycle) is None:

                bm.faces.new(cycle)

        except Exception:

            pass





def _snap_needs_edge_split(snap):

    """EDGE or MID snap → need to split edge."""

    return snap and snap.type in ('EDGE', 'MID') and snap.edge is not None





def add_segment(context, obj, world_start, world_end, snap_start, snap_end):

    """Add edge between two points; knife-cut through surfaces."""

    mat     = obj.matrix_world

    mat_inv = mat.inverted_safe()

    bm      = bmesh.from_edit_mesh(obj.data)



    local_start = mat_inv @ world_start

    local_end   = mat_inv @ world_end



    # ── Start vertex ──────────────────────────────────────────

    if _snap_needs_edge_split(snap_start):

        try:

            va = _split_edge_at_t(bm, snap_start.edge, snap_start.edge_t)

            va_new = True

        except Exception:

            va, va_new = _find_or_create_vert(bm, local_start)

    else:

        va, va_new = _find_or_create_vert(bm, local_start)



    # ── End vertex ────────────────────────────────────────────

    if _snap_needs_edge_split(snap_end):

        try:

            vb = _split_edge_at_t(bm, snap_end.edge, snap_end.edge_t)

            vb_new = True

        except Exception:

            vb, vb_new = _find_or_create_vert(bm, local_end)

    else:

        vb, vb_new = _find_or_create_vert(bm, local_end)



    if va == vb:

        bmesh.update_edit_mesh(obj.data)

        return va, vb



    bm.verts.ensure_lookup_table()

    bm.edges.ensure_lookup_table()

    bm.faces.ensure_lookup_table()



    # ── Knife cut: move floating vertices to surface boundary ─

    # Find surface boundary edges crossed by line and place vertices there.

    # Vertices created by EDGE/MID/VERT snap are already at boundary → untouched.

    va, vb = _knife_cut(bm, local_start, local_end, va, vb, va_new, vb_new)



    if va == vb:

        bmesh.update_edit_mesh(obj.data)

        return va, vb



    bm.verts.ensure_lookup_table()

    bm.edges.ensure_lookup_table()

    bm.faces.ensure_lookup_table()



    # ── If shared face exists → face_split ──────────────────────

    # face_split creates both edge and split faces.

    # DO face_split FIRST, NOT AFTER — else orphan edges inside faces.

    shared = list(set(va.link_faces) & set(vb.link_faces))

    if shared:

        for face in shared:

            _try_split_face(bm, face, va, vb)

    else:

        # No shared face: free edge + BFS cycle detection

        if not bm.edges.get([va, vb]):

            try:

                bm.edges.new([va, vb])

            except Exception:

                pass

        bm.verts.ensure_lookup_table()

        bm.edges.ensure_lookup_table()

        bm.faces.ensure_lookup_table()

        _try_make_faces(bm, va, vb)



    bmesh.update_edit_mesh(obj.data)

    return va, vb





# ── Main Operator ──────────────────────────────────────────────────────────────



class MESH_OT_DrawTool(bpy.types.Operator):

    bl_idname  = "mesh.draw_tool"

    bl_label   = "Draw Tool"

    bl_options = {'REGISTER', 'UNDO'}



    @classmethod

    def poll(cls, context):

        obj = context.active_object

        return obj and obj.type == 'MESH' and obj.mode == 'EDIT'



    # State

    _handle       = None

    _start_world  = None   # confirmed start point

    _start_snap   = None   # start SnapResult

    _current_world = None  # real-time preview end point

    _snap          = None  # real-time SnapResult

    _locked_axis   = None  # 0/1/2 or None

    _typed         = ""



    def invoke(self, context, event):

        self._start_world  = None

        self._start_snap   = None

        self._current_world = None

        self._snap          = None

        self._locked_axis   = None

        self._typed         = ""



        self._handle = bpy.types.SpaceView3D.draw_handler_add(

            draw_callback, (self, context), 'WINDOW', 'POST_PIXEL'

        )

        context.window_manager.modal_handler_add(self)

        context.area.header_text_set(

            "Draw  |  Left click: place point  |  X/Y/Z: lock axis  "

            "|  Type number + Enter: distance  |  Right click: cancel/finish"

        )

        return {'RUNNING_MODAL'}



    def modal(self, context, event):

        if not context.area:

            return {'PASS_THROUGH'}



        context.area.tag_redraw()

        rv3d = context.region_data

        mx, my = event.mouse_region_x, event.mouse_region_y

        obj = context.active_object



        # ── Mouse movement ──────────────────────────────────────────

        if event.type == 'MOUSEMOVE':

            if rv3d and obj and obj.mode == 'EDIT':

                depth = self._start_world or Vector((0.0, 0.0, 0.0))

                bm    = bmesh.from_edit_mesh(obj.data)



                if self._locked_axis is None:

                    snap = find_snap_edit(context, mx, my, obj, bm)

                    self._snap = snap

                    raw = snap.world.copy() if snap else mouse_to_world(context, mx, my, depth)

                else:

                    self._snap = None

                    raw = mouse_to_world(context, mx, my, depth)

                    if raw and self._start_world:

                        raw = self._project_to_axis(self._start_world, raw)



                if not self._typed:

                    self._current_world = raw



            return {'PASS_THROUGH'}



        # ── Left click: place point ──────────────────────────────────

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':

            if not rv3d or not obj or obj.mode != 'EDIT':

                return {'PASS_THROUGH'}



            target = self._resolve_target()

            if target is None:

                return {'PASS_THROUGH'}



            if self._start_world is None:

                self._start_world = target

                self._start_snap  = self._snap

                self._typed       = ""

            else:

                self._commit(context, obj, target)



            return {'RUNNING_MODAL'}



        # ── Enter: confirm typed value ───────────────────────────────

        elif event.type in {'RET', 'NUMPAD_ENTER'} and event.value == 'PRESS':

            if self._start_world:

                target = self._resolve_target()

                if target and obj and obj.mode == 'EDIT':

                    self._commit(context, obj, target)

                    return {'RUNNING_MODAL'}

            return {'PASS_THROUGH'}



        # ── Right click: cancel chain / finish ──────────────────────

        elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':

            if self._start_world is not None:

                self._reset_chain()

                return {'RUNNING_MODAL'}

            else:

                self._finish(context)

                return {'FINISHED'}



        # ── ESC: exit ──────────────────────────────────────────────

        elif event.type == 'ESC' and event.value == 'PRESS':

            self._finish(context)

            return {'FINISHED'}



        # ── X / Y / Z: lock axis ───────────────────────────────────

        elif event.value == 'PRESS' and not event.ctrl and not event.shift and not event.alt:

            if event.type == 'X':

                if self._start_world:

                    self._toggle_axis(0)

                    return {'RUNNING_MODAL'}

                return {'PASS_THROUGH'}

            elif event.type == 'Y':

                if self._start_world:

                    self._toggle_axis(1)

                    return {'RUNNING_MODAL'}

                return {'PASS_THROUGH'}

            elif event.type == 'Z':

                if self._start_world:

                    self._toggle_axis(2)

                    return {'RUNNING_MODAL'}

                return {'PASS_THROUGH'}



        # ── Keyboard number input ───────────────────────────────────

        if self._start_world and event.value in {'PRESS', 'REPEAT'}:

            if event.type == 'BACK_SPACE':

                self._typed = self._typed[:-1]

                self._sync_typed_preview()

                return {'RUNNING_MODAL'}

            ch = event.unicode

            if ch and ch in '0123456789':

                self._typed += ch

                self._sync_typed_preview()

                return {'RUNNING_MODAL'}

            if ch == '.' and '.' not in self._typed:

                self._typed += '.'

                return {'RUNNING_MODAL'}



        # ── Viewport navigation pass-through ────────────────────────

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:

            return {'PASS_THROUGH'}



        return {'PASS_THROUGH'}



    # ── Helper methods ───────────────────────────────────────────────────



    def _toggle_axis(self, idx):

        self._locked_axis = None if self._locked_axis == idx else idx

        if self._locked_axis is not None and self._start_world and self._current_world:

            self._current_world = self._project_to_axis(

                self._start_world, self._current_world)

        self._sync_typed_preview()



    def _project_to_axis(self, start, raw):

        ax = Vector((0.0, 0.0, 0.0))

        ax[self._locked_axis] = 1.0

        t = (raw - start).dot(ax)

        return start + ax * t



    def _resolve_target(self):

        """If typed value exists, use it; otherwise use snap/mouse."""

        if self._typed and self._start_world:

            return self._resolve_typed()

        return self._current_world.copy() if self._current_world else None



    def _resolve_typed(self):

        val_bu = _input_to_bu(self._typed)

        if val_bu is None or val_bu <= 0:

            return None

        if self._locked_axis is not None:

            ax = Vector((0.0, 0.0, 0.0))

            ax[self._locked_axis] = 1.0

            return self._start_world + ax * val_bu

        else:

            if self._current_world:

                d = self._current_world - self._start_world

                if d.length > 1e-8:

                    return self._start_world + d.normalized() * val_bu

        return None



    def _sync_typed_preview(self):

        if self._typed and self._start_world:

            target = self._resolve_typed()

            if target:

                self._current_world = target



    def _commit(self, context, obj, world_end):

        snap_end = self._snap if not self._typed else None

        add_segment(context, obj, self._start_world, world_end,

                    self._start_snap, snap_end)

        # Chain: end becomes new start

        self._start_world   = world_end.copy()

        self._start_snap    = None

        self._typed         = ""

        self._locked_axis   = None

        self._current_world = None

        self._snap          = None

        context.area.header_text_set(

            "Draw  |  Left click: continue  |  X/Y/Z: axis  "

            "|  Type + Enter: distance  |  Right click: new segment / ESC: exit"

        )



    def _reset_chain(self):

        self._start_world   = None

        self._start_snap    = None

        self._current_world = None

        self._locked_axis   = None

        self._typed         = ""

        self._snap          = None



    def _finish(self, context):

        if self._handle:

            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

            self._handle = None

        if context.area:

            context.area.header_text_set(None)

            context.area.tag_redraw()





# ── Register ───────────────────────────────────────────────────────────────────



def register():

    bpy.utils.register_class(MESH_OT_DrawTool)





def unregister():

    bpy.utils.unregister_class(MESH_OT_DrawTool)

