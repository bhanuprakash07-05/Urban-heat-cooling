from flask import Blueprint, jsonify, request
from models.recommendation_engine import sample_recommendations

bp = Blueprint("recommendation", __name__)

@bp.route("/optimized", methods=["GET"])
def optimized():
    # Accept optional ?city=Delhi
    city = request.args.get("city", "Delhi")
    result = sample_recommendations(city)
    return jsonify(result), 200
@bp.route("/custom", methods=["POST"])
def custom():
    from backend.services.optimization import HeatInterventionOptimizer

    data = request.get_json()
    city = data.get("city", "Delhi")
    interventions = data.get("interventions", [])
    constraints = data.get("constraints", {
        "max_budget": 1000000  # default 1 million
    })

    optimizer = HeatInterventionOptimizer(interventions, constraints)
    result = optimizer.optimize()

    return jsonify(result), 200