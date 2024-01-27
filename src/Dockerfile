# Pull a base image, Python 3.12.1 in this case
FROM python:3.12.1-slim-bullseye

# Create a directory in the container where the code will reside
WORKDIR /app

# Install system dependencies required for pygit2
# This includes git, libgit2-dev, cmake, and build-essential
RUN apt-get update && \
    apt-get install -y git libgit2-dev cmake build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy the dependencies file to the working directory
COPY ./app/requirements.txt .

# Install any Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install kubectl, docker, curl, wget, unzip, and bash
RUN apt-get update && \
    apt-get install -y curl wget unzip apt-transport-https ca-certificates gnupg-agent software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian bullseye stable" && \
    apt-get update && \
    apt-get install -y docker-ce docker-ce-cli containerd.io && \
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list && \
    apt-get update && \
    apt-get install -y kubectl && \
    apt-get install -y bash
    
# Copy the source code of the application to the working directory
COPY ./app/ .

# The command to run when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
