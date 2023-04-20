# Dockerfile for running code checker with GPT-3

# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies
RUN pip install openai

# Copy the code checker script into the container
COPY code_checker.py .

# Set environment variables for GPT-3 API
ENV OPENAI_API_KEY=<your_api_key>

# Run the code checker script
CMD ["python", "code_checker.py"]
