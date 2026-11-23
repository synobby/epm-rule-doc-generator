# Idea Validation Report – EPM Business Rule Documentation Generator

Nov 21, 2026 · Nobby

## Idea summary

**Verdict: worth building as a small MVP.** The problem is real and Oracle does not cover it natively today. The main risks are client data confidentiality and the accuracy of the AI output.

**The tool:** A web app where an Oracle EPM consultant pastes or uploads a business rule (an Essbase calc script, a Planning business rule, or a Groovy rule). The app returns a standard technical document: the rule's purpose, POV / FIX scope, dimensions and members touched, run-time prompts, a step-by-step logic flow, and performance or risk warnings. The result exports as Markdown or Word for a design document or handover pack. It is not a chatbot: rule in, structured document out.

> Placeholders marked **[ADD: …]** are evidence only the author can supply (interview quotes, numbers, project examples).

**Idea history:** the first candidate, an AI variance commentary generator, was dropped at Step 4 because Oracle already ships GenAI narrative commentary (Describe, Compare, Causality) in Narrative Reporting and Reports.

## Step 1 – Is the problem real?

**Yes. Business rules are the least-documented part of most EPM applications, and understanding them is slow, manual work.**

- **Inherited applications.** A consultant joining a support contract or a phase-2 project finds dozens to hundreds of rules with no or outdated documentation.
- **Handovers.** When a consultant rolls off, knowledge of what each rule does leaves with them.
- **Design documents.** Technical design documents need a rule-by-rule description, typically written by hand at the end of a project.
- **Learning curve.** Junior and functional consultants moving into technical work struggle to read FIX statements, cross-dimensional operators and Groovy.
- **Troubleshooting.** When numbers look wrong, the first step is working out which rules write to that intersection.

**Evidence:**

- [ ] Interviews with 5 EPM colleagues: *"Think of the last application you inherited. How long did it take to understand the rules? Was there documentation?"* **[ADD: quotes and time estimates]**
- [ ] Undocumented rules in one past project (anonymised). **[ADD: e.g., "38 of 52 rules had no description"]**
- [ ] Hours spent writing rule documentation for one design document. **[ADD: hours]**
- [ ] 2–3 public forum / Customer Connect posts asking "what does this calc script do?" **[ADD: links]**

## Step 2 – Who is the target user?

**Primary user: Oracle EPM implementation and support consultants** who inherit, review or hand over Planning, FreeForm or Essbase applications.

| Segment | Role | Main job to be done | Priority |
| --- | --- | --- | --- |
| Primary | EPM technical / functional consultant | Understand an inherited rule fast and produce design-document text | MVP focus |
| Secondary | Junior or functional consultant learning to code | Learn what calc script and Groovy syntax does, line by line | MVP focus |
| Tertiary | Client EPM administrator | Keep rule documentation current after go-live | Later |

**Persona – "Mia, EPM consultant, 3 years' experience":** strong on functional design, less confident in Groovy. Just assigned to a support contract with 60 undocumented business rules and a two-week handover. Today she reads each rule line by line and writes notes in Word.

## Step 3 – Is the market meaningful?

**Meaningful as a niche, not a mass market.** The users are a specialised professional group, and each spends many hours a year on rule analysis — a good fit for a focused productivity tool and for an internal tool at a consulting firm.

