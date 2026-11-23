# Submission checklist — Graded Assignment 4.2

✅ = done in this repo · 👤 = you must do it (needs your accounts, keys or voice)

## Project constraints

| Requirement | Status | Where |
|---|---|---|
| Solves a real problem for a specific user | ✅ | `docs/idea-validation-report.md` (EPM consultants inheriting undocumented rules) |
| At least one AI capability | ✅ | `core/llm_client.py`, `core/prompts.py` — structured documentation + "Teach me" |
| Usable web UI | ✅ | `app.py` (Streamlit) |
| Deployed to a live URL | 👤 | Render — see README "Deploy to Render" |
| Public GitHub repo | 👤 | Create it as **Public** |
| GitHub Actions workflow | ✅ | `.github/workflows/ci.yml` (secret scan + lint + 48 tests) |
| No hardcoded secrets | ✅ | Env vars only; `.env` ignored; gitleaks in CI |
| Proper README | ✅ / 👤 | `README.md` — add your live URL, demo link, issue link |

## Phase 1 – Validate and define
| Task | Status | Where |
|---|---|---|
| All 7 validation steps | ✅ / 👤 | `docs/idea-validation-report.md` — fill the **[ADD]** evidence (interviews, numbers) |
| User, problem, market evidence | ✅ / 👤 | Same file, Steps 1–3 |
| Differentiating angle | ✅ | Same file, Step 5 |
| 1-page PRD | ✅ | `docs/PRD.md` |

## Phase 2 – Spec and architecture
| Task | Status | Where |
|---|---|---|
| Architecture notes | ✅ | `architecture.md` |
| spec.md | ✅ | `spec.md` |
| CLAUDE.md or agents.md | ✅ | `CLAUDE.md` |
| .cursorrules | ✅ | `.cursorrules` |
| Revise spec after review | ✅ | `spec.md` v0.2, §10 review and change log |

## Phase 3 – Build
| Task | Status | Where |
|---|---|---|
| Scaffold the application | ✅ | Whole repo |
| Core AI feature | ✅ | `core/pipeline.py` |
| ≥ 5 meaningful commits | 👤 | Use the commit sequence in README "Commit plan" |
| ≥ 3 unit tests | ✅ | 48 tests in `tests/` |
| Secrets and input validation | ✅ | `core/validator.py`, gitleaks job, `.gitignore` |

## Phase 4 – Deploy
| Task | Status | Where |
|---|---|---|
| Configure GitHub Actions | ✅ | `ci.yml` — 👤 confirm the green tick after first push |
| Deploy to a live host | 👤 | Render Blueprint (`render.yaml`) |
| Set environment variables | 👤 | Enter `LLM_API_KEY` in Render when asked |
| Test the live app | 👤 | Incognito window; load sample rule; Generate; download .docx |
| Basic monitoring / analytics | ✅ | `core/telemetry.py` → Render Logs + sidebar stats; health check in `render.yaml` |

## Phase 5 – Document and reflect
| Task | Status | Where |
|---|---|---|
| Complete README | ✅ / 👤 | Add the three links |
| 2-minute demo | 👤 | Follow `docs/demo-script.md` |
| 1-page reflection | ✅ / 👤 | `docs/reflection.md` — fill the two **[ADD]** lines after deploying |
| GitHub issue for v2 | 👤 | Paste `docs/v2-issue.md` into GitHub → Issues → New issue |

## Before you submit (from the brief)
- [ ] Live URL works in an **incognito** window
- [ ] GitHub repo is public and opens when logged out
- [ ] Actions tab shows green ticks
- [ ] No secrets in the repo (gitleaks job is green; `.env` not committed)
- [ ] Demo link opens in incognito
- [ ] Reflection attached or linked (`docs/reflection.md`)
- [ ] All [ADD] placeholders filled
