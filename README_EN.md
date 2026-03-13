# Ugur Tools - Blender Addon



A comprehensive Blender addon designed to simplify 3D printing workflows with professional-grade measurement, alignment, boolean operations, and modeling tools.



**Author:** Ugur Bozkan

**Version:** 2.13.0

**Blender Version:** 5.0+

**License:** GPL-3.0



## Overview



Ugur Tools is a feature-rich addon that extends Blender's native capabilities with specialized tools for precision modeling and 3D printing preparation. Built with streamlined workflows in mind, it provides intuitive access to advanced measurement, alignment, boolean operations, and editing tools through an organized sidebar interface.



## Installation



1. Download the addon files from the repository

2. In Blender, go to **Edit > Preferences > Add-ons**

3. Click **Install...** and select the addon folder or .zip file

4. Search for "Ugur Tools" and enable the checkbox

5. The addon will appear in **View3D > Sidebar > Ugur Tools**



## Quick Start



Once installed, open the **N-Panel** (Sidebar) in the 3D Viewport and look for the "Ugur Tools" tab group. The tools are organized into five main categories:



- **Tools** - Measurements and object manipulation

- **Align** - Alignment and distribution tools

- **Boolean** - Boolean operations and hole drilling

- **Cursor** - 3D cursor positioning tools

- **Draw** - Edit mode drawing and modeling



## Features



### Tools Tab



#### Measurements and Display



- **Show/Hide Measurements Toggle** - Quickly toggle visibility of all measurement overlays in the viewport

- **Unit Selector** - Choose between metric (mm, cm, m) and imperial (inches, feet) units. Selected unit applies to all measurement tools

- **Object Dimensions Display** - Real-time display of selected object's X, Y, Z dimensions

- **Full Blender Unit System Support** - Seamlessly integrates with Blender's native unit settings



#### Measurement Tools



- **Tape Measure** - Create persistent measurement lines. Measurements are saved with your .blend file for future reference

- **Line Measure** - Multi-segment line measurement tool for complex distances

- **Guide Line** - Construction guide lines for precise modeling reference

- **BBox Overlay** - Real-time bounding box dimension overlay displayed in the viewport



#### Rotation Tools



- **Manual Angle Input** - Enter precise rotation angles in degrees

- **Direction Toggle** - Switch between clockwise (CW) and counterclockwise (CCW) rotation

- **Quick Rotate Buttons** - One-click 45° and 90° rotation in the current direction

- **Smart Rotation** - Rotates selected objects around their pivot point or the 3D cursor



### Align Tab



#### Basic Alignment



- **Mirror** - Mirror selected objects along the X, Y, or Z axis

- **Align to Active** - Align selected objects to the active object's position (X, Y, or Z axis)

- **Distribute Evenly** - Distribute 3 or more selected objects with equal spacing along any axis



#### Advanced Alignment



- **Face Alignment** - Click two faces (one on each object) to automatically align objects along the determined axis

- **Align Face to Axis** - Click a face to align its normal vector to the X, Y, or Z axis

- **Ground Tool** - Position objects on the ground plane (Z=0)

  - **Drop to Ground** - Move object down until it touches Z=0

  - **Lay Flat** - Click a face, then rotate the object so that face points downward and drop to ground



#### Vertex-Based Positioning



- **Point Align** - Select two vertices (source and target) to translate an object from one vertex position to another



### Boolean Tab



#### Boolean Operations



- **Subtract (Difference)** - Remove selected object from active object

- **Union** - Combine selected objects into one

- **Advanced Boolean Modifier Management** - Seamless modifier application and cleanup



#### Hole Drilling



The hole drilling tool is optimized for 3D printing workflows and provides multiple drilling modes:



- **Standard Hole Drilling** - Click on any surface to drill a perfectly cylindrical hole

- **Drill at 3D Cursor** - Drill at the current 3D cursor position without needing to click

- **Drill Selected Objects** - Drill through multiple selected meshes simultaneously (bullet-through effect)



#### Drilling Configuration



- **Diameter** - Set hole diameter in current units

- **Depth** - Control how deep the hole cuts into the object

