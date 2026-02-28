# cStick-2.0

cStick 2.0 is a multi-sensor smart cane pipeline for **fall-risk prediction** and **assistive safety monitoring**.  
It integrates (1) embedded sensor logging, (2) obstacle detection, and (3) edge/cloud ML workflows to compute and act on fall-risk using IMU + vitals + distance + GPS.

---

## Key Features
- **Sensor data logging to CSV (SD card)** from multiple hardware modules
- **Obstacle detection on Nicla Vision/OpenMV** with direction + distance estimation
- **DNN-based fall prediction** (training + saved model artifacts)
- **Edge-side inference + actuation hooks** (buzzer/vibration/speaker/GPS alert)
- **Adaptive edge + cloud workflow** (weekly sync, personalization seed, publish updates)

---

## Repository Contents
### Embedded / Data Collection (C++)
- `DataCollection.cpp`  
  Logs to `cStick.csv` on SD card with columns:  
  `timestamp_ms,Distance_cm,Pressure_hPa,HRV_bpm,Sugar_raw,SpO2_pct,AccelMag_g,Latitude,Longitude`

  Hardware referenced in code:
  - SD module (SPI)
  - HC-SR04 ultrasonic (distance)
  - BMP280 (pressure, I2C)
  - MAX3010x (HR/HRV + placeholder SpO2, I2C)
  - MPU6050 (accelerometer, I2C)
  - Analog glucose sensor (A0)
  - GPS NEO-6M (Serial)

> Note: SpO2 is a placeholder in the logger and should be replaced with a proper MAX30102 SpO2 algorithm or library.

---

### Obstacle Detection (Nicla Vision / OpenMV)
- `Obstacle Detection.py`  
  Implements a grayscale QVGA pipeline:
  - Threshold-based blob detection
  - **Distance estimate** via calibrated heuristic: `distance = (10.0 * 500) / block_width`
  - **Direction** (Left / Center / Right) from blob centroid
  - Logs obstacle updates when distance changes > 10 mm
  - Flags **CRITICAL** when distance < 50 mm
  - Prints summary + FPS every 2 seconds

---

### Fall Prediction (ML)
#### Training
- `DNN Fall Prediction.py`  
  Trains a 3-class DNN on **6 input features**:
  - `a, g, hrv, bs, sp, d`
  Output classes:
  - `0`: normal monitoring
  - `1`: warning
  - `2`: emergency / fall

  Model:
  - Dense(20, ReLU) → Dense(20, ReLU) → Dense(3, Softmax)
  Training:
  - Optimizer: SGD
  - Epochs: 200
  - Batch size: 32

  Saves:
  - TensorFlow model: `cstick_dnn_tf/`
  - Scaler stats: `scaler_mean.npy`, `scaler_scale.npy`

#### Inference + Decision + Actuation
- `FallPred.py`  
  Loads the saved model + scaler, predicts the class, and triggers placeholder actuators:
  - buzzer, vibration, speaker prompt
  - GPS alert on emergency (class 2)

---

### Adaptive Edge + Cloud Personalization (Reference Workflow)
- `Edge.py` / `Adaptive Edge.py`  
  Edge loop that:
  - Logs windows to `edge_logs.csv`
  - Predicts with a local model
  - Detects low-confidence “drift” and calls a micro-adapt placeholder
  - Performs a **weekly sync** (compress + encrypt placeholder + upload)
  - Downloads personalized model packages (placeholder), quantizes if needed, and activates them

- `Cloud.py`  
  Cloud job that:
  - Ingests per-user logs
  - Trains/updates global weights version `Θ'` (placeholder training)
  - Derives per-user seed `ϕu` from user data (example: mean HRV)
  - Assembles and publishes per-user model packages in `published/<user>/model_pkg.bin`

> These scripts are structured as a clear reference implementation. Replace placeholder parts (encryption, upload/download, real training, packaging) for deployment.

---

## Quick Start

### 1) Arduino / Embedded Logger (DataCollection.cpp)
1. Open `DataCollection.cpp` in Arduino IDE (or PlatformIO).
2. Install libraries (typical):
   - SD
   - Wire
   - Adafruit BMP280
   - SparkFun MAX3010x + heartRate helper
   - Adafruit MPU6050
   - TinyGPSPlus
3. Update pins and serial ports if needed:
   - `SD_CS_PIN`, `TRIG_PIN`, `ECHO_PIN`, `SUGAR_PIN`
   - `GPS_SERIAL` and baud
4. Flash to board and confirm `cStick.csv` is created on SD card.

### 2) DNN Training (Python)
```bash
pip install numpy pandas scikit-learn tensorflow
python "DNN Fall Prediction.py"
