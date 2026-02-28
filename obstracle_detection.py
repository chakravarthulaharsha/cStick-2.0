import sensor, image, time

# Constants
DISTANCE_THRESHOLD = 10.0  # Minimum change in distance (mm) to log
LOG_INTERVAL = 2.0  # Time interval for logging summary (seconds)
CRITICAL_DISTANCE = 50.0  # Highlight obstacles closer than this (mm)

# Variables
last_logged_obstacles = {}
last_log_time = 0

# Initialize camera
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)  # Disable Auto Gain
sensor.set_auto_whitebal(False)  # Disable Auto White Balance
clock = time.clock()

print("Camera ready. Starting obstacle detection...")

try:
    while True:
        clock.tick()
        img = sensor.snapshot()
        blobs = img.find_blobs([(120, 255)], pixels_threshold=100, area_threshold=100, merge=True)

        current_obstacles = {}
        for blob in blobs:
            # Calculate distance
            distance = (10.0 * 500) / blob.w()  # Adjust based on your setup
            # Determine direction
            direction = (
                "Left" if blob.cx() < img.width() // 3 else
                "Right" if blob.cx() > 2 * img.width() // 3 else
                "Center"
            )
            # Store obstacle data
            if direction not in current_obstacles or abs(current_obstacles[direction] - distance) > DISTANCE_THRESHOLD:
                current_obstacles[direction] = distance

        # Log significant changes
        for direction, distance in current_obstacles.items():
            if (
                direction not in last_logged_obstacles
                or abs(last_logged_obstacles[direction] - distance) > DISTANCE_THRESHOLD
            ):
                status = "CRITICAL" if distance < CRITICAL_DISTANCE else "Normal"
                print(f"[{status}] Obstacle detected: {distance:.2f} mm away, Direction: {direction}")
                last_logged_obstacles[direction] = distance

        # Periodic summary
        current_time = time.ticks_ms()
        if current_time - last_log_time > LOG_INTERVAL * 1000:
            print("\n--- Obstacle Summary ---")
            for direction, distance in sorted(current_obstacles.items(), key=lambda x: x[1]):
                status = "CRITICAL" if distance < CRITICAL_DISTANCE else "Normal"
                print(f"{direction}: {distance:.2f} mm ({status})")
            print("------------------------\n")
            last_log_time = current_time

        # FPS log
        print(f"FPS: {clock.fps():.2f}")

except Exception as e:
    print(f"Error: {e}")
