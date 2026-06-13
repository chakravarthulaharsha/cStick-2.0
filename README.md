# cStick-2.0

cStick 2.0 is an **IoMT-edge based vision-enabled smart cane pipeline** for **personalized fall prediction**, **fall detection**, and **assistive safety monitoring**.
It integrates (1) embedded sensor logging, (2) vision-based obstacle detection, (3) DNN-based fall prediction, (4) adaptive edge/cloud workflows, and (5) app-based monitoring to compute and act on fall-risk using motion signals, vitals, pressure/grip information, distance, and GPS.

Unlike reactive fall-detection systems that mainly respond after a fall occurs, cStick 2.0 is designed to support proactive safety by continuously monitoring physiological, motion-related, pressure-based, environmental, and location-related signals.

---

## Key Features

* **Sensor data logging to CSV (SD card)** from multiple hardware modules
* **Arduino Uno-based sensing and response control**
* **Obstacle detection on Arduino Nicla Vision/OpenMV** with direction + distance estimation
* **DNN-based fall prediction** using six multimodal input features
* **Three-class decision output**

  * `0`: normal monitoring / no fall
  * `1`: warning / fall predicted
  * `2`: emergency / definite fall
* **Edge-side inference + actuation hooks**

  * buzzer
  * vibration
  * speaker/audio prompt
  * display alert
  * GPS-supported emergency notification
* **Adaptive edge + cloud personalization workflow**

  * user-specific data update
  * model refinement workflow
  * personalized package publishing placeholder
* **Application prototype**

  * login
  * add new log
  * import CSV
  * daily view
  * monthly analytics
  * statistics
  * fall analytics
  * emergency alert
  * caregiver email notification
* **Model evaluation**

  * DNN accuracy: `96.67%`
  * DNN ROC-AUC: `0.982`
  * obstacle detection speed: approximately `19–20 FPS`

---

## Repository Contents

### Embedded / Data Collection (C++)

* `DataCollection.cpp`
* `Datacollection1.cpp`

  Logs to `cStick.csv` on SD card with columns:
  `timestamp_ms,Distance_cm,Pressure_hPa,HRV_bpm,Sugar_raw,SpO2_pct,AccelMag_g,Latitude,Longitude`

  Hardware referenced in code:

  * Arduino Uno
  * SD module (SPI)
  * HC-SR04 ultrasonic sensor (distance)
  * BMP280 pressure/environmental sensor (I2C)
  * MAX3010x / MAX30102 sensor (HR/HRV + SpO2-related sensing, I2C)
  * MPU6050 accelerometer (I2C)
  * Analog glucose-related sensor input (A0)
  * GPS NEO-6M module (Serial)
  * Buzzer
  * Display module

> Note: SpO2 and glucose-related values in the prototype should be calibrated and validated using clinically appropriate sensing methods before any real-world medical deployment.

---

### Obstacle Detection (Arduino Nicla Vision / OpenMV)

* `Obstacle Detection.py`
* `obstacle_detection.py`

  Implements a grayscale QVGA obstacle-awareness pipeline:

  * Threshold-based blob detection
  * Block-width based distance estimation
  * Direction estimation using blob centroid
  * Direction labels:

    * `Left`
    * `Center`
    * `Right`
  * Logs obstacle updates when distance changes significantly
  * Flags `CRITICAL` when the obstacle is below the critical threshold
  * Prints obstacle summary + FPS every few seconds

  Distance estimate:

  `distance = (10.0 * 500) / block_width`

  In the paper notation:

  `Db = (Wc × Fc) / wb`

  where:

  * `Db` = estimated obstacle distance
  * `Wc` = calibration object-width constant
  * `Fc` = calibration focal constant
  * `wb` = detected block width in pixels

  Prototype constants:

  * `Wc = 10.0`
  * `Fc = 500`

  Warning logic:

  * `CRITICAL` if `Db < 50 mm`
  * `NORMAL` if `Db ≥ 50 mm`

  The broader one-meter region is used for obstacle awareness, while the smaller threshold is used for immediate critical obstacle classification.

  During testing, the obstacle detection module operated at approximately `19–20 FPS`.

> Note: The obstacle distance calculation is a lightweight prototype-level approximation. It is suitable for real-time embedded warning, but it is not as precise as LiDAR or depth-camera-based measurement.

---

### Fall Prediction (ML)

#### Training

