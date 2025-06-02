# Base image with CUDA and cuDNN but no Python
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Set working directory
WORKDIR /code

# Install Python 3 and other OS dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-venv git curl build-essential \
 && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Copy and install Python dependencies
COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /code/app

# Launch FastAPI app
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
