# CrewAI + Docker: AI Research Crew

Three agents create a report on any topic:

    Researcher (web search) -> Writer -> Editor / Fact Checker

You can use it from the **browser (web UI)** or the **command line**.

## Setup
1. Install Docker Desktop and wait until it says "Engine running".
2. Copy `.env.example` to `.env` and put your Gemini API key
   (free, from https://aistudio.google.com) in `LLM_API_KEY`.

## Run the web UI
    docker compose up --build

Then open **http://localhost:8501**, type a topic, click *Generate report*.
When it finishes you can download the report as Markdown, Word or PDF.
(Stop the app with Ctrl+C in the terminal.)

## Run from the command line (no browser)
    docker compose run --rm crew python main.py "Electric cars in India"

Every run creates its own folder: `output/<date_time>_<topic>/`
with `draft.md` (writer) and `report.md` (final, after editing).

Use `--build` once after changing code or requirements.

## Project structure
    config/agents.yaml   WHO: role, goal, backstory, tools of each agent
    config/tasks.yaml    WHAT: description, expected output, order of tasks
    crew_builder.py      builds the crew from the YAML files (+ web_search tool)
    report_runner.py     runs one report and saves the files
    exporters.py         Markdown -> Word / PDF
    app.py               Streamlit web UI
    main.py              command-line entry point

To change how an agent behaves, edit the YAML files. No Python needed.

## Settings (in .env)
- `MODEL`            AI model name
- `RESEARCHER_MODEL` optional: different model for the Researcher only
- `MAX_RPM`          max AI requests per minute (lower it if you see 429 errors)
- `SEARCH_REGION`    in-en (India), us-en, wt-wt (worldwide)
