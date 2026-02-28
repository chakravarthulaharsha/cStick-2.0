# Nicla Vision (OpenMV) - Algorithm 1
# Obstacle Detection + Distance + Direction Estimation
#
# Matches paper steps:
# - grayscale, QVGA
# - disable auto gain / white balance
# - detect blocks using intensity threshold 120-255 + area constraints
# - distance = (10.0 * 500) / block_width
# - direction from centroid (left/center/right thirds)
# - update log if distance changes > 10 mm
# - CRITICAL if distance < 50 mm
# - every 2s: print summary + FPS

import sensor, image, time

# --------------------
# Step 1: Initialize camera sensor
# --------------------
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)          # grayscale
sensor.set_framesize(sensor.QVGA)               # 320x240
sensor.skip_frames(time=2000)                   # stabilize
sensor.set_auto_gain(False)                     # disable auto-gain
sensor.set_auto_whitebal(False)                 # disable auto white balance

clock = time.clock()

# Tunable constraints (paper says "minimum pixel count and area constraints")
MIN_PIXELS = 200
MIN_AREA = 200
THRESH = (120, 255)  # pixel intensity threshold

# Obstacle record store: key -> last_distance_mm
# key can be (direction, approx_xbin) or block id surrogate
obstacle_log = {}

# Periodic reporting
last_report_ms = time.ticks_ms()
REPORT_EVERY_MS = 2000

def direction_from_centroid(cx, img_w):
    third = img_w // 3
    if cx < third:
        return "Left"
    if cx > 2 * third:
        return "Right"
    return "Center"

def compute_distance_mm(block_w):
    # From paper: distance = (10.0 * 500) / block_width
    # NOTE: This is a calibrated heuristic; block_width must be non-zero.
    if block_w <= 0:
        return None
    return (10.0 * 500.0) / float(block_w)

# --------------------
# Step 2: Start main loop
# --------------------
while True:
    clock.tick()

    # Capture snapshot
    img = sensor.snapshot()

    # Detect blocks: use blobs on thresholded brightness
    # threshold is for GRAYSCALE: (low, high)
    blobs = img.find_blobs([THRESH],
                           pixels_threshold=MIN_PIXELS,
                           area_threshold=MIN_AREA,
                           merge=True)

    current_obstacles = []

    # For each detected block
    for b in blobs:
        cx = b.cx()
        cy = b.cy()
        bw = b.w()

        dist_mm = compute_distance_mm(bw)
        if dist_mm is None:
            continue

        direction = direction_from_centroid(cx, img.width())

        # Create a stable-ish key (bin by x-position + direction)
        xbin = int((cx / img.width()) * 10)  # 0..9
        key = (direction, xbin)

        # Update obstacle record if distance changes > 10mm
        prev = obstacle_log.get(key, None)
        if (prev is None) or (abs(dist_mm - prev) > 10.0):
            obstacle_log[key] = dist_mm

        # Print obstacle info (CRITICAL if distance < 50mm)
        level = "CRITICAL" if dist_mm < 50.0 else "Normal"
        print("[{}] dir={} dist_mm={:.1f} cx={} cy={} w={}".format(
            level, direction, dist_mm, cx, cy, bw
        ))

        current_obstacles.append((level, direction, dist_mm, cx, cy, bw))

        # Optional: visualize bounding box (helpful during dev)
        img.draw_rectangle(b.rect(), color=255)
        img.draw_cross(cx, cy, color=255)

    # Periodic update every 2 seconds: summary + FPS
    now = time.ticks_ms()
    if time.ticks_diff(now, last_report_ms) >= REPORT_EVERY_MS:
        last_report_ms = now

        print("----- SUMMARY (last 2s) -----")
        if len(obstacle_log) == 0:
            print("No obstacles logged.")
        else:
            # Print all tracked obstacles
            for k, dmm in obstacle_log.items():
                print("Obstacle {} -> {:.1f} mm".format(k, dmm))

        print("FPS: {:.2f}".format(clock.fps()))
        print("----------------------------")