# Ugur Tools - Blender 3D Printing Toolkit

A comprehensive Blender addon designed to simplify common 3D printing workflows. This toolkit brings together essential measurement, drawing, alignment, and analysis tools into a single, easy-to-use sidebar panel.

**Author:** Ugur Bozkan
**Version:** 2.13.0
**Blender:** 5.0+
**License:** GPL-3.0

> **Note:** This addon was developed and tested with Blender 5.0. It has not been tested with older versions.

---

## Features

### Measurement Tools
- **Tape Measure** - Place persistent measurement points that stay attached to objects even when they move. Measurements are saved with your .blend file.
- **Line Measure** - Chain multiple measurement segments together to measure complex paths. Displays individual and total distances.
- **BBox Measure** - Instantly see the bounding box dimensions (X, Y, Z) of any selected mesh object with an on-screen overlay.

### Guide System
- **Guide Lines** - Create offset guide lines from any mesh edge, similar to construction lines in CAD software. Supports numeric distance input and editing of existing guides.

### Drawing & Modeling
- **Draw Tool** - A knife-like tool for Edit Mode that lets you draw edges directly on mesh surfaces with full snap support (vertex, midpoint, edge, face). Includes axis locking (X/Y/Z) and numeric distance input for precise modeling.

### Scaling & Alignment
- **BBox Scale** - Scale objects to exact real-world dimensions along any axis based on their bounding box size.
- **Axis Align** - Align multiple selected objects along X, Y, or Z axis.
- **Distribute** - Evenly distribute 3+ objects along any axis with equal spacing.
- **Face Align** - Align one object to another by clicking on their faces.

### Analysis
- **Face Area** - Display the area of selected faces in Edit Mode with proper unit conversion.
- **Wall Thickness Check** - Analyze minimum wall thickness of your model for 3D printing validation.

### Rotation Helpers
- **Quick Rotate** - Rotate objects by custom angles with per-axis direction toggle (CW/CCW).

### Unit System
- Full support for Blender's unit system (Metric: mm, cm, m / Imperial: inches, feet)
- All measurements automatically display in the active scene unit

---

## Installation

1. Download the latest release (`.zip` file) from the [Releases](../../releases) page.
2. Open Blender 5.0+
3. Go to **Edit > Preferences > Add-ons**
4. Click **Install** and select the downloaded `.zip` file
5. Enable the addon by checking the box next to "Ugur Tools"

The tools will appear in the **3D Viewport Sidebar** (press `N`) under the **Ugur Tools** tab.

---

## Usage

### Measure Tab
Access measurement tools from the sidebar. Toggle visibility of all measurements with the eye icon. Clear all measurements with the trash icon.

### Draw Tool
1. Enter **Edit Mode** on a mesh object
2. Activate the Draw Tool from the sidebar
3. **Left click** to place points - edges are created between consecutive points
4. Press **X**, **Y**, or **Z** to lock to an axis
5. Type a number + **Enter** to specify an exact distance
6. **Right click** to end the current chain, **ESC** to exit

### Guide Lines
1. Hover over a mesh edge and **left click** to select it
2. Move the mouse to set the offset direction and distance
3. Type a number + **Enter** for precise offset distance
4. Click to place the guide line
5. Click on an existing guide to edit its distance

---

## File Structure

```
blender tools/
├── __init__.py        # Main addon file (panels, operators, registration)
├── snap_utils.py      # Vertex/edge/midpoint/face snap system
├── tape_measure.py    # Persistent tape measure tool
├── line_measure.py    # Multi-segment line measure
├── bbox_measure.py    # Bounding box dimension overlay
├── bbox_scale.py      # Scale to exact dimensions
├── guide_measure.py   # Construction guide lines
└── draw_tool.py       # Edit mode drawing/knife tool
```

---

## Why This Addon?

When working with 3D printers, you often need to:
- Measure exact dimensions of parts
- Scale models to precise real-world sizes
- Align and distribute objects for plate layout
- Draw precise cuts and geometry on existing meshes
- Verify wall thickness for printability

These tasks usually require switching between multiple tools or addons. **Ugur Tools** brings them all together in one place, making the 3D printing workflow in Blender faster and more intuitive.

---

## Contributing

Contributions, bug reports, and feature requests are welcome! Feel free to open an issue or submit a pull request.

---

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
