# Homework 13 — Productization

A linear regression trained on 100 synthetic samples with two features
(`make_regression(n_samples=100, n_features=2, noise=0.1, random_state=42)`).
It takes two numbers and returns a single predicted value.

## Start the server

```bash
python app.py
```

Serves on `http://127.0.0.1:5002`. Port 5002 rather than 5000, because macOS Control Center binds
5000 and answers 403 — which looks like a bug in the app and is not.

## Routes

**POST /predict** — for a program sending JSON.

```bash
curl -s -X POST http://127.0.0.1:5002/predict \
  -H 'Content-Type: application/json' \
  -d '{"features": [0.5, -0.2]}'
```
```json
{"prediction": 29.0467}
```

**GET /predict/<f1>/<f2>** — for a person or a browser.

```bash
curl -s http://127.0.0.1:5002/predict/0.5/-0.2
```
```json
{"prediction": 29.0467}
```

Both routes use the same model object, loaded once when the app starts, so they return the same
number for the same input.

## Bad input

Both routes answer with JSON and HTTP 400 rather than a traceback:

| Request | Response |
|---|---|
| `{"x": [1, 2]}` — no `features` key | 400 `{"error": "body must be JSON with a 'features' key"}` |
| `{"features": [1.0]}` — wrong count | 400 `{"error": "'features' must be a list of 2 numbers, got [1.0]"}` |
| `/predict/abc/0.2` — not a number | 400 `{"error": "both parameters must be numbers, got 'abc' and '0.2'"}` |
