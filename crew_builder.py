"""Builds the crew from config/agents.yaml and config/tasks.yaml."""
import os
from datetime import datetime
from pathlib import Path

import yaml
from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import tool
from ddgs import DDGS

CONFIG_DIR = Path(__file__).parent / "config"


# ---------- TOOL: lets the Researcher search the live internet ----------
@tool("web_search")
def web_search(query: str) -> str:
    """Search the web and return the top results (title, URL, snippet).
    Use this to find current and recent information."""
    try:
        results = DDGS().text(
            query,
            region=os.getenv("SEARCH_REGION", "in-en"),
            max_results=5,
        )
    except Exception as e:
        return (f"Search failed ({e}). Continue with general knowledge "
                "and clearly mark the information as unverified.")
    if not results:
        return "No results found. Try a different, shorter query."
    return "\n\n".join(
        f"{r.get('title', '')}\n{r.get('href', '')}\n{r.get('body', '')}"
        for r in results
    )


# Tool names used in agents.yaml -> real tool objects
TOOLS = {"web_search": web_search}


def make_llm(model: str | None = None) -> LLM:
    """One place that creates the AI model. Key and endpoint come from .env"""
    return LLM(
        model=model or os.getenv("MODEL", "openai/gemini-2.5-flash"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL") or None,
        temperature=0.3,
    )


def _load(name: str) -> dict:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _fill(text: str, values: dict) -> str:
    """Replace {topic} / {today} (simple, safe even if text has other braces)."""
    for key, value in values.items():
        text = text.replace("{" + key + "}", value)
    return " ".join(text.split())   # tidy YAML line breaks


def build_crew(topic: str, out_dir: str, task_callback=None) -> Crew:
    values = {"topic": topic, "today": datetime.now().strftime("%d %B %Y")}

    default_llm = make_llm()
    researcher_model = os.getenv("RESEARCHER_MODEL")
    researcher_llm = make_llm(researcher_model) if researcher_model else default_llm

    # ---------- Agents ----------
    agents = {}
    for key, cfg in _load("agents.yaml").items():
        agents[key] = Agent(
            role=_fill(cfg["role"], values),
            goal=_fill(cfg["goal"], values),
            backstory=_fill(cfg["backstory"], values),
            llm=researcher_llm if cfg.get("llm") == "researcher" else default_llm,
            tools=[TOOLS[t] for t in cfg.get("tools", [])],
            max_iter=cfg.get("max_iter", 20),
            verbose=True,
        )

    # ---------- Tasks ----------
    tasks = {}
    for key, cfg in _load("tasks.yaml").items():
        output_file = cfg.get("output_file")
        tasks[key] = Task(
            name=key,
            description=_fill(cfg["description"], values),
            expected_output=_fill(cfg["expected_output"], values),
            agent=agents[cfg["agent"]],
            context=[tasks[c] for c in cfg.get("context", [])] or None,
            output_file=f"{out_dir}/{output_file}" if output_file else None,
        )

    # ---------- Crew ----------
    return Crew(
        agents=list(agents.values()),
        tasks=list(tasks.values()),
        process=Process.sequential,
        max_rpm=int(os.getenv("MAX_RPM", "8")),
        task_callback=task_callback,
        verbose=True,
    )