- **Segments** - Adjust cylinder smoothness:

  - 4 segments = Square hole

  - 6 segments = Hexagon hole

  - 32 segments = Smooth circular hole (default)

  - Custom values supported for special requirements



### Cursor Tab



#### Cursor Positioning



- **Edit Mode Cursor Positioning** - Place cursor at the center of your selection

  - Selected face center - cursor moves to the geometric center of the face

  - Selected vertices center - cursor moves to the center point of all selected vertices

- **Object Mode Cursor Positioning** - Click any face in the viewport to place the cursor at its center

- **Guide Intersection** - Automatically move cursor to the intersection point of the last two guide lines



#### Use Cases



- Precise pivot point setup for rotations and transformations

- Quick reference point placement for alignments

- Drilling reference points for boolean operations



### Draw Tab



#### Edit Mode Drawing Tool



A powerful SketchUp-style drawing tool that integrates seamlessly with Blender's edit mode:



- **Continuous Edge Drawing** - Draw connected edges by clicking points in the viewport

- **Smart Snap System** - Automatic snapping to nearest geometry with priority system:

  - Vertex snap (highest priority)

  - Midpoint snap

  - Edge snap

  - Face snap (lowest priority)

- **Axis Locking** - Press X, Y, or Z to constrain drawing to a specific axis

- **Numeric Distance Input** - Enter exact distances while drawing for precision modeling

- **Intelligent Face Splitting** - Automatically splits faces when drawing intersects them

- **Edge Splitting** - Supports knife-cut logic with edge division

- **Cycle Detection** - Prevents invalid topology and self-intersecting geometry



#### Workflow



1. Enter Edit Mode

2. Activate the Draw tool from the Draw tab

3. Click points in the viewport to create edges

4. Use axis locks (X/Y/Z keys) for constrained drawing

5. Type numbers to input exact distances

6. Press Enter to confirm or Escape to cancel



## Unit System Support



Ugur Tools fully supports Blender's unit system:



- **Metric Units:** Millimeters (mm), Centimeters (cm), Meters (m)

- **Imperial Units:** Inches (in), Feet (ft)

- **Unit Conversion:** Automatic conversion between selected units

- **Display Precision:** Measurements display with appropriate decimal places based on unit size



All measurements, dimensions, and drilling parameters respect the selected unit system.



## Snap System



The addon includes an intelligent snap system that prioritizes geometry for precise modeling:



**Priority Order:**

1. Vertex snapping - snaps to exact vertex positions

2. Midpoint snapping - snaps to edge midpoints

3. Edge snapping - snaps to edges

4. Face snapping - snaps to face surfaces



**Supported Snap Targets:**

- Vertices (all edit mode geometry)

- Midpoints (between vertices)

- Edges (edge centers and lines)

- Face surfaces (any face in the scene)



## File Structure



```

blender_tools/

├── __init__.py           # Main addon file with UI panels and operator registration

├── snap_utils.py         # Vertex, edge, midpoint, and face snap system

├── tape_measure.py       # Persistent tape measure tool with saved measurements

├── line_measure.py       # Multi-segment line measurement functionality

├── bbox_measure.py       # Bounding box dimension overlay and visualization

├── bbox_scale.py         # Scale objects to exact dimensional specifications

├── guide_measure.py      # Construction guide lines for precise reference

└── draw_tool.py          # Edit mode drawing and knife tool with snap support

```



## Common Workflows



### 3D Printing Preparation



1. **Import Model** - Load your 3D model into Blender

2. **Measure** - Use Tape Measure or BBox Overlay to verify dimensions

3. **Align** - Use Ground tool to position model correctly for printing

4. **Boolean Operations** - Add support structures or drill mounting holes using Boolean tab

5. **Export** - Export as STL or other 3D printing format



### Precise Object Alignment



1. Select objects to align

2. Click on Align tab

3. For simple alignment: click "Align X/Y/Z" (after setting active object)

4. For complex alignment: use Face Alignment to click on corresponding faces

5. Objects snap to active object's position



### Creating Mounting Holes



1. Select the object to modify

2. Go to Boolean tab

3. Click on surface where hole should be, or position 3D Cursor

4. Set desired hole diameter and depth

5. Click "Drill" button