- Oracle Cloud EPM is used by large organisations across industries and regions, including the Philippines (e.g., Aboitiz Power, 2023 — [Apps Run The World](https://www.appsruntheworld.com/customers-database/products/view/oracle-cloud-epm)).
- Every Planning, FreeForm or Essbase application carries business rules; many also carry legacy on-premises Hyperion rules that must be understood during cloud migrations.
- Implementations are delivered and supported by consulting partners whose consultants rotate between projects often.

| Input | Value | Source |
| --- | --- | --- |
| EPM consultants in my firm / network | [ADD] | Firm headcount or LinkedIn |
| Applications inherited or handed over per consultant per year | [ADD, e.g., 2] | Interviews |
| Hours understanding and documenting rules per application | [ADD, e.g., 20] | Interviews |
| Hours saved if the tool cuts that by 50% | consultants × apps × hours × 0.5 | Calculated |

**Example:** 30 consultants × 2 apps × 20 hours × 0.5 = **600 hours saved per year in one firm.** Replace with real numbers.

## Step 4 – What competitors already exist?

**No direct competitor documents EPM business rules with AI. The real competition is manual work and general-purpose chat AI.**

| Alternative | What it does | Gap for our user |
| --- | --- | --- |
| Manual reading + Word notes | Consultant reads each rule and writes documentation | Slow, inconsistent, depends on skill |
| ChatGPT / Claude / Copilot (general chat) | Explains pasted code if prompted well | No EPM structure, different format each time, no design-doc export |
| Oracle EPM Assistants (26.04, AI Agent Studio) | Agent templates that retrieve data, trigger actions and automate EPM interactions via REST ([Oracle EPM AI features](https://docs.oracle.com/en/cloud/saas/enterprise-performance-management-common/epmai/)) | Conversational, aimed at live applications; needs Fusion AI Agent Studio; no rule documentation |
| Oracle GenAI narratives (Narrative Reporting / Reports) | Commentary on financial data (Describe, Compare, Causality) | Explains numbers, not rule logic |
| Calculation Manager (native) | Shows the rule and graphical flow; has a description field | Description is manual and often blank |
| Consulting firm templates | Standard design-document templates | Still filled in by hand |

**Watch item:** Oracle ships monthly updates; re-check the latest EPM *What's New* before submission. **[ADD: date checked]**

## Step 5 – What is our edge?

**EPM domain knowledge built into a fixed, structured output: a design-document section, not a chat reply.**

1. **Built by an EPM consultant** — sections match what EPM design documents need (POV/FIX scope, dimensions, run-time prompts, aggregation steps).
2. **Same structure every time** — schema-validated JSON output, so 60 rules produce one consistent document.
3. **Rule-aware pre-processing** — code extracts FIX statements, members and run-time prompts before the AI writes, and flags AI claims it cannot verify.
4. **Teaching mode** — line-by-line explanations help consultants learn calc script and Groovy.
5. **No Oracle licence or agent setup** — works on rule text alone: Cloud EPM, on-prem Hyperion and migrations.
6. **Export-ready** — one click to Markdown or Word.

## Step 6 – How do we run a cheap validation test?

**A one-week "Wizard of Oz" test before writing app code.**

1. Prepare 5 sample rules (no client data): simple calc, FIX + cross-dimensional, Groovy.
2. Generate the documents with one fixed prompt and the planned template.
3. Ask 3–5 EPM colleagues to score each document against the rule (1–5).
4. Time manual documentation of one rule vs reviewing the AI version.
5. Ask: *"Would you use this on your next handover?"*

| Metric | Target to proceed |
| --- | --- |
| Reviewer accuracy score (1–5) | Average ≥ 4 |
| Time vs manual | ≥ 50% faster |
| Colleagues who would use it | ≥ 3 of 5 |
| Critical errors (wrong scope / dimension) | 0 on simple rules; ≤ 1 on complex |

**Cost:** close to zero. **[ADD: results table]**

## Step 7 – What are the biggest failure risks?

| Risk | Why it matters | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Client confidentiality | Rules contain client names and logic; firms may ban external AI | High | Sample/anonymised rules; member masking; no storage; later a firm-approved AI endpoint |
| Wrong or invented explanations | A wrong FIX scope misleads the client | Medium | Code extracts facts first and cross-checks the AI; "draft – review required" label |
| Complex or very long rules | AI quality drops on long nested rules | Medium | 2,000-line cap with warning; splitting in v2 |
| Low adoption ("I'll just use ChatGPT") | Not enough added value | Medium | Consistent template + export; prove time saved |
| Oracle adds native rule documentation | Gap could close | Low–medium | Stay lightweight and platform-agnostic |
| API cost | Student budget | Low | Small model, cache, input cap |

## Verdict

**Proceed.** Real problem, clear user group, no direct competitor, and a scope small enough to build and deploy within the assignment. MVP: one rule in → structured documentation + "Teach me" view → Markdown/Word export.

## Sources

- [Oracle Cloud EPM – Features with AI](https://docs.oracle.com/en/cloud/saas/enterprise-performance-management-common/epmai/)
- [EPM Assistants for Planning](https://docs.oracle.com/en/cloud/saas/enterprise-performance-management-common/epmai/epm_assistants_for_planning.html)
- [Oracle EPM Assistants with AI Agent Studio (Hyperion Architect blog, Apr 2026)](http://hyperionarchitect.blogspot.com/2026/04/oracle-epm-assistants-with-ai-agent.html)
- [Support for Generative AI Narrative Summaries (EPM What's New, Jun 2026)](https://docs.oracle.com/en/cloud/saas/readiness/epm/2026/epm-jun26/26jun-epm-wn-f49621.htm)
- [Oracle Cloud EPM customers (Apps Run The World)](https://www.appsruntheworld.com/customers-database/products/view/oracle-cloud-epm)
