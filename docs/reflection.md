# Reflection — EPM Business Rule Documentation Generator

**Author:** Nobby · **Course:** AIM Gen AI and Agentic AI, Week 4 · **Live app:** [ADD: URL] · **Repo:** [ADD: URL]

## What I built and why
As an Oracle EPM consultant, I often inherit applications whose business rules have no documentation. I built a web app that takes one calc script or Groovy rule and returns a structured technical document plus a line-by-line "Teach me" view, exportable to Word or Markdown. It saves time on handovers and helps consultants like me learn to read code.

## Key learnings
1. **Validate before building.** My first idea, an AI variance commentary generator, failed the competitor step: Oracle already ships GenAI narratives in Narrative Reporting and Reports. Checking the release notes saved me from building something Oracle gives customers for free. Rule documentation had a clear gap.
2. **Let code do the exact work and AI do the writing.** The parser finds FIX scopes, members and run-time prompts deterministically. The AI only explains. This made the output easier to trust and to test, and it lets the app flag members the AI mentions that are not in the rule.
3. **Structured output beats chat.** Forcing the model to return JSON that matches a schema gave the same sections every time. A validation-and-retry step handled the occasional bad answer.
4. **Specs and tests are worth it for a non-developer.** Writing `spec.md` first, plus 37 automated tests, let me change code with confidence. CLAUDE.md and `.cursorrules` kept AI coding tools inside the rules I set.

## Challenges
- **Domain edge cases.** The first type detector treated `->` as Groovy, but in calc scripts it is the cross-dimensional operator. A unit test caught it, and I added it to the spec review.
- **Confidentiality.** Real rules contain client member names. I added optional masking, a no-storage design, and a test proving rule text never reaches the logs.
- **Scope pressure.** I limited the MVP to one rule at a time (2,000 lines max) and resisted adding batch upload, accounts or a database.
- **Learning the toolchain.** Git, GitHub Actions and Render were new to me. [ADD: one specific thing that tripped you up and how you fixed it.]
- **Live testing.** [ADD: what you saw when you tested the live app with a real API key, e.g., response time, any wrong explanations.]

## Improvements for future versions
- **Whole-application mode:** upload an LCM snapshot and document every rule, with a dependency map of which rule writes to which intersection (logged as a GitHub issue).
- **Automatic splitting** of very long rules by FIX block or Groovy method.
- **More rule types:** FCCS/HFM rules, Data Integration mappings and forms.
- **Enterprise deployment:** Docker image and support for a company-approved AI endpoint, so firms can use it on real client rules.
- **Persistent analytics and saved history** using a database, once there is a real user base.

## If I started again
I would talk to colleagues earlier, collecting real "how long did this take you" numbers before writing the PRD, and record the demo against the live URL as soon as the first version deployed.
