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
``GET  /plot``      the volatility-and-threshold chart as a PNG
``POST /run_full_analysis``  run the whole pipeline and regenerate every artifact
``GET  /run_full_analysis/<risk_quantile>/<test_fraction>``
                    refit with your own parameters and return the metrics, without
                    touching the committed artifacts
"""

from __future__ import annotations

import logging
import os

from flask import Flask, jsonify, request, send_file

from src.config import get_settings
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


@app.get("/plot")
def plot():
    """Return the volatility-and-threshold chart as an image."""

    figure = get_settings().images_dir / "volatility_and_risk_threshold.png"
    if not figure.exists():
        return jsonify(
            {"error": f"{figure.name} not generated; run python run_pipeline.py first"}
        ), 404
    return send_file(figure, mimetype="image/png")


@app.route("/run_full_analysis", methods=["GET", "POST"])
def run_full_analysis():
    """Run the pipeline end to end and report the artifacts it regenerated.

    This mutates the repository -- metrics, figures, model bundles and the deck
    are all rewritten -- so POST is the honest verb. GET is accepted too because
    it makes the route trivial to demonstrate from a browser or plain curl.
    Expect roughly half a minute.
    """

    from run_pipeline import run

    logger.info("full analysis requested (method=%s)", request.method)
    try:
        metrics = run(refresh=False)
    except Exception as exc:  # noqa: BLE001 - surface any pipeline failure as 500 JSON
        logger.exception("full analysis failed")
        return jsonify({"error": f"pipeline failed: {exc}"}), 500

    snapshot = metrics["latest_risk_snapshot"]
    regression = metrics["models"]["regression"]
    logger.info("full analysis complete: %s", snapshot["risk_classification"])
    return jsonify(
        {
            "status": "complete",
            "as_of_date": snapshot["as_of_date"],
            "risk_classification": snapshot["risk_classification"],
            "elevated_risk_score": snapshot["elevated_risk_score"],
            "ridge_mae": regression["ridge"]["mae"],
            "baseline_mae": regression["recent_volatility_baseline"]["mae"],
            "rows": metrics["data"]["rows_raw"],
            "artifacts": metrics["artifacts"],
        }
    )


@app.get("/run_full_analysis/<risk_quantile>/<test_fraction>")
def run_parameterised_analysis(risk_quantile: str, test_fraction: str):
    """Refit with caller-supplied parameters and return the resulting metrics.

    Deliberately does **not** write anything. Overwriting the committed artifacts
    with someone's exploratory parameters would make the repository's reported
    numbers untraceable, so this variant answers in-memory only.
    """

    try:
        quantile = float(risk_quantile)
        fraction = float(test_fraction)
    except ValueError:
        return jsonify({"error": "both parameters must be numbers"}), 400

    if not 0.0 < quantile < 1.0:
        return jsonify({"error": f"risk_quantile must be in (0, 1), got {quantile}"}), 400
    if not 0.05 <= fraction <= 0.5:
        return jsonify({"error": f"test_fraction must be in [0.05, 0.5], got {fraction}"}), 400

    from src.config import get_settings as _settings
    from src.modeling import fit_risk_models
    from src.storage import read_dataframe

    settings = _settings()
    dataset = settings.processed_dir / "spy_model_dataset.parquet"
    if not dataset.exists():
        return jsonify({"error": "run the pipeline first; no model dataset found"}), 503

    logger.info("parameterised refit: quantile=%.3f fraction=%.3f", quantile, fraction)
    bundle = fit_risk_models(
        read_dataframe(dataset),
        test_fraction=fraction,
        risk_quantile=quantile,
        include_diagnostics=False,
    )
    results = bundle.results
    return jsonify(
        {
            "inputs": {"risk_quantile": quantile, "test_fraction": fraction},
            "regression": results["regression"],
            "classification": results["classification"],
            "risk_threshold_annualized_vol": results["risk_threshold_annualized_vol"],
            "train_rows": results["train_rows"],
            "test_rows": results["test_rows"],
            "note": "computed in memory; committed artifacts were not modified",
        }
    )


if __name__ == "__main__":
    if load_model() is None:
        logger.warning("no model at %s -- /predict will return 503", model_path())
    port = int(os.getenv("API_PORT", "5001"))
    logger.info("serving on http://127.0.0.1:%d", port)
    app.run(host="127.0.0.1", port=port, debug=False)
