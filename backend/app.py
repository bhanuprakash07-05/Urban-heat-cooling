from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    # register blueprints
    from routes.analysis_routes import bp as analysis_bp
    from routes.prediction_routes import bp as prediction_bp
    from routes.recommendation_routes import bp as recommendation_bp
    from routes.data_routes import bp as data_bp

    app.register_blueprint(analysis_bp, url_prefix="/api/heat-analysis")
    app.register_blueprint(prediction_bp, url_prefix="/api/ml")
    app.register_blueprint(recommendation_bp, url_prefix="/api/recommendations")
    app.register_blueprint(data_bp, url_prefix="/api/citizen")

    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok", "message": "COOL.AI backend running"}, 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
