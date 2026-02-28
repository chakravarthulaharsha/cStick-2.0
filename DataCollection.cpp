/*
  cStick Data Logger -> SD card CSV

  CSV columns written:
  timestamp_ms,Distance_cm,Pressure_hPa,HRV_bpm,Sugar_raw,SpO2_pct,AccelMag_g,Latitude,Longitude

  Hardware (typical):
  - SD module (SPI): CS pin defined below
  - HC-SR04 ultrasonic: TRIG/ECHO pins defined below
  - BMP280 (I2C)
  - MAX30102/MAX30105 (I2C) for HRV & SpO2
  - MPU6050 (I2C) for accelerometer
  - Analog glucose sensor -> A0
  - GPS NEO-6M -> Serial1 (or SoftwareSerial if board lacks Serial1)

  Notes:
  - HRV/SpO2 from MAX3010x need stable finger placement and proper config.
  - The HRV shown here is a simple BPM estimate from beat detection (basic).
  - "Sugar_raw" is ADC raw value; convert to mg/dL using your sensor calibration.
*/

#include <Wire.h>
#include <SPI.h>
#include <SD.h>

// ---------- BMP280 ----------
#include <Adafruit_BMP280.h>

// ---------- MAX3010x ----------
#include <MAX30105.h>
#include "heartRate.h"   // from SparkFun MAX3010x library examples

// ---------- MPU6050 ----------
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// ---------- GPS ----------
#include <TinyGPSPlus.h>

// ================== PIN CONFIG ==================
static const int SD_CS_PIN = 10;      // change based on your wiring/board
static const int TRIG_PIN  = 7;
static const int ECHO_PIN  = 6;
static const int SUGAR_PIN = A0;

// If your board has Serial1 (Mega, many ESP32, etc.), use it for GPS:
#define GPS_SERIAL Serial1
static const uint32_t GPS_BAUD = 9600;

// ================== GLOBALS ==================
File logFile;

Adafruit_BMP280 bmp;           // I2C
MAX30105 particleSensor;       // I2C
Adafruit_MPU6050 mpu;          // I2C
TinyGPSPlus gps;

unsigned long lastSampleMs = 0;
const unsigned long SAMPLE_PERIOD_MS = 500;  // 2 Hz logging; change as needed

// MAX3010x beat detection state
float lastBPM = 0.0;
unsigned long lastBeatMs = 0;

// ================== HELPERS ==================
bool initSD() {
  if (!SD.begin(SD_CS_PIN)) {
    Serial.println("ERROR: SD init failed.");
    return false;
  }

  // Create/open file
  logFile = SD.open("cStick.csv", FILE_WRITE);
  if (!logFile) {
    Serial.println("ERROR: Cannot open cStick.csv");
    return false;
  }

  // If file is empty, write header
  if (logFile.size() == 0) {
    logFile.println("timestamp_ms,Distance_cm,Pressure_hPa,HRV_bpm,Sugar_raw,SpO2_pct,AccelMag_g,Latitude,Longitude");
    logFile.flush();
  }

  Serial.println("SD OK. Logging to cStick.csv");
  return true;
}

float readDistanceCm_HCSR04() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // timeout 30ms ~ 5m range
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);
  if (duration == 0) return -1.0; // no reading

  // speed of sound: 0.0343 cm/us, round-trip => /2
  float distanceCm = (duration * 0.0343f) / 2.0f;
  return distanceCm;
}

float readPressurehPa_BMP280() {
  // returns Pa -> convert to hPa
  float pressurePa = bmp.readPressure();
  if (pressurePa <= 0) return -1.0;
  return pressurePa / 100.0f;
}

int readSugarRaw_ADC() {
  // raw ADC 0..1023 (UNO) or 0..4095 (ESP32 depends)
  return analogRead(SUGAR_PIN);
}

float accelMagnitude_g() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);

  // a.acceleration is m/s^2; convert to g
  float ax = a.acceleration.x / 9.80665f;
  float ay = a.acceleration.y / 9.80665f;
  float az = a.acceleration.z / 9.80665f;

  float mag = sqrt(ax*ax + ay*ay + az*az);
  return mag;
}

/*
  Very simple SpO2 placeholder:
  Proper SpO2 needs red+IR ratio processing.
  SparkFun library focuses on heart rate; for SpO2 you can:
  - use Maxim algorithm implementations, or
  - use an SpO2-capable library for MAX30102.

  Here we return -1 unless you replace with your own SpO2 routine.
*/
float readSpO2_placeholder() {
  return -1.0f;
}

