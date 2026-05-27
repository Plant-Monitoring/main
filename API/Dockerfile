FROM python:3.10-slim

# Install system dependencies for Tkinter and virtual display
RUN apt-get update && apt-get install -y \
    tk \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /main

# Copy requirements (create a requirements.txt with needed packages)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application and optional plants.csv
COPY main.py .
# optional – if not present, fallback sample data is used
COPY plants.csv .

# Use xvfb-run to provide a virtual display for the GUI
CMD ["xvfb-run", "python", "main.py"]