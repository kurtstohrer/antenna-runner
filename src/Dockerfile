# Pull a base image, Ubuntu 20.04 in this case
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive



# Install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    wget \
    unzip \
    apt-transport-https \
    ca-certificates \
    gnupg-agent \
    software-properties-common \
    git \
    bash

# Install Docker and Kubectl
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable" && \
    apt-get update && \
    apt-get install -y docker-ce docker-ce-cli containerd.io && \
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list && \
    apt-get update && \
    apt-get install -y kubectl

# Clear the apt cache to reduce image size
RUN rm -rf /var/lib/apt/lists/*

# Create a directory in the container where the code will reside
WORKDIR /app

# Copy the dependencies file to the working directory
COPY ./app/requirements.txt .

# Install any dependencies including Uvicorn
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code of the application to the working directory
COPY ./app/ .

# The command to run when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
