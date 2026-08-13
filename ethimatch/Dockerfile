# EthiMatch — Neuro-Symbolic Clinical Trial Matching Platform
# Lightweight CPU image for reproducible Streamlit deployment.

FROM python:3.11-slim-bookworm

LABEL org.opencontainers.image.title="EthiMatch" \
      org.opencontainers.image.description="Neuro-Symbolic Clinical Trial Matching (Streamlit)" \
      org.opencontainers.image.source="https://github.com/your-org/ethimatch"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    HF_HOME=/root/.cache/huggingface

WORKDIR /app

# System libraries for scientific Python wheels (numpy, torch, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (CPU PyTorch first for smaller, reliable slim builds)
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

# Application source
COPY app.py console.py config.py ./
COPY data_interface.py data_simulator.py ethimatch_pipeline.py ./
COPY mock_database.py neural_extractor.py ./
COPY symbolic_validator.py xai_explainer.py trial_registry.py ./
COPY evaluation.py evaluation_cohort.py baseline_llm.py pdf_export.py ./
COPY ui/ ./ui/
COPY trials/ ./trials/
COPY data/bronze/ ./data/bronze/
COPY data/silver/ ./data/silver/
COPY data/gold/ ./data/gold/
COPY data/csv_sample/ ./data/csv_sample/

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
