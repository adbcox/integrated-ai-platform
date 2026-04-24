ARG BASE_RUNTIME_IMAGE=docker.openhands.dev/openhands/runtime@sha256:6d38c86944bcb7d05dd1add77bc9b7794cc1e7628f31615ca79cecd7556444fc
FROM ${BASE_RUNTIME_IMAGE}

USER root

ENV DEBIAN_FRONTEND=noninteractive

# Bake tmux into the runtime image so OpenHands does not need apt at session start.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tmux \
    && rm -rf /var/lib/apt/lists/*
