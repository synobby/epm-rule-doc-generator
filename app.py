"""Streamlit UI for the EPM Business Rule Documentation Generator.

This file only handles the screen. All logic lives in core/ (see architecture.md).
Run locally with:  streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # reads .env when running locally; Render uses real environment variables

from core import llm_client, telemetry  # noqa: E402
from core.exporters import DRAFT_NOTE, safe_filename, to_docx, to_markdown  # noqa: E402
from core.pipeline import run  # noqa: E402
from core.schemas import DocumentationOutput  # noqa: E402
from core.validator import ValidationError  # noqa: E402

st.set_page_config(page_title="EPM Rule Documentation Generator", page_icon="📄", layout="wide")

SAMPLE_PATH = Path(__file__).parent / "tests" / "samples" / "allocate_opex.csc"

# ---------------- Header ----------------
st.title("EPM Business Rule Documentation Generator")
st.caption(
    "Paste an Essbase / Planning calc script or a Groovy rule. Get a structured technical "
    "document and a line-by-line explanation."
)
if llm_client.is_demo_mode():
    st.info("Demo mode: no LLM API key is set, so AI sections show placeholders. "
            "Parsed facts are real. See README to add a key.")

with st.sidebar:
    st.subheader("Usage (since last restart)")
    stats = telemetry.snapshot()
    st.metric("Rules documented", stats["succeeded"])
    st.metric("Success rate", f"{stats['success_rate']:.0%}" if stats["runs"] else "–")
    st.metric("Avg. time", f"{stats['avg_seconds']:.1f} s" if stats["succeeded"] else "–")
    st.caption(f"Calc scripts: {stats['calc_scripts']} · Groovy: {stats['groovy_rules']} · "
               f"Rejected inputs: {stats['rejected_input']} · AI errors: {stats['ai_errors']}")
    st.caption("Metadata only. Rule text is never logged.")

st.warning("Privacy: use sample or anonymised rules only. Nothing is stored, "
           "but the rule text is sent to the AI provider. Turn on masking for real rules.")

# ---------------- Input ----------------
left, right = st.columns([3, 1])
with left:
    uploaded = st.file_uploader("Upload a rule file", type=["txt", "csc", "groovy"])
    if st.button("Load sample rule"):
        st.session_state["rule_text"] = SAMPLE_PATH.read_text()
    pasted = st.text_area("…or paste the rule here", height=260, key="rule_text")

with right:
    default_name = Path(uploaded.name).stem if uploaded else "Business rule"
    rule_name = st.text_input("Rule name", value=default_name)
    type_choice = st.selectbox("Rule type", ["Auto-detect", "calc_script", "groovy"])
    mask = st.toggle("Mask member names", value=False,
                     help="Replaces quoted member names with tokens before sending to the AI.")
    extra = st.text_input("Extra names to mask (comma-separated)", disabled=not mask)
    generate = st.button("Generate", type="primary", width="stretch")

# ---------------- Run ----------------
if generate:
    raw = uploaded.getvalue() if uploaded else pasted
    try:
        with st.spinner("Reading the rule and writing the documentation…"):
            result = run(
                raw,
                rule_name=rule_name,
                rule_type=None if type_choice == "Auto-detect" else type_choice,
                mask=mask,
                extra_mask_names=[n.strip() for n in extra.split(",") if n.strip()] if mask else None,
            )
        st.session_state["result"] = result
    except ValidationError as exc:
        st.error(str(exc))
    except llm_client.LLMError as exc:
        st.error(str(exc))
    except Exception:  # keep the user-facing message friendly
        st.error("Something went wrong while contacting the AI. Please try again.")
    else:
        st.rerun()  # refresh so the sidebar usage stats include this run

result = st.session_state.get("result")
if not result:
    st.stop()

for warning in result.warnings:
    st.warning(warning)
if result.unverified_members:
    st.warning("⚠ The AI mentioned members the parser did not find in the rule: "
               + ", ".join(result.unverified_members) + ". Please check them.")

doc = result.documentation
tab_doc, tab_facts, tab_teach = st.tabs(["Documentation", "Extracted facts", "Teach me"])

# ---------------- Documentation (editable) ----------------
with tab_doc:
    st.caption(f"{DRAFT_NOTE}  ·  Rule type: {doc.rule_type}  ·  AI confidence: {doc.confidence}")
    purpose = st.text_area("Purpose", doc.purpose, height=100)

    st.subheader("POV / FIX scope")
    scope = st.data_editor([s.model_dump() for s in doc.pov_fix_scope], num_rows="dynamic",
                           width="stretch", key="scope")
    st.subheader("Dimensions and members")
    dims = st.data_editor([d.model_dump() for d in doc.dimensions_and_members], num_rows="dynamic",
                          width="stretch", key="dims")
    st.subheader("Run-time prompts")
    rtps = st.data_editor([r.model_dump() for r in doc.runtime_prompts], num_rows="dynamic",
                          width="stretch", key="rtps")
    st.subheader("Step-by-step logic")
    steps = st.data_editor([s.model_dump() for s in doc.logic_steps], num_rows="dynamic",
                           width="stretch", key="steps")
    st.subheader("Risks and performance notes")
    risks = st.data_editor([r.model_dump() for r in doc.risks_and_performance_notes],
                           num_rows="dynamic", width="stretch", key="risks")

    edited = DocumentationOutput(
        rule_name=rule_name, rule_type=doc.rule_type, purpose=purpose, confidence=doc.confidence,
        pov_fix_scope=scope, dimensions_and_members=dims, runtime_prompts=rtps,
        logic_steps=steps, risks_and_performance_notes=risks,
    )
    c1, c2 = st.columns(2)
    c1.download_button("Download .md", to_markdown(edited), file_name=safe_filename(rule_name, "md"),
                       mime="text/markdown", width="stretch")
    c2.download_button("Download .docx", to_docx(edited), file_name=safe_filename(rule_name, "docx"),
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       width="stretch")

# ---------------- Extracted facts (code, not AI) ----------------
with tab_facts:
    facts = result.facts
    st.caption("Found by code, not AI. Use this to check the documentation.")
    a, b, c = st.columns(3)
    a.metric("Lines", facts.line_count)
    b.metric("FIX blocks", len(facts.fix_blocks))
    c.metric("Quoted members", len(facts.members))
    st.subheader("FIX blocks")
    st.dataframe([f.model_dump() for f in facts.fix_blocks], width="stretch")
    st.subheader("Run-time prompts / substitution variables")
    st.write(", ".join(facts.runtime_prompts) or "None found")
    st.subheader("Functions")
    st.write(", ".join(facts.functions) or "None found")
    st.subheader("Commands")
    st.write(", ".join(facts.commands) or "None found")
    if facts.groovy_api_calls:
        st.subheader("Groovy API calls")
        st.write(", ".join(facts.groovy_api_calls))
    st.subheader("Members")
    st.write(", ".join(facts.members) or "None found")

# ---------------- Teach me ----------------
with tab_teach:
    if result.teach_me:
        st.dataframe([line.model_dump() for line in result.teach_me.lines],
                     width="stretch", hide_index=True)
    else:
        st.info("The line-by-line view is not available for this run.")
