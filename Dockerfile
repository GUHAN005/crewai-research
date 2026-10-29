FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# build-essential: some CrewAI dependencies compile native code
# fonts-dejavu-core: needed so the PDF export can show all characters
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first so Docker can cache this layer
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

# Default: start the web UI.  (CLI: docker compose run --rm crew python main.py "topic")
CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
