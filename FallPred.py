# Algorithm 2 (Inference + Decision + Actuation)
# This is "edge-side" logic in Python form.
# On Arduino, you'd implement the same state machine around a TFLite model.

import numpy as np
import tensorflow as tf

# Load model + scaler stats (from training above)
model = tf.keras.models.load_model("cstick_dnn_tf")
mean = np.load("scaler_mean.npy")
scale = np.load("scaler_scale.npy")

def normalize(x6):
    x = (x6 - mean) / scale
    return x.astype(np.float32)

# --- Actuator placeholders (replace with real hardware code) ---
def buzzer_on(): print("BUZZER: ON")
def buzzer_off(): print("BUZZER: OFF")
def vibrate_on(): print("VIBRATION: ON")
def speak(msg): print("SPEAKER:", msg)
def send_gps_alert(lat, lon): print("GPS ALERT:", lat, lon)

def get_latest_sensor_window():
    """
    Replace with real sensor reads from:
    Accelerometer (a), Gyroscope (g), HRV, Blood Sugar, SpO2, Distance (d)
    Returns a 6-dim feature vector in the same scale/units as training.
    """
    # dummy example
    a = 0.12
    g = 0.05
    hrv = 72.0
    bs = 96.0
    sp = 98.0
    d = 150.0
    return np.array([a, g, hrv, bs, sp, d], dtype=np.float32)

def get_gps_coords():
    # Replace with GPS module read
    return (33.214, -97.132)  # dummy (Denton-ish)

def predict_class(x6):
    x = normalize(x6)[None, :]  # (1,6)
    probs = model.predict(x, verbose=0)[0]
    yhat = int(np.argmax(probs))
    conf = float(np.max(probs))
    return yhat, conf, probs

# Main loop (pseudo)
while True:
    x6 = get_latest_sensor_window()
    yhat, conf, probs = predict_class(x6)

    # Paper rule:
    # 0 -> continue monitoring
    # 1 -> warning
    # 2 -> emergency response + GPS
    if yhat == 0:
        buzzer_off()
        # keep monitoring
    elif yhat == 1:
        speak("Take a break, you might trip.")
        vibrate_on()
    elif yhat == 2:
        speak("Emergency: fall detected.")
        buzzer_on()
        vibrate_on()
        lat, lon = get_gps_coords()
        send_gps_alert(lat, lon)

    # Put your sampling delay here
    # time.sleep(0.2)
    break  # remove in real deployment