# spec.md — EPM Business Rule Documentation Generator

**Version:** 0.2 (MVP, revised after review) · **Status:** Approved for build · **Related:** PRD – EPM Business Rule Documentation Generator, `architecture.md`

## 1. Summary

A web app that takes one Oracle EPM business rule (Essbase/Planning calc script or Groovy rule), extracts its structure with code, and uses an LLM to produce:

1. A **structured technical document** (fixed sections, export-ready).
2. A **"Teach me" view** that explains the rule line by line.

It is not a chatbot: rule in → structured document out.

## 2. User flow

1. User opens the app (no login).
2. User pastes a rule or uploads a file (`.txt`, `.csc`, `.groovy`).
3. Optional: user switches on **Mask member names**.
4. User clicks **Generate**.
5. App shows three tabs:
   - **Documentation** – the structured document (editable text areas).
   - **Extracted facts** – FIX statements, members, run-time prompts, functions found by the parser.
   - **Teach me** – table of code line → plain-English meaning.
6. User clicks **Download .md** or **Download .docx**.

## 3. Functional requirements

| ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-1 | Accept rule input | Paste box or file upload; UTF-8 text; max **2,000 lines**; warning banner above **1,000 lines**; reject empty input or binary files with a clear message |
| FR-2 | Detect rule type | Classify as `calc_script` or `groovy` (rules in §6.1); user can override with a dropdown |
| FR-3 | Extract facts with code (no AI) | Parser returns FIX blocks (with nesting depth and line numbers), quoted members, run-time prompt variables, `@` functions, calc commands (`AGG`, `CALC DIM`, `DATACOPY`, `CLEARDATA`, `SET …`) |
| FR-4 | Mask member names (optional) | Quoted members and user-listed names replaced with tokens (`MBR_001` …) before the LLM call; tokens restored in the output; mapping kept in memory only |
| FR-5 | Generate documentation | LLM returns JSON matching the schema in §5; app validates it; on failure, retry once, then show an error |
| FR-6 | Generate "Teach me" view | One row per meaningful code line (skip blank lines and pure comments); max 2,000 rows; **if this call fails, the documentation is still shown with a notice** |
| FR-7 | Show extracted facts beside AI output | Extracted-facts tab always rendered from the parser, so users can verify the AI text |
| FR-8 | Edit before export | Purpose is an editable text area; table sections are editable grids (add/remove rows) |
| FR-9 | Export | `.md` and `.docx` downloads; file name `<rule_name>_documentation.<ext>`; footer "AI-generated draft – review required" |
| FR-10 | Privacy | No rule text, output or masking map is written to disk, logs or a database |
| FR-11 | Demo mode | With no API key (or `LLM_PROVIDER=mock`), the app runs end to end: parser facts are real, AI sections show labelled placeholders |
| FR-12 | Usage monitoring | Each generation logs one JSON line (outcome, duration, rule type, line count, masked flag, provider) and updates a sidebar panel: runs, success rate, average time |

## 4. Non-functional requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-1 | Response time | < 30 s up to 300 lines; < 90 s up to 2,000 lines |
| NFR-2 | Cost | Small/fast model; input capped at 2,000 lines; identical inputs served from an in-memory cache |
| NFR-3 | Reliability | JSON schema validation on every LLM response |
| NFR-4 | Security | API key only in environment variables; never logged; HTTPS via hosting provider |
| NFR-5 | Quality | Unit tests for validator, detector, parsers, masking, LLM retries, pipeline, exporters and monitoring run in CI on every push |
| NFR-6 | Accessibility | Works in current Chrome and Edge; readable at 1366 px width |
| NFR-7 | Secret safety | Secret scanning (gitleaks) on every push; `.env` git-ignored; only `.env.example` committed |
| NFR-8 | Availability | Host health check on `/_stcore/health`; host restarts the app if it stops answering |

## 5. AI module design

### 5.1 Model and settings
- **Provider:** configurable via env var `LLM_PROVIDER`: `gemini` or `groq` (free tiers, via their OpenAI-compatible endpoints), `anthropic`, `openai`, or `mock` for tests and demo mode.
- **Model:** a small, fast model (deployed default `gemini-3.5-flash`; e.g. `claude-haiku-5-5` on Anthropic), set by `LLM_MODEL`.
- **Temperature:** 0.2 (consistent, factual output).
- **Max output tokens:** 8,000.
- **Two calls per rule:** (1) documentation, (2) "Teach me". Run in parallel.
- **Masking:** when on, the parser is re-run on the masked text so the facts sent to the model are masked too; names are restored after validation.

### 5.2 Prompt inputs
Each call receives:
1. **System prompt** – role ("senior Oracle EPM technical consultant"), rules ("use only what is in the code; if unsure, say 'Not determinable from the rule'"), output format (JSON only).
2. **Extracted facts** from the parser (FR-3) as JSON – grounds the model.
3. **Rule text** (masked if FR-4 is on), with line numbers.

### 5.3 Documentation output schema
```json
{
  "rule_name": "string",
  "rule_type": "calc_script | groovy",
  "purpose": "string (2-4 sentences)",
  "pov_fix_scope": [{"dimension": "string", "members": "string", "source_lines": "string"}],
  "dimensions_and_members": [{"dimension": "string", "members_read": "string", "members_written": "string"}],
  "runtime_prompts": [{"name": "string", "purpose": "string"}],
  "logic_steps": [{"step": 1, "description": "string", "source_lines": "string"}],
  "risks_and_performance_notes": [{"severity": "high | medium | low", "note": "string"}],
  "confidence": "high | medium | low"
}
```

