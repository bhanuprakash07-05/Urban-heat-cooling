# Urban Heat Cooling 

Urban Heat Cooling is a Python/Flask backend prototype that provides heat‑analysis, temperature prediction, citizen reporting and intervention recommendation endpoints for urban heat / cooling planning. The repo includes a Flask application (backend/) with routes for analysis, predictions, recommendations and citizen reports, plus example/sample-model utilities.

This README documents what I found in the repository, how to run the backend locally, and recommended next steps to stabilize, containerize, and publish the project.

Status
- Working prototype (Flask app) with example/sample functions and routes.
- Some development artifacts (a committed virtual environment under `backend/venv`) are present — see "Repository hygiene" below.
- No top-level `requirements.txt` or Dockerfile detected (create these to improve reproducibility).

What’s in the repository (important files / folders observed)
- backend/
  - app.py — Flask application factory and entrypoint (runs on host 0.0.0.0:5000 by default).
  - routes/
    - analysis_routes.py — heatmap endpoints (e.g., GET /api/heat-analysis/heat-comprehensive, POST /api/heat-analysis/heat-intervention-optimization). Uses backend/data/heatmap_delhi_sample.csv.
    - data_routes.py — citizen reporting endpoints (e.g., POST /api/citizen/reports) which append JSON reports to a file.
    - recommendation_routes.py — recommendation endpoints (/api/recommendations/optimized GET and /api/recommendations/custom POST) using a local optimizer.
    - prediction_routes.py — (referenced by app.py; provides /api/ml endpoints — implement details live in the repo).
  - models/
    - temperature_predictor.py — sample prediction utilities.
    - recommendation_engine.py — helper for sample recommendations (referenced by route).
  - services/ — optimization / algorithmic helpers referenced by routes.
  - data/
    - heatmap_delhi_sample.csv — sample heatmap CSV used by analysis endpoints (referenced in routes).
  - venv/ — a committed Python virtual environment (lots of site-packages files present).
- Other files
  - No license file detected at repo root (add LICENSE).
  - No explicit requirements.txt or environment.yml in repo root or backend/ (add one).
  - No Dockerfile or docker-compose.yml detected (recommended to add).
  - No CI workflows discovered (consider adding .github/workflows).

Observed / inferred dependencies
- Flask, flask-cors (app uses CORS), pandas, numpy
- Several geospatial/science libs found inside committed venv: geopandas, pyproj, pyogrio, shapely (these indicate geospatial operations may be used)
- Likely additional libs: scikit-learn (if models are used), joblib, or similar
Note: these packages were found inside the committed venv. Please create a clean requirements.txt listing only what the app needs (no site-packages).

Quickstart — run locally (recommended)
1. Clone
```bash
git clone https://github.com/bhanuprakash07-05/Urban-heat-cooling.git
cd Urban-heat-cooling
```

2. Create an isolated virtualenv and install dependencies (example)
```bash
python3 -m venv .venv
source .venv/bin/activate
# Create requirements.txt (see suggested content below) then:
pip install -r requirements.txt
```

Suggested minimal requirements.txt (create this file in repo root)
```
Flask>=2.2
flask-cors
pandas
numpy
scikit-learn
# optional / only if used:
geopandas
pyproj
pyogrio
shapely
```
Adjust versions as needed for your environment.

3. Run the backend
From repository root:
```bash
# Run the Flask app defined at backend/app.py
python backend/app.py
```
This starts the API on http://0.0.0.0:5000 by default. The app exposes a simple health route and registers the blueprints under the prefixes shown below.

API endpoints (observed)
- GET /health
  - Basic health check → returns {"status": "ok", "message": "COOL.AI backend running"}
- Heat analysis (blueprint prefix `/api/heat-analysis`)
  - GET /api/heat-analysis/heat-comprehensive
    - Returns heatmap points and basic statistics (loads backend/data/heatmap_delhi_sample.csv)
  - POST /api/heat-analysis/heat-intervention-optimization
    - Accepts JSON with interventions / constraints and runs an optimizer (HeatInterventionOptimizer) — returns optimization result
