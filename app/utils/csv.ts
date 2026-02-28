import { FallDetectionLog } from "@/Entities/FallDetectionLog";

const HEADER = [
  "Distance","Pressure","HRV","Sugar level","SpO2","Accelerometer","Decision","Notes","Measurement Date"
];

export function toCSV(rows: FallDetectionLog[]): string {
  const header = HEADER.join(",");
  const body = rows.map(r => [
    r.distance, r.pressure, r.hrv, r.sugar_level, r.spo2, r.accelerometer, r.decision,
    quote(r.notes ?? ""), r.measurement_date
  ].join(",")).join("\n");
  return header + "\n" + body;
}

function quote(s: string) {
  if (s.includes(",") || s.includes("\n") || s.includes('"')) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}
