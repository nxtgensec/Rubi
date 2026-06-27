$ErrorActionPreference = "Stop"

Write-Host "Starting Rubi services with Docker Compose..."
docker compose up --build
