#!/usr/bin/env python3
"""
AgroGuard AI: AI-Powered Grain Spoilage Prevention System
Single-Command Unified Application Launcher
Department of Computer Science & Engineering · K.R. Mangalam University (CS002)
"""

import os
import sys

# Configure standard streams for UTF-8 on Windows consoles
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import uvicorn

BANNER = r"""
   ___                 ____                     __   ___    ____
  / _ | ___ ________  / ___/_ _____ ___________/ /  / _ |  /  _/
 / __ |/ _ `/ __/ _ \/ (_ / // / _ `/ __/ _  / _ \ / __ | _/ /  
/_/ |_|\_, /_/  \___/\___/\_,_/\_,_/_/  \_,_/_//_//_/ |_|/___/  
      /___/                                                     
  🌾 AI-POWERED GRAIN SPOILAGE PREVENTION PLATFORM FOR STORAGE FACILITIES
  🎓 K.R. Mangalam University · CS002 Community Service Project (Semester-III)
  👥 Team: Chirag Chanchal, Divyant, Aditya Diwakar, Adarsh Sharma, Sambhav Sharma
  🌍 Aligned with UN SDGs: SDG 2 (Zero Hunger) · SDG 12 (Responsible Prod.) · SDG 13 (Climate)
"""


def verify_ml_models():
    """Ensures model artifacts exist before starting the server."""
    model_dir = os.path.join(os.path.dirname(__file__), "ml_engine", "saved_models")
    rf_path = os.path.join(model_dir, "rf_spoilage_model.joblib")
    nn_path = os.path.join(model_dir, "nn_spoilage_model.joblib")

    if not os.path.exists(rf_path) or not os.path.exists(nn_path):
        print("[!] Pre-trained models not found. Initiating automated training pipeline...")
        from ml_engine.train_models import train_and_evaluate_models
        train_and_evaluate_models()
    else:
        print("[✓] Pre-trained Random Forest and Neural Network models loaded successfully.")


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def get_usable_port(preferred_port: int, host: str = "127.0.0.1") -> int:
    if not is_port_in_use(preferred_port, host):
        return preferred_port
    print(f"[!] Port {preferred_port} is already in use by another process.")
    for p in range(preferred_port + 1, preferred_port + 20):
        if not is_port_in_use(p, host):
            print(f"[✓] Automatically selected available alternate port: {p}")
            return p
    return preferred_port


def main():
    print(BANNER)
    verify_ml_models()

    host = os.getenv("HOST", "0.0.0.0")
    requested_port = int(os.getenv("PORT", "8000"))
    port = get_usable_port(requested_port, "127.0.0.1" if host == "0.0.0.0" else host)

    print(f"\n[🚀] Starting AgroGuard AI Server...")
    print(f"     ► Web Dashboard:  http://localhost:{port}")
    print(f"     ► REST API Docs:  http://localhost:{port}/docs")
    print(f"     ► OpenAPI Schema: http://localhost:{port}/openapi.json")
    print(f"     ► Health Check:   http://localhost:{port}/api/health\n")

    uvicorn.run("backend.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
