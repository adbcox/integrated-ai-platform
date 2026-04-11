FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

# Install SSH server
RUN apt-get update && apt-get install -y openssh-server && \
    mkdir -p /var/run/sshd && \
    rm -rf /var/lib/apt/lists/*

# Authorize the Mac's SSH key so VS Code Remote SSH works
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
COPY .ssh/authorized_keys /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/authorized_keys

# Allow root SSH login (local dev container only)
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8010 22

# Start SSH daemon then the API server
CMD ["/bin/bash", "-c", "/usr/sbin/sshd && uvicorn browser_operator_api:app --host 0.0.0.0 --port 8010"]
