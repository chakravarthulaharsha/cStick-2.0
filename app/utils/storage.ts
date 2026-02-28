import { FallDetectionLog } from "@/Entities/FallDetectionLog";

const KEY = "cstick.logs.v1";

export function getLogs(): FallDetectionLog[] {
  const raw = localStorage.getItem(KEY);
  if (!raw) return [];
  try { return JSON.parse(raw) as FallDetectionLog[]; } catch { return []; }
}

export function setLogs(logs: FallDetectionLog[]) {
  localStorage.setItem(KEY, JSON.stringify(logs));
}

export function addLog(log: FallDetectionLog) {
  const logs = getLogs();
  logs.unshift(log);
  setLogs(logs);
}

export function updateLog(id: string, patch: Partial<FallDetectionLog>) {
  setLogs(getLogs().map(l => (l.id === id ? { ...l, ...patch } : l)));
}

export function deleteLog(id: string) {
  setLogs(getLogs().filter(l => l.id !== id));
}
