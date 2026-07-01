# MathPracAI

A soft, code-font Algebra 2 practice generator powered by Python.

## Run Locally

From this folder, run:

```bash
python3 app.py
```

Then open:

```text
http://localhost:8010
```

## Architecture Notes

- `app.py` handles HTTP routing and request flow.
- `generators.py` handles problem generation.
- `models.py` handles the `Problem` object and serialization.
- `validators.py` handles answer validation.
- `renderers.py` handles HTML rendering.
- `formatters.py` handles math text formatting.
- `script.js` handles browser-side interactions.
- `styles.css` handles styling.
