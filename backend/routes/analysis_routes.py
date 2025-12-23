from flask import Blueprint, jsonify, request
import pandas as pd
from pathlib import Path
from datetime import datetime

bp = Blueprint("analysis", __name__)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HEAT_CSV = DATA_DIR / "heatmap_delhi_sample.csv"

@bp.route("/heat-comprehensive", methods=["GET"])
def heat_comprehensive():
    # support optional query params (city, date_range) in future
    if not HEAT_CSV.exists():
        # return an empty but valid structure for frontend
        return jsonify({
            "heatMap": {
                "data": [],
                "statistics": {"avg": 0, "max": 0, "min": 0, "count": 0},
                "clusters": [],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }), 200

    df = pd.read_csv(HEAT_CSV)
    points = []
    for _, r in df.iterrows():
        points.append({
            "lat": float(r.get("lat", 0)),
            "lng": float(r.get("lng", r.get("lon", 0))),
            "temperature": float(r.get("temperature", 0)),
            "cluster": int(r.get("cluster_id", 0)),
            "location": r.get("location", "")
        })

    stats = {
        "avg": float(df["temperature"].mean()),
        "max": float(df["temperature"].max()),
        "min": float(df["temperature"].min()),
        "count": int(len(df))
    }

    clusters = [
        {"cluster_id": int(cid), "avg_temp": float(group["temperature"].mean())}
        for cid, group in df.groupby("cluster_id")
    ]

    return jsonify({
        "heatMap": {
            "data": points,
            "statistics": stats,
            "clusters": clusters,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }), 200
@bp.route("/heat-intervention-optimization", methods=["POST"])
def heat_intervention_optimization():
    from backend.services.optimization import HeatInterventionOptimizer

    data = request.get_json()
    interventions = data.get("interventions", [])
    constraints = data.get("constraints", {})
    optimization_params = data.get("optimization_params", {})

    optimizer = HeatInterventionOptimizer(
        population_size=optimization_params.get("population_size", 50),
        generations=optimization_params.get("generations", 100),
        mutation_rate=optimization_params.get("mutation_rate", 0.1),
        crossover_rate=optimization_params.get("crossover_rate", 0.7)
    )

    result = optimizer.optimize_interventions(interventions, constraints)

    return jsonify(result), 200