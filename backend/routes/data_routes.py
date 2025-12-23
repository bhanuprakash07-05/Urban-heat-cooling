from flask import Blueprint, jsonify, request
from pathlib import Path
import json
from datetime import datetime

bp = Blueprint("citizen", __name__)
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CITIZEN_FILE = DATA_DIR / "citizen_reports.json"

# return summary object used by CitizenPortal
@bp.route("/engagement", methods=["GET"])
def engagement():
    if CITIZEN_FILE.exists():
        with open(CITIZEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "total_reports": 0,
            "active_users": 0,
            "recent_reports": []
        }
    return jsonify(data), 200

# accept new report (frontend currently logs to console; still good to have)
@bp.route("/reports", methods=["POST"])
def create_report():
    payload = request.get_json(force=True) or {}
    report = {
        "id": payload.get("id") or int(datetime.utcnow().timestamp()),
        "location": payload.get("location", "Unknown"),
        "temperature_reported": payload.get("temperature", None),
        "description": payload.get("description", ""),
        "severity": payload.get("severity", "medium"),
        "status": "verified" if payload.get("temperature", 0) > 40 else "investigating",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    # append to JSON file
    if CITIZEN_FILE.exists():
        with open(CITIZEN_FILE, "r", encoding="utf-8") as f:
            arr = json.load(f)
    else:
        arr = {"total_reports": 0, "active_users": 0, "recent_reports": []}

    arr["recent_reports"].insert(0, report)
    arr["total_reports"] = arr.get("total_reports", 0) + 1
    arr["active_users"] = max(arr.get("active_users", 0), 1)

    with open(CITIZEN_FILE, "w", encoding="utf-8") as f:
        json.dump(arr, f, indent=2)

    return jsonify({"status": "ok", "report": report}), 201
    interventions = data.get("interventions", [])
    constraints = data.get("constraints", {})
    optimization_params = data.get("optimization_params", {})

    optimizer = HeatInterventionOptimizer(interventions, constraints, optimization_params)
    result = optimizer.optimize()

    return jsonify(result), 200 