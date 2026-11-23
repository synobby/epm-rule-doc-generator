# PRD – EPM Business Rule Documentation Generator

Nov 21, 2026 · Nobby

A web app that turns an Oracle EPM business rule (calc script or Groovy) into a structured, export-ready technical document and a line-by-line explanation, in under a minute.

## 1. Problem statement

EPM consultants who inherit or hand over an application spend hours reading undocumented business rules line by line, then writing descriptions by hand. Calculation Manager's description field is usually blank, and general chat AI gives a different, unstructured answer every time. The result is slow handovers, inconsistent design documents, and a steep learning curve for consultants who are new to calc scripts and Groovy.

## 2. Target users

- **Primary – EPM implementation / support consultant:** needs to understand an inherited rule fast and produce design-document text.
- **Secondary – junior or functional consultant learning to code:** needs a line-by-line explanation of calc script and Groovy syntax.
- **Later – client EPM administrator:** keeps rule documentation current after go-live.

## 3. Goals and success metrics

| Goal | Metric | Target (MVP) |
| --- | --- | --- |
| Save time | Time to produce reviewed documentation for one rule vs manual | ≥ 50% faster |
| Be accurate | Reviewer accuracy score (1–5) on test rules | Average ≥ 4; 0 wrong FIX scopes on simple rules |
| Be consistent | Outputs that follow the fixed template | 100% |
| Be fast | Time from "Generate" to result | < 30 seconds up to 300 lines; < 90 seconds up to 2,000 lines |
| Be useful | Test users who would use it on their next handover | ≥ 3 of 5 |

## 4. Core features (MVP)

| # | User story | Acceptance criteria | Priority |
| --- | --- | --- | --- |
| F1 | As a consultant, I paste or upload a rule (.txt, .csc, .groovy) so I can document it | Accepts up to 2,000 lines; shows a warning above 1,000 lines that results may be slower and less precise; detects calc script vs Groovy automatically | Must |
| F2 | As a consultant, I get a structured document so I can drop it into a design doc | Fixed sections: Purpose, POV/FIX scope, Dimensions & members, Run-time prompts, Step-by-step logic, Risks & performance notes | Must |
| F3 | As a consultant, I see extracted FIX statements, members and RTPs beside the AI text so I can verify accuracy | Extraction done by code (not AI) and shown in its own tab | Must |
| F4 | As a learner, I switch to "Teach me" view so I understand each line | Line-by-line table: code line → plain-English meaning | Must |
| F5 | As a consultant, I export the result so I can use it in a handover pack | Download as Markdown and Word (.docx) | Must |
| F6 | As a consultant, I mask member names before sending so client data stays private | Optional toggle replaces member names with placeholders and restores them in the output | Should |
| F7 | As a consultant, I edit the generated text before export | Inline editing of each section | Could |

## 5. Scope

| In scope (MVP) | Out of scope (later versions) |
| --- | --- |
| One rule at a time, pasted or uploaded | Batch upload of a whole application or LCM snapshot |
| Essbase / Planning calc scripts and short Groovy rules | HFM / FCCS rules, Data Management mappings, forms |
| Structured documentation + "Teach me" view | Dependency map and impact analysis across rules |
| Markdown and Word export | Connecting to a live EPM instance via REST API |
| Single-user web app, no login | User accounts, saved history, team sharing |
| English output | Other languages |

## 6. Constraints, assumptions and risks

**Constraints:** Uses sample or anonymised rules only; no client data is stored (rules are processed in memory and discarded). Hosted on a free tier (Render) with one LLM API. Built and deployed within the course timeline.

**Assumptions:** Consultants are allowed to use the tool on masked or sample rules. A 2,000-line cap covers almost all single business rules.

**Risks and mitigations:**

- **AI explains a rule wrongly** → code-based extraction shown beside the AI text (F3); output labelled "Draft – review required".
- **Client confidentiality** → member masking (F6), no storage, clear privacy note on the page.
- **Long or complex rules** → 2,000-line cap with a warning above 1,000 lines; automatic splitting by FIX block or Groovy method in a later version.
- **API cost** → small model, input length cap, cached results for repeat inputs.
