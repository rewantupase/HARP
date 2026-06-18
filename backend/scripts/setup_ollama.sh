#!/bin/bash
# Pull all required models into Ollama
set -e
OLLAMA_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

echo "Pulling Phi-3 Mini..."
curl -X POST "$OLLAMA_URL/api/pull" -d '{"name":"phi3:mini"}' -H "Content-Type: application/json"

echo "Pulling Mistral 7B..."
curl -X POST "$OLLAMA_URL/api/pull" -d '{"name":"mistral:7b"}' -H "Content-Type: application/json"

echo "Pulling Llama 3 8B..."
curl -X POST "$OLLAMA_URL/api/pull" -d '{"name":"llama3:8b"}' -H "Content-Type: application/json"

echo "All models pulled."
curl "$OLLAMA_URL/api/tags" | python3 -c "import json,sys; [print(m['name']) for m in json.load(sys.stdin)['models']]"
