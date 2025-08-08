#!/bin/bash

echo "=== PYTHON VERSION FIX FÜR CHAINLIT ==="
echo "Chainlit erfordert Python 3.11 oder 3.12 (nicht 3.13+)"
echo

# 1. Deactivate current venv
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "1. Deaktiviere aktuelles venv..."
    deactivate 2>/dev/null || true
fi

# 2. Set Python 3.12 for this project
echo "2. Setze Python 3.12 für dieses Projekt..."
pyenv local 3.12.5

# Verify pyenv worked
if python --version | grep -q "3.12"; then
    echo "✓ Python 3.12.5 aktiv"
else
    echo "❌ Python 3.12 nicht verfügbar"
    echo "Installiere Python 3.12:"
    echo "  pyenv install 3.12.5"
    echo "  pyenv local 3.12.5"
    exit 1
fi

# 3. Remove old venv  
echo
echo "3. Entferne altes venv (Python 3.13)..."
rm -rf .venv
echo "✓ Altes .venv entfernt"

# 4. Create new venv with Python 3.12
echo
echo "4. Erstelle neues venv mit Python 3.12..."
python -m venv .venv

if [ $? -eq 0 ]; then
    echo "✓ Neues venv erstellt mit $(python --version)"
else
    echo "❌ venv Erstellung fehlgeschlagen"
    exit 1
fi

# 5. Activate new venv
echo
echo "5. Aktiviere neues venv..."
source .venv/bin/activate

echo "✓ venv aktiviert: $VIRTUAL_ENV"
echo "Python in venv: $(python --version)"

# 6. Upgrade pip
echo
echo "6. Upgrade pip..."
python -m pip install --upgrade pip
echo "✓ pip Version: $(pip --version)"

# 7. Install requirements
echo
echo "7. Installiere Dependencies..."
if [ -f "indexer/requirements.txt" ]; then
    echo "Installing indexer requirements..."
    pip install -r indexer/requirements.txt
fi

if [ -f "backend/requirements.txt" ]; then
    echo "Installing backend requirements..."  
    pip install -r backend/requirements.txt
fi

# Essential packages if requirements missing
echo "Installing essential packages..."
pip install python-dotenv requests

echo
echo "8. Test Installation..."
python -c "
import sys
print(f'Python: {sys.version}')
try:
    import chainlit
    print('✓ Chainlit installed successfully')
except ImportError as e:
    print(f'❌ Chainlit error: {e}')
    print('Manual install: pip install chainlit')
    
try:
    import llama_index  
    print('✓ LlamaIndex available')
except ImportError as e:
    print(f'❌ LlamaIndex error: {e}')
    print('Manual install: pip install llama-index')
"

echo
echo "=== SETUP ABGESCHLOSSEN ==="
echo "✓ Python 3.12 venv erstellt und aktiviert"
echo "✓ Dependencies installiert"
echo
echo "NÄCHSTE SCHRITTE:"
echo "1. Bleibe in dieser Terminal-Session (venv aktiv)"
echo "2. Starte Ollama: 'ollama serve' (in neuem Terminal)"
echo "3. Lade Model: 'ollama pull llama3.1:latest'"  
echo "4. Erstelle Index: 'python -m indexer.ingest'"
echo "5. Starte App: 'python -m chainlit run backend/app.py'"
echo
echo "Teste erst mit: python quick_debug.py"