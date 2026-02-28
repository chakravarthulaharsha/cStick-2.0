# Algorithm 3 - Cloud Side (Ingest, Train Global Θ', Derive Per-user Seed ϕu, Publish)

import pandas as pd
import numpy as np
from pathlib import Path

def ingest_user_blob(user_id, decompressed_csv_text, cloud_store_dir="cloud_data"):
    cloud_dir = Path(cloud_store_dir) / user_id
    cloud_dir.mkdir(parents=True, exist_ok=True)
    f = cloud_dir / "logs.csv"
    # append to per-user dataset store
    with f.open("a") as out:
        out.write(decompressed_csv_text)

def split_df(df, val_frac=0.2, seed=42):
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    n = len(df)
    nva = int(n * val_frac)
    return df.iloc[nva:], df.iloc[:nva]

def train_global_theta(theta_prev, df_train):
    """
    Replace with real training:
    - load previous global weights Θ
    - train on aggregated user data
    - return updated Θ'
    """
    theta_prime = {"weights_version": theta_prev.get("weights_version", 0) + 1}
    return theta_prime

def metrics_pass(theta_prime, df_val):
    # Placeholder: compute accuracy/ROC-AUC etc.
    return True

def derive_seed(theta_prime, df_user):
    """
    ϕu = DeriveSeed(Θ', Du)
    In practice: personalization head weights, calibration params,
    or LoRA-like adapter computed for that user.
    """
    return {"user_bias": float(df_user["hrv"].mean()) if "hrv" in df_user else 0.0}

def assemble(theta_prime, phi_u):
    """
    Θ'u = Assemble(Θ', ϕu)
    Return a package (bytes) for edge download (e.g., TFLite + JSON adapters).
    """
    pkg = {
        "global": theta_prime,
        "personal": phi_u
    }
    return json.dumps(pkg).encode("utf-8")

def publish(theta_prime, out_dir="published"):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    Path(out_dir, "global_theta.json").write_text(json.dumps(theta_prime, indent=2))

def cloud_job(global_theta_path="published/global_theta.json", cloud_data_dir="cloud_data"):
    # Load previous Θ
    theta_prev = {"weights_version": 0}
    gp = Path(global_theta_path)
    if gp.exists():
        theta_prev = json.loads(gp.read_text())

    # Aggregate all user data
    all_rows = []
    users = []
    for user_dir in Path(cloud_data_dir).glob("*"):
        if user_dir.is_dir():
            f = user_dir / "logs.csv"
            if f.exists():
                dfu = pd.read_csv(f)
                dfu["user"] = user_dir.name
                all_rows.append(dfu)
                users.append(user_dir.name)

    if len(all_rows) == 0:
        return

    D = pd.concat(all_rows, ignore_index=True)

    Dtr, Dva = split_df(D)
    theta_prime = train_global_theta(theta_prev, Dtr)

    if metrics_pass(theta_prime, Dva):
        publish(theta_prime)

        # Per-user seeds
        for u in users:
            Du = D[D["user"] == u].copy()
            phi_u = derive_seed(theta_prime, Du)
            pkg_bytes = assemble(theta_prime, phi_u)
            out_u = Path("published") / u
            out_u.mkdir(parents=True, exist_ok=True)
            (out_u / "model_pkg.bin").write_bytes(pkg_bytes)

# cloud_job()  # run on schedule (e.g., weekly)