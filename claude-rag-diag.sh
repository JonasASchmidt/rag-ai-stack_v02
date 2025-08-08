#!/bin/bash

echo "=== RAG Stack Diagnose ==="
echo "Datum: $(date)"
echo

# 1. Environment Check
echo "1. ENVIRONMENT CHECK"
echo "-------------------"
if [ -f ".env" ]; then
    echo "✓ .env file exists"
    echo "Key variables:"
    grep -E "OLLAMA_API_URL|LLM_MODEL|DOCS_DIR|INDEX_DIR" .env 2>/dev/null || echo "⚠️  Key variables not found in .env"
else
    echo "❌ .env file missing! Copy from .env.example"
fi
echo

# 2. Ollama Connection Check
echo "2. OLLAMA CONNECTION CHECK"
echo "-------------------------"
OLLAMA_URL=${OLLAMA_API_URL:-"http://localhost:11434"}
echo "Testing connection to: $OLLAMA_URL"

if curl -s "$OLLAMA_URL/api/tags" >/dev/null 2>&1; then
    echo "✓ Ollama is reachable"
    echo "Available models:"
    curl -s "$OLLAMA_URL/api/tags" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for model in data.get('models', []):
        print(f'  - {model[\"name\"]}')
except:
    print('  Could not parse models')
"
else
    echo "❌ Ollama not reachable at $OLLAMA_URL"
    echo "Solutions:"
    echo "  - Start Ollama: 'ollama serve'"
    echo "  - Check if running: 'ps aux | grep ollama'"
    echo "  - Or use Docker: 'docker compose up ollama'"
fi
echo

# 3. Directory Structure Check
echo "3. DIRECTORY STRUCTURE CHECK"
echo "---------------------------"
DOCS_DIR=${DOCS_DIR:-"docs"}
INDEX_DIR=${INDEX_DIR:-"storage"}

echo "Documents directory: $DOCS_DIR"
if [ -d "$DOCS_DIR" ]; then
    echo "✓ Documents directory exists"
    DOC_COUNT=$(find "$DOCS_DIR" -type f \( -name "*.txt" -o -name "*.pdf" -o -name "*.md" \) | wc -l)
    echo "  Document count: $DOC_COUNT"
    if [ $DOC_COUNT -eq 0 ]; then
        echo "⚠️  No documents found for indexing"
    fi
else
    echo "❌ Documents directory missing"
    mkdir -p "$DOCS_DIR" && echo "Created $DOCS_DIR directory"
fi

echo "Index directory: $INDEX_DIR"
if [ -d "$INDEX_DIR" ]; then
    echo "✓ Index directory exists"
    INDEX_FILES=$(find "$INDEX_DIR" -type f | wc -l)
    echo "  Index files count: $INDEX_FILES"
    if [ $INDEX_FILES -eq 0 ]; then
        echo "⚠️  No index files found - run indexing first"
    fi
else
    echo "❌ Index directory missing"
    mkdir -p "$INDEX_DIR" && echo "Created $INDEX_DIR directory"
fi
echo

# 4. Python Dependencies Check
echo "4. PYTHON DEPENDENCIES CHECK"
echo "----------------------------"
if python3 -c "import chainlit, llama_index" 2>/dev/null; then
    echo "✓ Core dependencies available"
else
    echo "❌ Missing core dependencies"
    echo "Install with: pip install -r indexer/requirements.txt -r backend/requirements.txt"
fi
echo

# 5. Process Check
echo "5. RUNNING PROCESSES CHECK"
echo "-------------------------"
if pgrep -f "chainlit" > /dev/null; then
    echo "✓ Chainlit is running"
    echo "  PIDs: $(pgrep -f chainlit | tr '\n' ' ')"
else
    echo "⚠️  Chainlit not running"
fi

if pgrep -f "indexer" > /dev/null; then
    echo "✓ Indexer is running"
else
    echo "⚠️  Indexer not running"
fi
echo

# 6. Quick Test
echo "6. QUICK CONNECTIVITY TEST"
echo "--------------------------"
if [ -f "backend/app.py" ]; then
    echo "Testing backend imports..."
    python3 -c "
import sys
sys.path.append('.')
try:
    from backend.app import *
    print('✓ Backend imports successful')
except Exception as e:
    print(f'❌ Backend import error: {e}')
"
else
    echo "❌ backend/app.py not found"
fi
echo

echo "=== NEXT STEPS ==="
echo "1. Fix any ❌ errors above"
echo "2. Ensure Ollama is running with required model"
echo "3. Run indexing: python -m indexer.ingest"
echo "4. Start backend: python -m chainlit run backend/app.py"
echo "5. Test at http://localhost:8000"