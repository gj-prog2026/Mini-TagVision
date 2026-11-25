# Part 1 - camera model
import os
import numpy as np
import cv2

os.makedirs("out", exist_ok=True)

W, H = 1280, 720
# this is the intrinsic matrix
K = np.array([[800, 0, 640],
              [0, 800, 360],
              [0,   0,   1]], dtype=float)

# actual length and width of the field in mm
# value here is 4m x 2m given by prev repo on field size 
FIELD_L, FIELD_W = 4000, 2000 
CAM_POS = np.array([0, 0, 3000.0]) 

# Pose: make the camera point down
# as the initial orientation of camera has it pointing upwards
rvec = np.array([np.pi, 0, 0])
R, _ = cv2.Rodrigues(rvec)
# t = translation part of camera pose
# X_cam = R.X_world + t
t = -R @ CAM_POS

def project(Xw):
    """Xw: (N,3) world points in mm -> (N,2) pixel coords."""
    # world -> camera coords
    Xc = Xw @ R.T + t

    # divide by Z
    x = Xc[:, 0] / Xc[:, 2]
    y = Xc[:, 1] / Xc[:, 2]

    # apply K
    u = K[0, 0] * x + K[0, 2]
    v = K[1, 1] * y + K[1, 2]

    return np.stack([u, v], axis=1)


# draw the field
img = np.zeros((H, W, 3), np.uint8)
# BGR green
img[:] = (40, 120, 40) 

# order has to go 1 -> 2 -> 4 -> 3 
# 4 is lower right corner (odd on left, even on right)
corners = np.array([(-FIELD_L/2, FIELD_W/2, 0), 
                    (FIELD_L/2, FIELD_W/2, 0),
                    (FIELD_L/2, -FIELD_W/2, 0),
                    (-FIELD_L/2, -FIELD_W/2, 0)])

corners_px = project(corners)

cv2.polylines(img, [np.round(corners_px).astype(np.int32)], 
              True, (255, 255, 255), 2)

cv2.imwrite("out/part1.png", img)