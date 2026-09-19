#!/bin/sh
set -eu

if [ "${OLLAMA_EMBEDDED:-false}" = "true" ]; then
  if ! command -v ollama >/dev/null 2>&1; then
    echo "OLLAMA_EMBEDDED=true but ollama is not installed in this image." >&2
    echo "Rebuild with: docker build --build-arg INSTALL_OLLAMA=true ..." >&2
    exit 1
  fi

  export OLLAMA_HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
  ollama serve &

  attempts=0
  until curl -fsS "http://${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 60 ]; then
      echo "Ollama did not become ready in time." >&2
      exit 1
    fi
    sleep 1
  done

  model="${OLLAMA_MODEL:-llama3.1:8b}"
  if ! ollama list | awk 'NR > 1 { print $1 }' | grep -Fxq "$model"; then
    ollama pull "$model"
  fi
fi

exec "$@"
