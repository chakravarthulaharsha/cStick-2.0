export type Pressure = 0 | 1 | 2;        // 0=Low, 1=Medium, 2=High
export type Accelerometer = 0 | 1;       // 0=No, 1=Detected
export type Decision = 0 | 1 | 2;        // 0=Safe, 1=Warning, 2=Fall

export interface FallDetectionLog {
  id: string;
  distance: number;            // meters
  pressure: Pressure;
  hrv: number;                 // ms
  sugar_level: number;         // mg/dL
  spo2: number;                // %
  accelerometer: Accelerometer;
  decision: Decision;
  notes?: string;
  measurement_date: string;    // e.g., '2025-01-20T08:30'
}