float readHRV_BPM_MAX3010x() {
  long irValue = particleSensor.getIR();

  // If no finger: IR low
  if (irValue < 50000) {
    lastBPM = 0.0;
    return 0.0;
  }

  // beat detection from SparkFun example
  if (checkForBeat(irValue)) {
    unsigned long now = millis();
    unsigned long delta = now - lastBeatMs;
    lastBeatMs = now;

    if (delta > 0) {
      float bpm = 60.0f / (delta / 1000.0f);
      // basic sanity clamp
      if (bpm >= 40.0f && bpm <= 200.0f) {
        lastBPM = bpm;
      }
    }
  }
  return lastBPM;
}

void feedGPS() {
  while (GPS_SERIAL.available() > 0) {
    gps.encode(GPS_SERIAL.read());
  }
}

bool getLatLon(double &lat, double &lon) {
  feedGPS();
  if (gps.location.isValid() && gps.location.age() < 2000) {
    lat = gps.location.lat();
    lon = gps.location.lng();
    return true;
  }
  return false;
}

void writeCSVRow(unsigned long tms,
                 float distCm,
                 float pressurehPa,
                 float hrvBpm,
                 int sugarRaw,
                 float spo2,
                 float accelMagG,
                 double lat,
                 double lon,
                 bool hasGPS) {

  // Build a CSV line (print to Serial + SD)
  // Use empty fields for GPS if not valid
  Serial.print(tms); Serial.print(",");
  Serial.print(distCm, 2); Serial.print(",");
  Serial.print(pressurehPa, 2); Serial.print(",");
  Serial.print(hrvBpm, 2); Serial.print(",");
  Serial.print(sugarRaw); Serial.print(",");
  Serial.print(spo2, 2); Serial.print(",");
  Serial.print(accelMagG, 3); Serial.print(",");

  if (hasGPS) {
    Serial.print(lat, 6); Serial.print(",");
    Serial.print(lon, 6);
  } else {
    Serial.print(","); // lat empty
    Serial.print("");  // lon empty (already last field)
  }
  Serial.println();

  if (logFile) {
    logFile.print(tms); logFile.print(",");
    logFile.print(distCm, 2); logFile.print(",");
    logFile.print(pressurehPa, 2); logFile.print(",");
    logFile.print(hrvBpm, 2); logFile.print(",");
    logFile.print(sugarRaw); logFile.print(",");
    logFile.print(spo2, 2); logFile.print(",");
    logFile.print(accelMagG, 3); logFile.print(",");

    if (hasGPS) {
      logFile.print(lat, 6); logFile.print(",");
      logFile.print(lon, 6);
    } else {
      logFile.print(",");
      logFile.print("");
    }
    logFile.println();
    logFile.flush(); // ensures data is saved each row (safer, slightly slower)
  }
}

// ================== SETUP / LOOP ==================
void setup() {
  Serial.begin(115200);
  delay(300);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  Wire.begin();

  // GPS
  GPS_SERIAL.begin(GPS_BAUD);

  // SD
  initSD();

  // BMP280
  if (!bmp.begin(0x76)) { // common addresses: 0x76 or 0x77
    Serial.println("ERROR: BMP280 not found at 0x76. Try 0x77 or check wiring.");
  } else {
    Serial.println("BMP280 OK");
  }

  // MPU6050
  if (!mpu.begin()) {
    Serial.println("ERROR: MPU6050 not found. Check wiring.");
  } else {
    Serial.println("MPU6050 OK");
  }

  // MAX3010x
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("ERROR: MAX3010x not found. Check wiring.");
  } else {
    Serial.println("MAX3010x OK");
    // Typical config from SparkFun examples
    particleSensor.setup();               // default config
    particleSensor.setPulseAmplitudeRed(0x1F);
    particleSensor.setPulseAmplitudeIR(0x1F);
    particleSensor.setPulseAmplitudeGreen(0); // off
  }
}

void loop() {
  // Keep GPS parser updated
  feedGPS();

  unsigned long now = millis();
  if (now - lastSampleMs < SAMPLE_PERIOD_MS) return;
  lastSampleMs = now;

  float distCm = readDistanceCm_HCSR04();
  float pressurehPa = readPressurehPa_BMP280();
  float hrvBpm = readHRV_BPM_MAX3010x();
  int sugarRaw = readSugarRaw_ADC();
  float spo2 = readSpO2_placeholder();     // replace with your real SpO2 algorithm
  float accelMagG = accelMagnitude_g();

  double lat = 0.0, lon = 0.0;
  bool hasGPS = getLatLon(lat, lon);

  writeCSVRow(now, distCm, pressurehPa, hrvBpm, sugarRaw, spo2, accelMagG, lat, lon, hasGPS);
}