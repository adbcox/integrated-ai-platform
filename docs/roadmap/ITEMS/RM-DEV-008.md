# RM-DEV-008

- **ID:** `RM-DEV-008`
- **Title:** Docker compose dev environment
- **Category:** `DEV`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P2`
- **Queue rank:** `7`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Create a Docker Compose configuration that spins up the complete development environment including all services, databases, caches, and external service mocks.

## Why it matters

Eliminates "works on my machine" problems. Ensures environment parity. Simplifies onboarding for new developers. Enables isolated testing and development.

## Key requirements

- Complete service stack in docker-compose.yml
- Database initialization and migrations
- Cache services (Redis) configuration
- External service mocks
- Volume mounting for development
- Environment variable configuration
- Health checks for all services
- Easy start/stop commands

## Affected systems

- local development environment
- deployment preparation
- service integration testing

## Expected file families

- docker-compose.yml
- docker-compose.dev.yml
- Dockerfile for services
- scripts/docker-dev-setup.sh

## Dependencies

- Docker installation
- setup script (RM-DEV-002)

## Risks and issues

### Key risks
- Docker compatibility issues
- performance on certain hosts (especially macOS)
- complexity of multi-service orchestration

### Known issues / blockers
- none; ready to start

## Recommended first milestone

Working docker-compose.yml with backend service, PostgreSQL, and Redis running.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: docker-compose.yml created and tested
- Validation / closeout condition: complete environment starts with single command
