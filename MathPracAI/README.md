# MathPracAI

A soft, code-font Algebra 2 practice generator powered by Python.

## Run Locally

From this folder, run:

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

Then open:

```text
http://localhost:8010
```

## Architecture Notes

- `app.py` creates the Flask app and registers route blueprints.
- `routes/practice_routes.py` handles practice/test request flow.
- `routes/auth_routes.py` handles login, logout, and signup.
- `routes/dashboard_routes.py` handles tutor/admin dashboards, profiles, workspaces, and code endpoints.
- `views/auth_views.py`, `views/dashboard_views.py`, and `views/shared_views.py` handle HTML rendering helpers.
- `firebase_backend/config.py` initializes Firebase Admin SDK and Firestore.
- `firebase_backend/auth_service.py`, `firebase_backend/firestore_service.py`, and `firebase_backend/code_service.py` keep backend logic out of route files.
- `math_engine/generators.py` handles problem generation.
- `math_engine/models.py` handles the `Problem` object and serialization.
- `math_engine/validators.py` handles answer validation.
- `math_engine/renderers.py` handles practice/test HTML rendering.
- `math_engine/formatters.py` handles math text formatting.
- `static/script.js` handles browser-side interactions.
- `static/styles.css` handles styling.

## Firebase Environment

Set these before running against Firebase:

```bash
export FIREBASE_WEB_API_KEY="..."
export FIREBASE_SERVICE_ACCOUNT_PATH="/path/to/service-account.json"
export MATHPRACAI_SECRET_KEY="replace-in-production"
```

`FIREBASE_SERVICE_ACCOUNT_JSON` can be used instead of `FIREBASE_SERVICE_ACCOUNT_PATH`.