### 5.4 "Teach me" output schema
```json
{
  "lines": [{"line_no": 1, "code": "string", "explanation": "string", "concept": "string (e.g., FIX, cross-dim operator, @RELATIVE)"}]
}
```

### 5.5 Guardrails
- Facts from the parser are passed in; the model is told not to contradict them.
- After generation, the app checks that every **quoted** member named in `pov_fix_scope` exists in the parser output; mismatches are flagged in the UI with a warning. (Unquoted names are not checked — known limitation.)
- Output always labelled **"AI-generated draft – review required"**.

## 6. Parser rules (code, not AI)

### 6.1 Rule type detection
- `groovy` if the text contains any of: `operation.`, `def `, `/*RTPS:`, `import ` (at line start), a closure parameter `{ x ->`, `.each {`.
- A bare `->` is **not** a Groovy signal: it is the calc script cross-dimensional operator (`"Actual"->"Jan"`).
- Otherwise `calc_script`.

### 6.2 Calc script extraction
| Item | Pattern (simplified) |
|---|---|
| FIX blocks | `FIX\s*\((.*?)\)` … matching `ENDFIX`; track depth with a stack |
| Members | Text in double quotes `"…"` |
| Run-time prompts | `{VarName}` and `&SubVar` |
| Functions | `@[A-Z]+\(` |
| Commands | `AGG`, `CALC DIM`, `CALC ALL`, `DATACOPY`, `CLEARDATA`, `CLEARBLOCK`, `SET \w+` |
| Comments | `/* … */` and `//` lines (kept for context, skipped in "Teach me") |

### 6.3 Groovy extraction
| Item | Pattern (simplified) |
|---|---|
| RTPs | `rtps.\w+` and `/*RTPS: … */` header |
| Embedded calc | Triple-quoted strings `""" … """` containing `FIX(` – run through the calc script parser. Line numbers are relative to the embedded string (shown as a warning) |
| Grid / data map calls | `operation.grid`, `getDataMap`, `executeDataMap`, `operation.application.getDimension` |

## 7. Out of scope (MVP)
Batch upload or LCM snapshots · HFM/FCCS rules · data maps and forms · dependency map · live EPM connection via REST · user accounts and history · non-English output.

## 8. Test plan

37 automated tests (`pytest -q`), all run in GitHub Actions with the mock provider.

| Test | File | Pass condition |
|---|---|---|
| Nested FIX scopes, depth and line numbers | `test_parser_calc.py` | Outer FIX lines 6–16, inner 7–12 on the sample |
| Members, RTPs, substitution variables, functions, commands | `test_parser_calc.py` | Match expected values |
| Comments ignored without shifting line numbers; unbalanced FIX warned | `test_parser_calc.py` | As stated |
| Groovy RTPs, API calls, embedded calc script | `test_parser_groovy.py` | As stated |
| Type detection on 10 samples (incl. cross-dim `->` in calc) | `test_detector_validator.py` | 10/10 correct |
| Empty, binary, line limits, Windows line endings | `test_detector_validator.py` | 2,001 lines rejected; 1,001 warned |
| Masking round-trip, extra names, nested unmask | `test_masker.py` | Restored text equals original |
| LLM retry once, fail after two bad answers, code fences stripped | `test_llm_and_pipeline.py` | As stated |
| Full pipeline (with and without masking) and exporters | `test_llm_and_pipeline.py` | All sections present; no tokens left |
| Monitoring counts and logs; **logs contain no rule text** | `test_telemetry.py` | As stated |
| Gemini / Groq endpoints, model override, demo fallback | `test_providers.py` | As stated |
| Accuracy on 5 sample rules | Manual review | Average reviewer score ≥ 4/5 |

Sample rules live in `tests/samples/` and use Oracle sample-application style names only (no client data).

## 9. Definition of done (MVP)
- All FR items implemented; tests passing in GitHub Actions.
- Deployed to a public URL.
- README explains setup, environment variables and privacy behaviour.
- 2-minute demo recorded using a sample rule.

## 10. Review and change log

The v0.1 spec was reviewed against the first working build (code walkthrough + running every test). Changes:

| # | Finding in review | Change in v0.2 |
|---|---|---|
| 1 | Detecting Groovy by a bare `->` would misclassify calc scripts, because `->` is the cross-dimensional operator | §6.1: only a closure parameter `{ x ->` counts; regression test added |
| 2 | No way to try the app or run CI without an API key | FR-11 demo mode; `mock` provider |
| 3 | Brief requires monitoring; v0.1 had none | FR-12 usage log + sidebar stats (metadata only); NFR-8 health check |
| 4 | Brief requires a secrets check; v0.1 relied on `.gitignore` only | NFR-7 gitleaks secret scanning in CI |
| 5 | If "Teach me" failed, the whole run failed | FR-6: documentation still shown, with a notice |
| 6 | v0.1 did not say the extracted facts sent to the AI must also be masked; otherwise names would leak through them | §5.1: parser re-run on masked text |
| 7 | Cross-check and embedded-FIX line numbers have limits not stated | §5.5 and §6.3 now state them |
| 8 | Recommended stack is Next.js + Vercel | Kept Python + Streamlit + Render: faster to learn and ship for a non-developer; core logic is UI-independent so a Next.js front end can be added in v2 (see `architecture.md` §5, §9) |
| 9 | Test plan listed planned tests, not actual ones | §8 now lists the implemented tests |
| 10 | Paid API key is a barrier for a student project | §5.1: free Gemini / Groq providers via OpenAI-compatible endpoints (`tests/test_providers.py`) |
