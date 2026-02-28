# Algorithm 3 - Edge Side (Logging, Predict, MicroAdapt, Weekly Sync, Fetch Updates)

import os, time, json, gzip
from dataclasses import dataclass
from pathlib import Path
import numpy as np

EDGE_CSV = Path("edge_logs.csv")
STATE_JSON = Path("edge_state.json")

@dataclass
class DeviceCaps:
    max_model_bytes: int = 300_000
    int8_quant: bool = True

def ensure_csv_exists():
    if not EDGE_CSV.exists():
        EDGE_CSV.write_text("t,a,g,hrv,bs,sp,d,user,ctx\n")

def load_state():
    if STATE_JSON.exists():
        return json.loads(STATE_JSON.read_text())
    return {"last_sync_ts": 0, "user": "u1"}

def save_state(st):
    STATE_JSON.write_text(json.dumps(st, indent=2))

def preprocess_window(raw_x6):
    # Minimal validity checks; expand as you need
    if np.any(np.isnan(raw_x6)):
        return None
    return raw_x6.astype(np.float32)

def append_row(t, x6, user, ctx=""):
    line = "{},{},{},{},{},{},{},{},{}\n".format(
        int(t), *[float(v) for v in x6], user, ctx
    )
    with EDGE_CSV.open("a") as f:
        f.write(line)

def predict(model, x6):
    # model is an object with predict_proba or similar
    probs = model.predict_proba(x6[None, :])[0]
    yhat = int(np.argmax(probs))
    conf = float(np.max(probs))
    return yhat, conf, probs

def detect_drift(conf, conf_thresh=0.60):
    return conf < conf_thresh

def micro_adapt(model, x6):
    """
    Lightweight on-device micro update.
    In real edge deployments: update batchnorm stats, calibrate thresholds,
    or do a tiny SGD step if you have labels.
    Here: placeholder that returns model unchanged.
    """
    return model

def rows_after(last_ts):
    rows = []
    with EDGE_CSV.open("r") as f:
        header = f.readline()
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 10:
                continue
            t = int(parts[0])
            if t > last_ts:
                rows.append(line)
    return rows

def compress_bytes(lines):
    raw = "".join(lines).encode("utf-8")
    return gzip.compress(raw)

def encrypt_bytes(blob):
    # Placeholder: replace with AES-GCM, libsodium, etc.
    # Do NOT ship plaintext in real deployments.
    return blob

def upload_to_cloud(enc_blob):
    # Placeholder: HTTP POST to your server / storage
    # Return True if successful
    return True

def download_from_cloud(user):
    # Placeholder: pull latest model package for user
    # Return bytes or None
    return None

def quantize_if(model_bytes, caps: DeviceCaps):
    # Placeholder: if too large, choose int8 model variant
    return model_bytes

def warmup_and_activate(model_bytes):
    # Placeholder: load into runtime and run 1-2 dummy inferences
    print("Activated updated personalized model (bytes={})".format(
        len(model_bytes) if model_bytes else 0
    ))

# ---- Dummy model wrapper (so code runs as reference) ----
class DummyModel:
    def predict_proba(self, X):
        # returns [p0,p1,p2]
        return np.array([[0.8, 0.15, 0.05]], dtype=np.float32)

# ---- Main edge loop ----
def edge_run(delta_t_s=1.0):
    ensure_csv_exists()
    st = load_state()
    user = st["user"]
    last_sync_ts = st["last_sync_ts"]

    caps = DeviceCaps()
    model = DummyModel()  # replace with your local deployed model Θ̂u

    while True:
        # Edge: collect & log
        t = int(time.time())
        raw_x6 = np.array([0.12, 0.05, 72.0, 96.0, 98.0, 150.0], dtype=np.float32)  # replace
        x6 = preprocess_window(raw_x6)
        if x6 is not None:
            append_row(t, x6, user, ctx="walk")

        # Edge: predict & micro-adapt
        yhat, conf, probs = predict(model, x6)
        if detect_drift(conf):
            model = micro_adapt(model, x6)

        # Weekly: sync to cloud (simulate using a trigger)
        weekly_trigger = (time.gmtime().tm_wday == 6 and time.gmtime().tm_hour == 23)  # Sunday 23:00 UTC
        policy_ok = True

        if weekly_trigger and policy_ok:
            B = rows_after(last_sync_ts)
            if len(B) > 0:
                payload = encrypt_bytes(compress_bytes(B))
                ok = upload_to_cloud(payload)
                if ok:
                    last_sync_ts = max(int(line.split(",")[0]) for line in B)
                    st["last_sync_ts"] = last_sync_ts
                    save_state(st)

        # Edge: fetch & activate personalized update
        pkg = download_from_cloud(user)
        if pkg is not None:
            pkg = quantize_if(pkg, caps)
            warmup_and_activate(pkg)

        time.sleep(delta_t_s)

# edge_run()  # uncomment when using for real