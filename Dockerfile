FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Hugging Face Spaces exposes port 7860 by default
ENV PORT=7860

# Create and set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the entire repository into the container
COPY . /app/

# Start the FastAPI server using the dynamic port provided by Railway/Hosting platform
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
