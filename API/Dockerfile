# --- Stage 1: dependencies ---
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Stage 2: runtime ---
FROM python:3.10-slim

# Install only the necessary runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \          
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy the application code and optional trained model
COPY api.py .
# copied only if present
COPY plant_health_cnn.keras* .   

EXPOSE 5000

CMD ["python", "api.py", "--host", "0.0.0.0", "--port", "5000"]