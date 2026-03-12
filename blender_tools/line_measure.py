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
