# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Install OpenJDK and other necessary tools
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk gcc g++ make && \
    apt-get install -y python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