6. Adjust segments for circle vs. polygon shape



### Distributing Multiple Objects



1. Select 3 or more objects (at least 3 required)

2. Go to Align tab

3. Click "Distribute Evenly"

4. Select axis (X, Y, or Z)

5. Objects distribute with equal spacing along selected axis



## Keyboard Shortcuts and Controls



### Draw Tool

- **X, Y, Z Keys** - Lock drawing to specific axis

- **Number Keys** - Input exact distance values

- **Enter** - Confirm drawing

- **Escape** - Cancel operation

- **Mouse Click** - Place vertex/snap point



### Measurement Tools

- **Click** - Place measurement point

- **Shift + Click** - Add additional measurement points (Line Measure)

- **Escape** - Cancel measurement



### Alignment Tools

- **Click** - Select face or vertex for alignment operation

- **Escape** - Cancel selection



## Advanced Features



### Persistent Measurements



Tape measurements created in your scene are automatically saved with your .blend file. When you reopen the file, your measurements remain in place, enabling non-destructive documentation of your model dimensions.



### Smart Face Detection



All tools that work with faces (drilling, cursor positioning, face alignment) include intelligent face detection that prioritizes visible, front-facing geometry in your viewport.



### Modifier Management



Boolean operations automatically manage modifiers:

- Creates appropriate modifier types for the operation

- Optionally applies modifiers for final geometry

- Preserves non-destructive workflow options



## System Requirements



- **Blender:** Version 5.0 or later

- **Operating System:** Windows, macOS, or Linux

- **RAM:** 2GB minimum (4GB+ recommended)

- **Graphics:** Any GPU with Blender support



## Compatibility Notes



- **Developed and tested with:** Blender 5.0

- **Not tested with:** Blender versions prior to 5.0

- **Known Limitations:** Some features may not work in older Blender versions due to API changes



If you encounter issues with other Blender versions, please report them with your specific version number.



## Tips and Best Practices



### Measurement Best Practices



- Use consistent units throughout your project to avoid confusion

- Keep unit settings matched to your export format requirements (mm for 3D printing is standard)

- Use Guide Lines as visual references rather than relying on tape measure overlays during modeling



### Alignment Best Practices



- Always set the desired target object as "Active" (highlighted in orange) before aligning

- Use Face Alignment for organic shapes where axis-aligned placement isn't appropriate

- Use Distribute Evenly with caution when objects have non-uniform scales



### Boolean Best Practices



- Apply modifiers only after finalizing all boolean operations

- For 3D printing, ensure all objects are manifold (watertight) before export

- Use larger segment counts for smooth holes in visible areas

- Test print small sections first when using complex boolean operations



### Draw Tool Best Practices



- Work with clean topology when possible

- Use axis locks (X/Y/Z) to maintain clean edge orientation

- Input numeric distances for precision rather than clicking freely

- Start with simple shapes and build complexity gradually



## Troubleshooting



### Tools Don't Appear in Sidebar



- Ensure addon is enabled in Preferences > Add-ons

- Check that you're in a 3D Viewport (not other workspace types)

- Toggle the N-Panel visibility (press N key)



### Snapping Not Working as Expected



- Verify you're in Edit Mode (for vertex/edge snapping)

- Check that snap objects are visible in the viewport

- Ensure you're hovering over valid geometry



### Boolean Operations Failing



- Verify both objects have valid manifold topology

- Check that objects don't have inverted normals

- Try rotating object 90 degrees if drilling seems off-axis

- Ensure sufficient segment count for the desired hole shape



### Measurements Not Saving



- Save your .blend file explicitly (File > Save)

- Auto-save should preserve measurements if enabled



## Contributing and Feedback



For bug reports, feature requests, or contributions, please submit them to the project repository with:

- Detailed description of the issue or request

- Steps to reproduce (if applicable)

- Blender version and operating system

- Screenshots or video demonstrations when helpful



## License



Ugur Tools is released under the GPL-3.0 License. See LICENSE file for details.



---



**Version History:**

- **2.13.0** - Current stable release

- Built for Blender 5.0+

- Optimized for 3D printing workflows



For updates and additional information, refer to the project repository or author's documentation.