* `DNN Fall Prediction.py`

  Trains a 3-class DNN on six input features:

  * `d`: obstacle distance
  * `p`: stick-pressure / grip-pressure level
  * `h`: heart rate variability (HRV)
  * `b`: blood sugar level
  * `s`: SpO2
  * `a`: accelerometer-based motion status

  Feature vector:

  `x = [d, p, h, b, s, a]`

  Output classes:

  * `0`: no fall / normal monitoring
  * `1`: fall predicted / warning
  * `2`: definite fall / emergency

  Model:

  * Dense(20, ReLU) → Dense(20, ReLU) → Dense(3, Softmax)

  Training:

  * Dataset size: `9,670 samples`
  * Training samples: `7,736`
  * Testing samples: `1,934`
  * Optimizer: `SGD`
  * Learning rate: `0.01`
  * Epochs: `200`
  * Batch size: `32`
  * Loss: `Categorical cross-entropy`

  Saves:

  * TensorFlow model: `cstick_dnn_tf/`
  * Scaler stats:

    * `scaler_mean.npy`
    * `scaler_scale.npy`

#### Inference + Decision + Actuation

* `FallPred.py`

  Loads the saved model + scaler, predicts the class, and triggers placeholder actuators:

  * buzzer
  * vibration
  * speaker/audio prompt
  * display alert
  * GPS-supported alert on emergency class

  Decision logic:

  * Class `0`: continue monitoring
  * Class `1`: generate warning alert
  * Class `2`: trigger emergency response

---

### Adaptive Edge + Cloud Personalization (Reference Workflow)

* `Edge.py`

* `Adaptive Edge.py`

  Edge loop that:

  * Logs sensor windows to `edge_logs.csv`
  * Predicts with a local model
  * Detects low-confidence or drift-like behavior
  * Calls a micro-adaptation placeholder
  * Performs periodic synchronization
  * Downloads personalized model packages as placeholders
  * Quantizes if needed
  * Activates updated packages in the workflow

* `Cloud.py`

  Cloud job that:

  * Ingests per-user logs
  * Updates model weights as a placeholder workflow
  * Derives user-specific personalization parameters
  * Assembles and publishes per-user model packages in:

  `published/<user>/model_pkg.bin`

  The personalization dataset is represented as:

  `Dp = D0 ∪ Du`

  where:

  * `D0` = original dataset
  * `Du` = new user-specific records
  * `Dp` = updated personalization dataset

  The model update is represented as:

  `θ' = θ − η∇θL(Dp; θ)`

  where:

  * `θ` = current DNN parameters
  * `θ'` = updated personalized DNN parameters
  * `η` = learning rate
  * `L(Dp; θ)` = loss on the updated personalization dataset

> These scripts are structured as a reference implementation. Replace placeholder parts such as encryption, upload/download, real training, validation, packaging, authentication, and secure caregiver access before deployment.

---

### Application Prototype

* `app/`

  The application prototype supports user-facing logging, visualization, analytics, and emergency communication.

  Main functions:

  * Login
  * Main menu
  * Add New Log
  * Import CSV
  * Daily View
  * Monthly Analytics
  * Edit Data
  * Statistics
  * Fall Analytics
  * Fall vs. No-Fall Metrics
  * Average Measurements
  * Decision Distribution
  * Emergency alert confirmation
  * Caregiver email alert

  Add New Log fields:

  * Distance
  * Pressure
  * Heart Rate Variability
  * Blood Sugar
  * SpO2
  * Accelerometer Status

> Note: In the application, the pressure field refers to stick-pressure or grip-pressure. It does not refer to clinical blood pressure.

---

## Model Evaluation

The fall prediction model was compared with SVM and Logistic Regression.

| Model               | Accuracy (%) | ROC-AUC | Remarks                                                                    |
| ------------------- | -----------: | ------: | -------------------------------------------------------------------------- |
| DNN                 |        96.67 |   0.982 | Best performance; supports nonlinear multi-sensor fall-risk classification |
| SVM                 |        92.14 |   0.937 | Strong baseline but less flexible for personalization                      |
| Logistic Regression |        91.02 |   0.921 | Lightweight and interpretable but weaker for nonlinear patterns            |

The DNN achieved the best performance because fall-risk conditions are usually nonlinear and depend on relationships among multiple signals. For example, sudden acceleration may not always indicate danger by itself, but when combined with abnormal SpO2, HRV, blood sugar variation, increased grip pressure, or nearby obstacle distance, it may indicate a higher-risk condition.

