#!/usr/bin/env bash
set -euo pipefail
if [ ! -f .env ]; then
  cp .env.example .env
  KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
  sed -i.bak "s|replace-with-32-byte-url-safe-base64-fernet-key|$KEY|" .env
fi
docker compose up --build -d
