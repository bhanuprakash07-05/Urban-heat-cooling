from flask import Blueprint, jsonify, request
from models.temperature_predictor import load_model_and_predict, sample_predictions
from models.cnn_site_classifier import sample_site_classification

bp = Blueprint("prediction", __name__)

# Temperature prediction: support GET (no body) and POST (body with features or zone list)
@bp.route("/temperature-prediction", methods=["GET", "POST"])
def temperature_prediction():
    # If POST with features list, use them. Otherwise return sample predictions for frontend table.
    if request.method == "POST":
        payload = request.get_json(force=True) or {}
        features = payload.get("features")
        if features:
            out = load_model_and_predict(features)
            return jsonify({"predictions": [out]}), 200

    # default: return an array of sample predictions (frontend needs an array)
    preds = sample_predictions()  # returns list of {location,daily_max,daily_min,heat_risk_level,...}
    return jsonify({"predictions": preds}), 200

# site classification endpoint used by frontend
@bp.route("/site-classification", methods=["GET"])
def site_classification():
    # optional ?zone=zone-1
    zone = request.args.get("zone", "zone-1")
    cls = sample_site_classification(zone)
    return jsonify(cls), 200