---

## Quick Start

### 1) Arduino / Embedded Logger (`DataCollection.cpp`)

1. Open `DataCollection.cpp` in Arduino IDE or PlatformIO.
2. Install libraries:

   * SD
   * Wire
   * Adafruit BMP280
   * SparkFun MAX3010x + heartRate helper
   * Adafruit MPU6050
   * TinyGPSPlus
3. Update pins and serial ports if needed:

   * `SD_CS_PIN`
   * `TRIG_PIN`
   * `ECHO_PIN`
   * `SUGAR_PIN`
   * `GPS_SERIAL`
   * GPS baud rate
4. Flash to the board.
5. Confirm that `cStick.csv` is created on the SD card.

---

### 2) DNN Training (Python)

Install dependencies:

```bash
pip install numpy pandas scikit-learn tensorflow
```

Run:

```bash
python "DNN Fall Prediction.py"
```

Expected outputs:

```text
cstick_dnn_tf/
scaler_mean.npy
scaler_scale.npy
```

---

### 3) Fall Prediction Inference

Run:

```bash
python FallPred.py
```

The script loads the trained model and scaler statistics, predicts the fall-risk class, and triggers the corresponding alert logic.

---

### 4) Obstacle Detection

For Arduino Nicla Vision / OpenMV, upload one of the following files:

```text
Obstacle Detection.py
```

or

```text
obstacle_detection.py
```

Monitor serial output for:

```text
Distance
Direction
Warning status
FPS
```

---

### 5) Edge Workflow

Run:

```bash
python Edge.py
```

or:

```bash
python "Adaptive Edge.py"
```

This starts the reference edge-side workflow for local prediction, logging, drift detection placeholder logic, synchronization, and personalized model activation placeholders.

---

### 6) Cloud Workflow

Run:

```bash
python Cloud.py
```

This simulates the reference cloud-side workflow for user-log ingestion, personalization, and model package publishing.

---

## Current Prototype Status

This repository contains a research prototype implementation of cStick 2.0.

Implemented or represented modules include:

* Embedded sensor collection
* Arduino Uno-based sensor handling
* Arduino Nicla Vision/OpenMV-based obstacle detection
* DNN-based fall prediction
* Edge-side inference workflow
* Adaptive personalization workflow
* Cloud reference workflow
* GPS-supported emergency response
* App-based log entry and analytics
* Caregiver alert workflow

Some components are implemented as placeholders and should be completed before real-world deployment.

---

## Limitations

The current prototype has the following limitations:

* SpO2 sensing requires clinical-grade calibration.
* Blood-sugar-related sensing requires clinical validation.
* Obstacle distance estimation is approximate.
* Vision-based obstacle detection may be affected by lighting changes.
* Adaptive personalization is implemented as a workflow and requires larger-scale validation.
* Arduino Uno does not perform full DNN training.
* Sensor noise may affect performance in uncontrolled environments.
* Battery and power optimization are still needed.
* Secure IoMT deployment requires authentication, encryption, and privacy protection.
* Larger testing with elderly users is required.
* The system is not a certified medical device.

---

## Future Work

Future improvements may include:

* Larger-scale validation with elderly participants
* More robust sensor fusion
* Improved obstacle detection under different lighting conditions
* Better energy optimization
* Secure caregiver communication
* Encrypted data transmission
* Authenticated caregiver access
* Improved adaptive personalization
* Blood pressure, temperature, and ECG-based health indicators
* Long-term testing in home-care, assisted-living, and clinical environments

---

## Research Context

cStick 2.0 demonstrates the feasibility of combining:

* IoMT sensing
* Edge processing
* Vision-enabled obstacle awareness
* DNN-based fall prediction
* Adaptive personalization
* Multimodal feedback
* GPS-supported emergency response
* Application-based monitoring

The system provides a foundation for future personalized, privacy-aware, and real-time elderly care technologies.

---

## Disclaimer

cStick 2.0 is a research prototype and is not a certified medical device. It should not be used as the sole system for medical diagnosis, emergency response, or fall prevention without additional clinical validation, hardware calibration, security testing, and regulatory approval.

---

## Citation

If you use this repository or build upon this work, please cite the related cStick 2.0 research paper:

```text
cStick 2.0: An IoMT-Edge Based Vision-Enabled Smart System for Personalized Fall Prediction and Detection
```
