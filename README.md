# EPM Business Rule Documentation Generator

![CI](https://github.com/<your-username>/epm-rule-doc-generator/actions/workflows/ci.yml/badge.svg)

Turns an Oracle EPM business rule (Essbase / Planning calc script or Groovy) into a **structured technical document** and a **line-by-line "Teach me" explanation**, with export to Markdown and Word. Built for EPM consultants who inherit undocumented applications.

| | |
|---|---|
| **Live app** | `<add your Render URL>` |
| **Demo video (2 min)** | `<add your video link>` |
| **v2 issue** | `<add your GitHub issue link>` |

> ⚠️ Use sample or anonymised rules only. Nothing is stored, but rule text is sent to the AI provider. Turn on **Mask member names** for anything from a real project. Output is an AI-generated draft and must be reviewed.

## Project documents

| Deliverable | File |
|---|---|
| Idea validation (7 steps) | [`docs/idea-validation-report.md`](docs/idea-validation-report.md) |
| 1-page PRD | [`docs/PRD.md`](docs/PRD.md) |
| Spec (v0.2, revised after review) | [`spec.md`](spec.md) |
| Architecture notes | [`architecture.md`](architecture.md) |
| AI assistant rules | [`CLAUDE.md`](CLAUDE.md), [`.cursorrules`](.cursorrules) |
| Reflection | [`docs/reflection.md`](docs/reflection.md) |
| Demo script | [`docs/demo-script.md`](docs/demo-script.md) |
| Submission checklist | [`docs/SUBMISSION.md`](docs/SUBMISSION.md) |

## How it works

1. **Code reads the rule** – finds FIX blocks (with nesting and line numbers), quoted members, run-time prompts, substitution variables, `@` functions and calc commands. No AI involved.
2. **AI writes the explanation** – the rule *and* the extracted facts go to the LLM, which must answer in a fixed JSON format (validated, retried once if wrong).
3. **Code checks the AI** – any member the AI mentions that the parser did not find is flagged.

## Run it locally

Requires Python 3.12+.

```bash
git clone https://github.com/<your-username>/epm-rule-doc-generator.git
cd epm-rule-doc-generator
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
streamlit run app.py
```

With no API key in `.env`, the app runs in **demo mode**: parsed facts are real, AI sections show placeholders. Put your key in `LLM_API_KEY` to switch on the AI.

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` | `anthropic`, `openai` or `mock` |
| `LLM_MODEL` | `claude-haiku-5-5` | Model name for the chosen provider |
| `LLM_API_KEY` | – | API key (secret; never commit) |
| `MAX_LINES` | `2000` | Maximum rule length |
| `WARN_LINES` | `1000` | Show a warning above this length |
| `LLM_TIMEOUT_SECONDS` | `90` | Timeout per AI call |

## Security

- Secrets only in environment variables (Render dashboard / local `.env`, which is git-ignored).
- **gitleaks** scans every push for leaked keys.
- Input validation: empty, binary and over-length inputs rejected (`core/validator.py`).
- Rule text is never written to disk or logs; a unit test enforces this.

## Monitoring

- One JSON log line per generation (outcome, duration, rule type, line count) → Render **Logs**.
- Sidebar shows runs, success rate and average time since the last restart.
- Render **Metrics** for CPU/memory; health check on `/_stcore/health`.

## Tests and CI

```bash
pytest -q        # 33 tests, no API key needed (AI is mocked)
ruff check .     # lint
```

GitHub Actions (`.github/workflows/ci.yml`) runs secret scanning, lint and tests on every push and pull request to `main`.

## Deploy to Render

1. Push this repo to GitHub (public).
2. In [Render](https://render.com): **New → Blueprint** → select the repo (it reads `render.yaml`).
3. Enter your `LLM_API_KEY` when asked.
4. Every push to `main` redeploys automatically.

## Commit plan (first push)

```bash
git init && git branch -M main
git add .gitignore README.md spec.md architecture.md docs/ CLAUDE.md .cursorrules && git commit -m "Add validation report, PRD, spec, architecture and AI assistant rules"
git add core/validator.py core/detector.py core/schemas.py && git commit -m "Add input validation, rule type detection and data models"
git add core/parser_calc.py core/parser_groovy.py core/masker.py && git commit -m "Add calc script and Groovy parsers with member masking"
git add core/ && git commit -m "Add LLM client, prompts, cross-checks, exporters, pipeline and monitoring"
git add app.py .streamlit/ && git commit -m "Add Streamlit UI with usage sidebar"
git add tests/ pyproject.toml requirements.txt .github/ && git commit -m "Add 33 tests and GitHub Actions CI with secret scanning"
git add render.yaml .env.example && git commit -m "Add Render deployment config and env template"
git remote add origin https://github.com/<your-username>/epm-rule-doc-generator.git
git push -u origin main
```

## Tech choices

Python + Streamlit + Render instead of the course's suggested Next.js + Vercel: faster to learn and ship for a consultant new to coding, and Streamlit gives tables, uploads and downloads out of the box. All logic lives in `core/`, independent of the UI, so a Next.js front end can be added later (see `architecture.md` §9).

## Project structure

```
app.py              Streamlit screen (no business logic)
core/               validator, detector, parsers, masker, prompts, LLM client, checks, exporters, telemetry, pipeline
tests/              pytest tests + sample rules (no client data)
docs/               validation report, PRD, reflection, demo script, v2 issue, submission checklist
.github/workflows/  CI pipeline
render.yaml         deployment config
```

## Limitations (MVP)

One rule at a time · calc scripts and Groovy only (no HFM/FCCS) · English only · parser uses simple patterns and may miss unusual syntax · usage stats reset on restart · no saved history.
