"""Streamlit web UI:  type a topic, click a button, get the report."""
import os
from pathlib import Path

import streamlit as st

from exporters import markdown_to_docx, markdown_to_pdf
from report_runner import OUTPUT_DIR, list_past_reports, load_report, run_report

st.set_page_config(page_title="AI Research Crew", page_icon="🤖", layout="centered")

STEP_LABELS = {
    "research_task": "Researcher finished the web research",
    "writing_task": "Writer finished the first draft",
    "editing_task": "Editor finished the fact check",
}


def show_result(result: dict) -> None:
    """Show the report with download buttons (Markdown, Word, PDF)."""
    st.success(f"Report ready: {result['name']}")
    name = result["name"]
    report = result["report"]

    # Build the export files once per report (not on every click)
    cache = st.session_state.setdefault("exports", {})
    if cache.get("name") != name:
        cache.clear()
        cache["name"] = name
        for key, fn in (("docx", markdown_to_docx), ("pdf", markdown_to_pdf)):
            try:
                cache[key] = fn(report)
            except Exception as e:                      # never break the page
                cache[key] = None
                cache[key + "_error"] = str(e)

    c1, c2, c3 = st.columns(3)
    c1.download_button("⬇ Markdown", report.encode("utf-8"),
                       file_name=f"{name}.md", mime="text/markdown",
                       use_container_width=True)
    if cache.get("docx"):
        c2.download_button("⬇ Word (.docx)", cache["docx"], file_name=f"{name}.docx",
                           mime="application/vnd.openxmlformats-officedocument."
                                "wordprocessingml.document",
                           use_container_width=True)
    else:
        c2.warning("Word export failed")
    if cache.get("pdf"):
        c3.download_button("⬇ PDF", cache["pdf"], file_name=f"{name}.pdf",
                           mime="application/pdf", use_container_width=True)
    else:
        c3.warning("PDF export failed")

    st.divider()
    tab_final, tab_draft = st.tabs(["Final report", "Writer's draft"])
    with tab_final:
        st.markdown(report)
    with tab_draft:
        st.markdown(result.get("draft") or "_No draft found._")
    st.caption(f"Files are also saved on your computer in: {result['folder']}")


# ---------------------------------------------------------------- page
st.title("🤖 AI Research Crew")
st.caption("Researcher (web search) → Writer → Editor / Fact Checker")

# Sidebar: open an older report
with st.sidebar:
    st.header("Past reports")
    past = list_past_reports()
    choice = st.selectbox("Open a saved report", ["—"] + past, index=0)
    if choice != "—" and st.session_state.get("loaded") != choice:
        st.session_state["result"] = load_report(Path(OUTPUT_DIR) / choice)
        st.session_state["loaded"] = choice
    if not past:
        st.caption("No saved reports yet.")

topic = st.text_input(
    "What should the crew research?",
    value=os.getenv("TOPIC", ""),
    placeholder="Example: Best selling car brands in India",
)

if st.button("Generate report", type="primary", disabled=not topic.strip()):
    # Clear the old report so it is never confused with the new one
    st.session_state.pop("result", None)
    st.session_state["loaded"] = choice          # stops the sidebar re-loading an old report
    error = None

    if not os.getenv("LLM_API_KEY"):
        error = RuntimeError("LLM_API_KEY is missing. Add your key to the .env "
                             "file and restart the container.")
    else:
        with st.status("Crew is working... this takes about 3-6 minutes.",
                       expanded=True) as status:
            st.write("🔎 Researcher is searching the web...")

            def on_step(task_name: str) -> None:
                st.write("✅ " + STEP_LABELS.get(task_name, f"{task_name} finished"))

            try:
                st.session_state["result"] = run_report(topic.strip(), on_step)
                status.update(label="Done!", state="complete", expanded=False)
            except Exception as e:
                error = e
                status.update(label="Something went wrong (details below)",
                              state="error", expanded=True)

    # Show the error OUTSIDE the status box so it is always visible
    if error is not None:
        message = f"{type(error).__name__}: {error}"
        st.error(message[:1500])
        lowered = message.lower()
        if "per day" in lowered or "perday" in lowered:
            st.warning(
                "Daily free limit reached for this model (Gemini free tier counts "
                "requests PER DAY, PER MODEL). Waiting 1-2 minutes will not help.\n\n"
                "Options:\n"
                "1. Change MODEL in your .env to a different Gemini model "
                "(every model has its own daily counter), then restart.\n"
                "2. Wait for the daily reset (midnight Pacific time).\n"
                "3. Link billing in Google AI Studio to move to a higher tier."
            )
        elif any(k in lowered for k in ("429", "rate", "quota", "resource_exhausted")):
            st.info("Per-minute limit reached. Wait 1-2 minutes and try again. "
                    "If it keeps happening, set MAX_RPM=5 in .env (then restart).")
        elif any(k in lowered for k in ("api key", "api_key", "401", "403", "permission")):
            st.info("Check LLM_API_KEY in your .env file.")
        else:
            st.info("For the full technical details, look at the PowerShell window "
                    "where docker compose is running.")

if st.session_state.get("result"):
    show_result(st.session_state["result"])
