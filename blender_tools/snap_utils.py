import bpy
from mathutils import Vector
from bpy_extras.view3d_utils import (
    location_3d_to_region_2d,
    region_2d_to_origin_3d,
    region_2d_to_vector_3d,
)


def find_snap(context, mx, my):
    region = context.region
    rv3d = context.region_data
    if not rv3d:
        return None

    coord = Vector((mx, my))
    depsgraph = context.evaluated_depsgraph_get()

    VERT_THRESH = 20.0
    MID_THRESH  = 20.0
    EDGE_THRESH = 15.0

    best_vert = None
    best_vert_d = VERT_THRESH
    best_mid = None
    best_mid_d = MID_THRESH
    best_edge = None
    best_edge_d = EDGE_THRESH

    for obj in context.visible_objects:
        if obj.type != 'MESH':
            continue
        obj_eval = obj.evaluated_get(depsgraph)
        mat = obj_eval.matrix_world
        mat_inv = mat.inverted()
        mesh = obj_eval.data

        # Vertex snap
        for v in mesh.vertices:
            wp = mat @ v.co
            sc = location_3d_to_region_2d(region, rv3d, wp)
            if sc is None:
                continue
            d = (coord - sc).length
            if d < best_vert_d:
                best_vert_d = d
                best_vert = {"obj": obj, "local": v.co.copy(), "world": wp.copy(),
                             "snap_type": 'VERT'}

        # Midpoint + edge snap (aynı döngüde)
        for edge in mesh.edges:
            w1 = mat @ mesh.vertices[edge.vertices[0]].co
            w2 = mat @ mesh.vertices[edge.vertices[1]].co
            sc1 = location_3d_to_region_2d(region, rv3d, w1)
            sc2 = location_3d_to_region_2d(region, rv3d, w2)
            if sc1 is None or sc2 is None:
                continue

            # Midpoint snap
            mid_world = (w1 + w2) / 2.0
            sc_mid = location_3d_to_region_2d(region, rv3d, mid_world)
            if sc_mid is not None:
                d = (coord - sc_mid).length
                if d < best_mid_d:
                    best_mid_d = d
                    best_mid = {"obj": obj, "local": mat_inv @ mid_world,
                                "world": mid_world.copy(), "snap_type": 'MID'}

            # Edge closest-point snap
            ev = Vector(sc2) - Vector(sc1)
            el = ev.length
            if el < 0.001:
                continue
            t = max(0.0, min(1.0, (coord - Vector(sc1)).dot(ev) / (el * el)))
            closest = Vector(sc1) + t * ev
            d = (coord - closest).length
            if d < best_edge_d:
                best_edge_d = d
                world_pt = w1.lerp(w2, t)
                best_edge = {"obj": obj, "local": mat_inv @ world_pt,
                             "world": world_pt.copy(), "snap_type": 'EDGE'}

    # Öncelik: vertex > midpoint > edge > face
    if best_vert:
        return best_vert
    if best_mid:
        return best_mid
    if best_edge:
        return best_edge

    // Face snap — raycast
    ray_origin = region_2d_to_origin_3d(region, rv3d, coord)
    ray_dir = region_2d_to_vector_3d(region, rv3d, coord)
    hit, location, normal, index, obj, matrix = context.scene.ray_cast(
        depsgraph, ray_origin, ray_dir
    )
    if hit and obj:
        mat_inv = obj.matrix_world.inverted()
        return {"obj": obj, "local": mat_inv @ location, "world": location.copy(),
                "snap_type": 'FACE'}

    return None
