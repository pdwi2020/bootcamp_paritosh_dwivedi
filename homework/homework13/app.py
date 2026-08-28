"""Flask API serving the Stage 13 homework model."""

import logging

import joblib
import numpy as np
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hw13")

# Loaded ONCE at startup, not per request.
MODEL = joblib.load("model/model.pkl")
N_FEATURES = 2

app = Flask(__name__)


def _predict(values):
    return float(MODEL.predict(np.array(values, dtype=float).reshape(1, -1))[0])


@app.post("/predict")
def predict_post():
    """Score a JSON body of the form {"features": [f1, f2]}."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or "features" not in body:
        return jsonify({"error": "body must be JSON with a 'features' key"}), 400

    features = body["features"]
    if not isinstance(features, (list, tuple)) or len(features) != N_FEATURES:
        return jsonify(
            {"error": f"'features' must be a list of {N_FEATURES} numbers, got {features!r}"}
        ), 400
    try:
        values = [float(v) for v in features]
    except (TypeError, ValueError):
        return jsonify({"error": "every feature must be a number"}), 400

    prediction = _predict(values)
    logger.info("POST /predict %s -> %.4f", values, prediction)
    return jsonify({"prediction": prediction})


@app.get("/predict/<f1>/<f2>")
def predict_path(f1, f2):
    """Score two path parameters, for a person or a browser."""
    try:
        values = [float(f1), float(f2)]
    except ValueError:
        return jsonify({"error": f"both parameters must be numbers, got {f1!r} and {f2!r}"}), 400

    prediction = _predict(values)
    logger.info("GET /predict/%s/%s -> %.4f", f1, f2, prediction)
    return jsonify({"prediction": prediction})


if __name__ == "__main__":
    # 5002, not 5000: macOS Control Center binds 5000 and answers 403.
    app.run(host="127.0.0.1", port=5002, debug=False)
