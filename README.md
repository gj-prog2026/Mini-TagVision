# Mini-TagVision
 
A small, from-scratch version of an overhead robot-field vision system (like SSL-Vision / TagVision), built as a learning project.
 
The idea: **render** a fake overhead camera image where the true robot and ball positions are known, then write a vision pipeline that has to **recover** those positions from the pixels alone, and score it against the truth. Building both directions (world → pixels and pixels → world) covers every stage of the real system.
 
No camera needed. Everything is synthetic.
 
---
 
## Setup
 
Requires Python 3 with `numpy` and `opencv-python`.
 
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install numpy opencv-python
```
 
> Use `python -m pip` rather than bare `pip`. It guarantees packages install into the Python you are actually running (the venv), and avoids a broken `pip.exe` launcher.
 
## Running
 
From the project folder, with the venv active:
 
```powershell
python mini_tagvision.py
```
 
Output images are saved to `out/` (e.g. `out/part1.png`). Open them from VS Code's file explorer.
 
---
 
## Plan
 
| Part | Topic | What it builds | Real-system equivalent |
|---|---|---|---|
| 1 | Camera model | `project()`: world point (mm) → pixel; draw the field | `camera/` |
| 2 | Synthetic scene | Robots (team dot + heading dot) and ball, with saved ground truth | `synth/` |
| 3 | Detection | HSV thresholding, morphology, contours → blob centres, heading | `detect/` |
| 4 | Back-projection | `pixel_to_plane(u, v, h)`: pixel → field position at the right height | `pose/projection.py` |
| 5 | Calibration | Recover the camera pose from field corners with `solvePnP`; reprojection error | `calibration/` |
| 6 | Output and timing | Send detections over UDP multicast (`224.5.23.2:10006`); time each stage vs 16.7 ms | `output/`, `engine/` |
| 7 | Discussion prep | Explain the pipeline; real cameras; marker choices; performance; team split | n/a |
 
## Progress
 
- [x] Environment set up (venv, numpy, opencv-python)
- [x] Part 1: camera intrinsics `K`, pose `R` and `t`, `project()`, field outline drawn
- [ ] Part 1: centre line
- [ ] Parts 2–7
---
 
## Notes: Part 1 (camera model)
 
### Setup values
- Image: 1280 × 720 px
- Field: 4000 × 2000 mm, centred on the world origin, at z = 0
- Camera: 3000 mm above the field centre, looking straight down
- All distances in **millimetres**
### Intrinsics: `K`
```
[ fx  0  cx ]     fx = fy = 800   focal length in pixels (how zoomed in)
[  0 fy  cy ]     cx, cy = 640, 360   principal point (image centre)
[  0  0   1 ]
```
`K` describes the camera itself, not where it is. It converts camera coordinates into pixels.
 
### Extrinsics: `R` and `t` (the camera pose)
- **`rvec = [π, 0, 0]`**: axis-angle rotation. Direction = axis (x), length = angle (π rad = 180°).
- **`R = cv2.Rodrigues(rvec)`**: the same rotation as a 3×3 matrix. A 180° turn about x keeps x and flips y and z:
```
[ 1  0  0 ]
[ 0 -1  0 ]
[ 0  0 -1 ]
```
  This turns the camera from facing up to facing down, so field points have **positive depth** (in front of the lens). Without it the field would be behind the camera.
- **`t = -R @ CAM_POS`**: the shift. The camera must sit at the origin of its own coordinates, so `R · CAM_POS + t = 0` → `t = −R · CAM_POS` = (0, 0, 3000), meaning "the field centre is 3 m in front of the camera".
### `project()`: world → pixel in three moves
1. **World → camera:** `X_cam = R · X_world + t` (in code `Xw @ R.T + t`, because points are stored as rows)
2. **Perspective divide:** divide x and y by depth Z. Further away = smaller.
3. **Apply K:** multiply by the focal length, add the principal point.
Worked example: corner (2000, 1000, 0) → camera (2000, −1000, 3000) → ratios (0.667, −0.333) → pixel ≈ (1173, 93), top right.
 
### Python / NumPy notes
- `@` is matrix multiplication; `*` is element-wise. Mixing them up gives wrong numbers silently.
- `Xc[:, 2]` = column 2 of every row (all depths).
- OpenCV drawing needs whole-pixel `int32` points: `np.round(pts).astype(np.int32)`.
- `cv2.polylines(img, [pts], isClosed, colour, thickness)` takes a **list** of shapes; colours are **BGR**.
- List polygon corners in order around the edge, or the outline becomes a bow-tie.
 