# CLAUDE.md — instructions for AI coding assistants

This file tells Claude (and other AI coding agents) how to work in this repo.
Read `spec.md` and `architecture.md` before changing code.

## What this project is
A Streamlit web app that turns one Oracle EPM business rule (Essbase/Planning calc script or
Groovy) into structured technical documentation plus a line-by-line "Teach me" view.
Users are EPM consultants. It is **not a chatbot**: rule in → structured document out.

## Golden rules
1. **Code finds facts, AI writes explanations.** Anything that must be exact (FIX scopes,
   members, run-time prompts, line counts) is extracted by `core/parser_*.py`, never by the LLM.
2. **Keep `app.py` thin.** UI only. All logic goes in `core/`. New logic needs a unit test.
3. **Never hardcode secrets.** Keys come from environment variables (`LLM_API_KEY`). Never
   print, log or commit them. `.env` is git-ignored; only `.env.example` is committed.
4. **Never store or log rule text.** Logs carry metadata only (rule type, line count, duration,
   success). See `core/telemetry.py`.
5. **LLM output must validate.** Every LLM answer goes through the Pydantic models in
   `core/schemas.py`. If you change an output field, update the schema, the prompt, the
   exporters and the tests together.
6. **Tests never call a real LLM.** `tests/conftest.py` forces `LLM_PROVIDER=mock`.
7. **Use only sample rules.** Test data lives in `tests/samples/` with Vision-style member
   names. Never add client rules.

## Commands
```bash
pip install -r requirements.txt   # install
streamlit run app.py              # run locally (demo mode if no API key)
pytest -q                         # tests
ruff check .                      # lint (must pass before commit)
```

## Code style
- Python 3.12, type hints on public functions, docstrings that explain *why*.
- Small, readable functions; regex patterns named and commented.
- Ruff settings in `pyproject.toml` (line length 110).
- Plain-English, friendly error messages for users; no stack traces in the UI.

## Where things live
| Need to change… | Edit |
|---|---|
| Input limits / validation | `core/validator.py` |
| Calc script or Groovy parsing | `core/parser_calc.py`, `core/parser_groovy.py` |
| Prompts | `core/prompts.py` |
| LLM provider, retries, cache | `core/llm_client.py` |
| Output fields | `core/schemas.py` (+ prompts, exporters, tests) |
| Export format | `core/exporters.py` |
| Usage logging / stats | `core/telemetry.py` |
| Screen layout | `app.py` |

## Definition of done for any change
- `ruff check .` and `pytest -q` pass locally and in GitHub Actions.
- `spec.md` updated if behaviour changed (add a line to its change log).
- One focused commit with a message that says what changed and why.
