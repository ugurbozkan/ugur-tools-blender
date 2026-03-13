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

    EDGE_THRESH = 20.0

    FACE_THRESH = 20.0



    best_type = None

    best_dist = VERT_THRESH

    best_co = None

    best_obj = None



    for obj in context.visible_objects:

        if obj.type != 'MESH':

            continue

        if obj.hide_viewport:

            continue



        bm = obj.evaluated_get(depsgraph).data



        for v in bm.vertices:

            wc = obj.matrix_world @ v.co

            rc = location_3d_to_region_2d(region, rv3d, wc)

            if rc:

                d = (coord - rc).length

                if d < best_dist:

                    best_type = 'VERT'

                    best_dist = d

                    best_co = wc

                    best_obj = obj



        for e in bm.edges:

            v0 = obj.matrix_world @ e.verts[0].co

            v1 = obj.matrix_world @ e.verts[1].co

            r0 = location_3d_to_region_2d(region, rv3d, v0)

            r1 = location_3d_to_region_2d(region, rv3d, v1)

            if r0 and r1:

                t = max(0, min(1, ((coord - r0) | (r1 - r0)) / ((r1 - r0) | (r1 - r0))))

                p = r0 + t * (r1 - r0)

                d = (coord - p).length

                if d < best_dist:

                    best_type = 'EDGE'

                    best_dist = d

                    best_co = v0 + t * (v1 - v0)

                    best_obj = obj



        for f in bm.faces:

            avg = Vector()

            for v in f.verts:

                avg += obj.matrix_world @ v.co

            avg /= len(f.verts)

            ra = location_3d_to_region_2d(region, rv3d, avg)

            if ra:

                d = (coord - ra).length

                if d < FACE_THRESH and d < best_dist:

                    best_type = 'FACE'

                    best_dist = d

                    best_co = avg

                    best_obj = obj



    return {'type': best_type, 'co': best_co, 'obj': best_obj, 'dist': best_dist}

