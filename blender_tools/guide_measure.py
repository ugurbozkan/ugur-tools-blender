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

_guides = []
_handle = None
_mesh_cache = {}

EDGE_THRESH  = 20.0
GUIDE_THRESH = 18.0

def _mat_key(mat):
    return (mat[0][0], mat[0][1], mat[0][2], mat[0][3],
            mat[1][0], mat[1][1], mat[1][2], mat[1][3],
            mat[2][0], mat[2][1], mat[2][2], mat[2][3])
NUM_MAP = {'ZERO':'0','ONE':'1','TWO':'2','THREE':'3','FOUR':'4','FIVE':'5','SIX':'6','SEVEN':'7','EIGHT':'8','NINE':'9','NUMPAD_0':'0','NUMPAD_1':'1','NUMPAD_2':'2','NUMPAD_3':'3','NUMPAD_4':'4','NUMPAD_5':'5','NUMPAD_6':'6','NUMPAD_7':'7','NUMPAD_8':'8','NUMPAD_9':'9'}
def _in_front(rv3d, wp):
    return (rv3d.view_matrix @ wp).z < 0
def _on_screen(region, sc):
    return sc is not None and 0 <= sc.x <= region.width and 0 <= sc.y <= region.height
def register():
    bpy.utils.register_class(MEASURE_OT_Guide)
def unregister():
    global _handle
    if _handle:
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
    _guides.clear()
    bpy.utils.unregister_class(MEASURE_OT_Guide)