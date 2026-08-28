# Handoff plan

**Author:** Paritosh Dwivedi

What an on-call operator would need to run and support this service.

- **Deployment path.** `python run_pipeline.py` produces `model/model.pkl`;
  `python app.py` serves it on `127.0.0.1:5001`. There is no container or cloud
  target — this course stops at the conceptual boundary, and the API is intended
  to run locally or behind an internal reverse proxy.
- **Endpoints.** `GET /health` (liveness plus which model is loaded),
  `GET /schema` (the ten-feature contract), `POST /predict` (score one
  observation). No authentication is implemented; anything beyond localhost must
  sit behind an authenticating proxy before it carries real traffic.
- **Data contract.** `/predict` accepts a JSON object with all ten features from
  `src/features.py::FEATURE_COLUMNS`, every value numeric. Missing or
  non-numeric fields return **400** with the offending field named. A missing
  model artifact returns **503**, not 500, so a monitor can distinguish "not
  ready" from "broken".
- **Versioning and rollback.** `model/model.pkl` is the serving artifact and is
  pinned until explicitly refreshed; `model/risk_models.joblib` is rewritten by
  every pipeline run. Rollback is restoring the previous `model.pkl` and
  restarting the process. Keep the last three.
- **Port conflict, known.** macOS Control Center binds port 5000 and answers
  **403**, which looks like an application fault and is not. The default is 5001;
  override with `API_PORT`.
- **Monitoring and alerts.** See `docs/monitoring_plan.md` for the six metrics,
  thresholds and routing.
- **Interpreting the output.** `elevated_risk_score` is a ranking and decision
  score, not a calibrated probability — the response says so on every call. A
  `normal` classification means no elevated flag was raised under the stated
  assumptions; it is not a claim the position is safe.
- **Known limitation to state at handoff.** The model under-predicts the top
  realised-volatility decile by roughly 8.5 percentage points, so it is least
  reliable in exactly the conditions that matter most. Calendar-year recall
  ranges from 33% to 83%.
- **Escalation.** On-call operator, then the model owner (Paritosh Dwivedi).
  Reproduce any incident with `python -m src.run_step score` before escalating —
  it exercises the same prediction path as the API.
- **Audit.** Every raw snapshot in `data/raw/` has a manifest with provider,
  parameters, timestamp and SHA-256, so any past decision can be tied to the
  exact input that produced it.