- ML / prediction (blueprint prefix `/api/ml`)
  - Prediction endpoints are registered (see `routes/prediction_routes.py`) — used for sample_predictions / model endpoints
- Recommendations (blueprint prefix `/api/recommendations`)
  - GET /api/recommendations/optimized?city=Delhi
  - POST /api/recommendations/custom — accepts city/interventions/constraints → returns optimized suggestions
- Citizen reporting (blueprint prefix `/api/citizen`)
  - POST /api/citizen/reports — accepts a JSON payload with fields such as `location`, `temperature`, `description`, `severity`; it appends to a JSON file and returns status 201 when created.

Example curl requests
- Health:
```bash
curl http://localhost:5000/health
```
- Get heatmap:
```bash
curl http://localhost:5000/api/heat-analysis/heat-comprehensive
```
- Create a citizen report:
```bash
curl -X POST http://localhost:5000/api/citizen/reports \
  -H "Content-Type: application/json" \
  -d '{"location":"Karol Bagh","temperature":42,"description":"Very hot","severity":"high"}'
```
- Get sample recommendations:
```bash
curl "http://localhost:5000/api/recommendations/optimized?city=Delhi"
```

Data
- backend/data/heatmap_delhi_sample.csv — used by heat analysis endpoints. Replace or extend with real data for production.
- Citizen reports are appended to a JSON file (path controlled in `backend/routes/data_routes.py` via a constant such as CITIZEN_FILE) — ensure correct file permissions.

Repository hygiene & recommended fixes
- Remove the committed Python virtualenv (`backend/venv/`) from the repo. Commit only a requirements.txt or environment.yml. Steps:
  - Add `backend/venv/` (and other `venv` paths) to `.gitignore`.
  - Remove the venv from git with:
    ```bash
    git rm -r --cached backend/venv
    git commit -m "Remove committed virtualenv and add to .gitignore"
    ```
- Add a top-level `requirements.txt` or `environment.yml` that lists the real dependencies.
- Add a LICENSE file (e.g., MIT) if you intend to open-source the project.
- Add README files for both the backend and any frontend (if added later) that document environment variables and ports.

Containerization (example)
- Example Dockerfile (backend) — create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/ ./backend/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "backend/app.py"]
```
- Build & run:
```bash
docker build -t urban-heat-cooling .
docker run -p 5000:5000 urban-heat-cooling
```

CI / Deployment suggestions
- Add `.github/workflows/ci.yml` to run:
  - Python linting (flake8/ruff)
  - Unit tests (pytest) — add tests/ directory and simple tests for routes or internal functions
  - `pip install -r requirements.txt` and `python -m backend.app` smoke test (use a short timeout)
- Add deployment instructions for a cloud host or container registry (GHCR, DockerHub, AWS ECR).

Testing
- No automated tests were found. Recommended:
  - Add unit tests for route functions under `tests/` using pytest and Flask test client
  - Add simple integration tests to call `/health` and a few example endpoints

Security & robustness notes
- Sanitize and validate inputs for POST endpoints (the code currently trusts JSON payloads and writes to disk).
- Consider using file/DB storage for citizen reports (e.g., SQLite/Postgres) instead of appending to JSON for concurrency and durability.
- Add CORS restrictions (if the API will be consumed by untrusted domains) and rate-limiting if opened to the public.

Next steps I can help with
- Create a cleaned commit or PR that:
  - Removes `backend/venv` from repository and adds `.gitignore`
  - Adds a `requirements.txt` with pinned versions
  - Adds a Dockerfile and a simple `docker-compose.yml` to run the app and optional services
  - Adds a `LICENSE` (MIT) if you want
- Add a minimal pytest-based test that runs the health endpoint

If you want any of the above automated changes, tell me which items to create and I will prepare the file contents and a branch/PR you can apply.
