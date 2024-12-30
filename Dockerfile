# Stage 1: Build stage
FROM tensorflow/tensorflow:latest

# Set environment variables to avoid writing bytecode and enable unbuffered mode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install build dependencies and Python dependencies
RUN apt update \
    && apt install -y pkg-config \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port
EXPOSE 80

# Set the command to run your application
CMD ["bash", "run.sh"]
