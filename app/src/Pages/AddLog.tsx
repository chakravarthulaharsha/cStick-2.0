import React from "react";
import LogForm from "@/Components/logs/LogForm";
import { addLog } from "@/utils/storage";
import { useNavigate } from "react-router-dom";
import type { FallDetectionLog } from "@/Entities/FallDetectionLog";

export default function AddLog() {
  const nav = useNavigate();
  function handleSubmit(data: FallDetectionLog) {
    addLog(data);
    nav("/DailyView"); // change to your route
  }
  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-4">Add Fall Detection Log</h1>
      <LogForm onSubmit={handleSubmit} />
    </div>
  );
}
