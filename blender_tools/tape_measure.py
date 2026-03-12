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
