"""Flask API exposing the weekly risk monitor for programmatic use.

Stage 13 deliverable. The API is a thin transport layer: every prediction goes
through :func:`src.serving.predict_one`, the same function the notebook and the
CLI use, so the served answer cannot drift from the analysed answer.

Run it with::

    python app.py                      # http://127.0.0.1:5001

Port 5001 is the default because macOS Control Center (AirPlay Receiver) binds
5000 and answers 403, which looks like an application bug but is not. Override
with the ``API_PORT`` environment variable.

Endpoints
---------
``GET  /health``    liveness plus which model is loaded
``GET  /schema``    the feature contract a caller must satisfy
``POST /predict``   score one observation; JSON body of feature name to number
"""

from __future__ import annotations

import logging
import os

from flask import Flask, jsonify, request

from src.serving import load_model, model_path, predict_one

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("risk_monitor.api")

app = Flask(__name__)


@app.get("/health")
def health():
    """Report liveness and whether a serving model is available."""

    bundle = load_model()
    return jsonify(
        {
            "status": "ok",
            "model_loaded": bundle is not None,
            "model_path": str(model_path()),
            "model_fit_end": bundle.fit_metadata.get("fit_end") if bundle else None,
        }
    )


@app.get("/schema")
def schema():
    """Return the feature contract so a caller can build a valid request."""

    bundle = load_model()
    if bundle is None:
        return jsonify({"error": "no serving model; run python run_pipeline.py first"}), 503
    return jsonify(
        {
            "required_features": bundle.required_features(),
            "all_values": "numeric",
            "example": {name: 0.0 for name in bundle.required_features()},
        }
    )


@app.post("/predict")
def predict():
    """Score one observation, answering 400 on bad input rather than 500."""

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "request body must be valid JSON"}), 400

    try:
        result = predict_one(payload)
    except ValueError as exc:  # bad or missing features
        logger.warning("rejected request: %s", exc)
        return jsonify({"error": str(exc)}), 400
    except FileNotFoundError as exc:  # model artifact absent
        logger.error("model unavailable: %s", exc)
        return jsonify({"error": str(exc)}), 503

    logger.info(
        "scored observation: %s (%.4f)",
        result["risk_classification"],
        result["elevated_risk_score"],
    )
    return jsonify(result)


if __name__ == "__main__":
    if load_model() is None:
        logger.warning("no model at %s -- /predict will return 503", model_path())
    port = int(os.getenv("API_PORT", "5001"))
    logger.info("serving on http://127.0.0.1:%d", port)
    app.run(host="127.0.0.1", port=port, debug=False)
