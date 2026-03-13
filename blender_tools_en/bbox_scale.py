import bpy

from mathutils import Vector





class MEASURE_OT_BBoxScale(bpy.types.Operator):

    bl_idname = "measure.bbox_scale"

    bl_label = "BBox Scale"

    bl_options = {'REGISTER', 'UNDO'}



    axis: bpy.props.EnumProperty(

        items=[('X', 'X', ''), ('Y', 'Y', ''), ('Z', 'Z', '')],

        default='X'

    )

    target_size: bpy.props.FloatProperty(name="Target Size", default=1.0, min=0.0001)



    def execute(self, context):

        obj = context.active_object

        if not obj or obj.type != 'MESH':

            self.report({'ERROR'}, "Select mesh object")

            return {'CANCELLED'}

        mat = obj.matrix_world

        corners = [mat @ Vector(c) for c in obj.bound_box]

        axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[self.axis]

        vals = [c[axis_idx] for c in corners]

        current = max(vals) - min(vals)

        if current < 0.0001:

            self.report({'ERROR'}, "Object size too small")

            return {'CANCELLED'}

        sc = list(obj.scale)

        sc[axis_idx] *= self.target_size / current

        obj.scale = sc

        return {'FINISHED'}



    def invoke(self, context, event):

        obj = context.active_object

        if not obj or obj.type != 'MESH':

            self.report({'ERROR'}, "Select mesh object")

            return {'CANCELLED'}

        mat = obj.matrix_world

        corners = [mat @ Vector(c) for c in obj.bound_box]

        axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[self.axis]

        vals = [c[axis_idx] for c in corners]

        self.target_size = max(vals) - min(vals)

        return context.window_manager.invoke_props_dialog(self)





def register():

    bpy.utils.register_class(MEASURE_OT_BBoxScale)



def unregister():

    bpy.utils.unregister_class(MEASURE_OT_BBoxScale)

