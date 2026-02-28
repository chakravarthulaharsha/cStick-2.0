/*
  Writes SD:/cStick.csv with the SAME columns as your dataset:

  Distance,Pressure,HRV,Sugar level,SpO2,Accelerometer,Decision

  - Distance: HC-SR04 (cm)
  - Pressure: BMP280 (hPa)
  - HRV: MAX3010x (BPM estimate)  [your dataset uses HRV column; we log BPM]
  - Sugar level: analogRead(A0) (raw) -> rename/conversion if you have mg/dL calibration
  - SpO2: placeholder (-1) unless you plug your SpO2 algorithm/library
  - Accelerometer: magnitude in g from MPU6050
  - Decision: -1 by default. Set it from your model/rules (0,1,2)

  File behavior: APPEND by default (keeps old data).
  If you want OVERWRITE each boot, see initSD() section.
*/

#include <Wire.h>
#include <SPI.h>
#include <SD.h>

#include <Adafruit_BMP280.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

#include <MAX30105.h>
#include "heartRate.h"

// ================== PIN CONFIG ==================
static const int SD_CS_PIN = 10;
static const int TRIG_PIN  = 7;
static const int ECHO_PIN  = 6;
static const int SUGAR_PIN = A0;

// ================== GLOBALS ==================
File logFile;

Adafruit_BMP280 bmp;
Adafruit_MPU6050 mpu;
MAX30105 particleSensor;

unsigned long lastSampleMs = 0;
const unsigned long SAMPLE_PERIOD_MS = 500; // logging rate

float lastBPM = 0.0;
unsigned long lastBeatMs = 0;

// ================== SD INIT ==================
bool initSD_append() {
  if (!SD.begin(SD_CS_PIN)) {
    Serial.println("ERROR: SD init failed.");
    return false;
  }

  logFile = SD.open("cStick.csv", FILE_WRITE);
  if (!logFile) {
    Serial.println("ERROR: Cannot open cStick.csv");
    return false;
  }

  // If empty, write EXACT header like your dataset
  if (logFile.size() == 0) {
    logFile.println("Distance,Pressure,HRV,Sugar level,SpO2,Accelerometer,Decision");
    logFile.flush();
  }

  Serial.println("SD OK. Logging to cStick.csv (append mode).");
  return true;
}

/*
// If you want OVERWRITE each boot, use this instead:
bool initSD_overwrite() {
  if (!SD.begin(SD_CS_PIN)) return false;
  if (SD.exists("cStick.csv")) SD.remove("cStick.csv");
  logFile = SD.open("cStick.csv", FILE_WRITE);
  if (!logFile) return false;
  logFile.println("Distance,Pressure,HRV,Sugar level,SpO2,Accelerometer,Decision");
  logFile.flush();
  return true;
}
*/

// ================== SENSOR READS ==================
float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);
  if (duration == 0) return -1.0;

  return (duration * 0.0343f) / 2.0f;
}

float readPressurehPa() {
  float pressurePa = bmp.readPressure();
  if (pressurePa <= 0) return -1.0;
  return pressurePa / 100.0f;
}

float readHRV_BPM() {
  long irValue = particleSensor.getIR();

  if (irValue < 50000) { // no finger / weak signal
    lastBPM = 0.0;
    return 0.0;
  }

  if (checkForBeat(irValue)) {
    unsigned long now = millis();
    unsigned long delta = now - lastBeatMs;
    lastBeatMs = now;

    if (delta > 0) {
      float bpm = 60.0f / (delta / 1000.0f);
      if (bpm >= 40.0f && bpm <= 200.0f) lastBPM = bpm;
    }
  }
  return lastBPM;
}

int readSugarRaw() {
  return analogRead(SUGAR_PIN);
}

float readSpO2_placeholder() {
  // Your dataset has SpO2 values; plug your real SpO2 algorithm here.
  return -1.0f;
}

float readAccelMag_g() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  float ax = a.acceleration.x / 9.80665f;
  float ay = a.acceleration.y / 9.80665f;
  float az = a.acceleration.z / 9.80665f;

  return sqrt(ax * ax + ay * ay + az * az);
}

// ================== DECISION (0/1/2) ==================
int computeDecision(float distanceCm, float hrvBpm, int sugarRaw, float spo2, float accelMagG) {
  /*
    Replace this with your real model output or rules.
    Returning:
      0 = no fall
      1 = warning
      2 = fall
    For now we set unknown -> -1.
  */
  return -1;
}

// ================== CSV WRITE ==================
void writeRow(float distCm, float pressurehPa, float hrv, int sugar, float spo2, float accelMag, int decision) {
  // EXACT order like dataset:
  // Distance,Pressure,HRV,Sugar level,SpO2,Accelerometer,Decision

  // Serial debug
  Serial.print(distCm, 2); Serial.print(",");
  Serial.print(pressurehPa, 2); Serial.print(",");
  Serial.print(hrv, 2); Serial.print(",");
  Serial.print(sugar); Serial.print(",");
  Serial.print(spo2, 2); Serial.print(",");
  Serial.print(accelMag, 3); Serial.print(",");
  Serial.println(decision);

  // SD log
  if (logFile) {
    logFile.print(distCm, 2); logFile.print(",");
    logFile.print(pressurehPa, 2); logFile.print(",");
    logFile.print(hrv, 2); logFile.print(",");
    logFile.print(sugar); logFile.print(",");
    logFile.print(spo2, 2); logFile.print(",");
    logFile.print(accelMag, 3); logFile.print(",");
    logFile.println(decision);
    logFile.flush();
  }
}

// ================== SETUP / LOOP ==================
void setup() {
  Serial.begin(115200);
  delay(300);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  Wire.begin();

  // SD (append mode by default)
  initSD_append();

  // BMP280
  if (!bmp.begin(0x76)) {
    Serial.println("ERROR: BMP280 not found at 0x76 (try 0x77).");
  } else {
    Serial.println("BMP280 OK");
  }

  // MPU6050
  if (!mpu.begin()) {
    Serial.println("ERROR: MPU6050 not found.");
  } else {
    Serial.println("MPU6050 OK");
  }

  // MAX3010x
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("ERROR: MAX3010x not found.");
  } else {
    Serial.println("MAX3010x OK");
    particleSensor.setup();
    particleSensor.setPulseAmplitudeRed(0x1F);
    particleSensor.setPulseAmplitudeIR(0x1F);
    particleSensor.setPulseAmplitudeGreen(0);
  }

  // Print header to serial (optional)
  Serial.println("Distance,Pressure,HRV,Sugar level,SpO2,Accelerometer,Decision");
}

void loop() {
  unsigned long now = millis();
  if (now - lastSampleMs < SAMPLE_PERIOD_MS) return;
  lastSampleMs = now;

  float distCm = readDistanceCm();
  float pressurehPa = readPressurehPa();
  float hrv = readHRV_BPM();
  int sugar = readSugarRaw();
  float spo2 = readSpO2_placeholder();
  float accelMag = readAccelMag_g();

  int decision = computeDecision(distCm, hrv, sugar, spo2, accelMag);

  writeRow(distCm, pressurehPa, hrv, sugar, spo2, accelMag, decision);
}