#!/bin/bash

echo "=== NUTZE EXISTIERENDE PYTHON 3.12.5 ==="
echo

# 1. Deactivate current venv
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "1. Deaktiviere aktuelles venv..."
    deactivate 2>/dev/null || true
fi

# 2. Set local Python version
echo "2. Setze lokale Python Version auf 3.12.5..."
pyenv local 3.12.5

# Verify it worked
echo "Aktuelle Python Version: $(python --version)"

if python --version | grep -q "3.12.5"; then
    echo "✓ Python 3.12.5 ist aktiv"
else
    echo "❌ Python 3.12.5 nicht aktiv"
    echo "Manuell aktivieren:"
    echo "  pyenv shell 3.12.5"
    echo "  python --version"
    exit 1
fi

# 3. Remove old venv
echo
echo "3. Entferne altes venv..."
rm -rf .venv
echo "✓ Altes .venv entfernt"

# 4. Create new venv with 3.12.5
echo
echo "4. Erstelle neues venv mit Python 3.12.5..."
python -m venv .venv

# 5. Activate new venv
echo "5. Aktiviere venv..."
source .venv/bin/activate

echo "✓ venv aktiviert"
echo "Python in venv: $(python --version)"
echo "Virtual Environment: $VIRTUAL_ENV"

# 6. Upgrade pip
echo
echo "6. Upgrade pip..."
python -m pip install --upgrade pip --quiet

# 7. Install requirements
echo
echo "7. Installiere Dependencies..."

# Check what requirement files exist
if [ -f "indexer/requirements.txt" ]; then
    echo "Installiere indexer/requirements.txt..."
    pip install -r indexer/requirements.txt --quiet
    echo "✓ Indexer dependencies installiert"
fi

if [ -f "backend/requirements.txt" ]; then
    echo "Installiere backend/requirements.txt..."
    pip install -r backend/requirements.txt --quiet
    echo "✓ Backend dependencies installiert"
fi

# Install essential packages
echo "Installiere essential packages..."
pip install python-dotenv requests --quiet

# 8. Test critical imports
echo
echo "8. Teste kritische Imports..."
python -c "
import sys
print(f'✓ Python: {sys.version.split()[0]}')

try:
    import chainlit
    print('✓ Chainlit erfolgreich importiert')
except ImportError as e:
    print(f'❌ Chainlit Fehler: {e}')
    print('   Installiere manuell: pip install chainlit')

try:
    import llama_index
    print('✓ LlamaIndex erfolgreich importiert')
except ImportError as e:
    print(f'❌ LlamaIndex Fehler: {e}')
    print('   Installiere manuell: pip install llama-index')

try:
    from dotenv import load_dotenv
    print('✓ python-dotenv verfügbar')
except ImportError:
    print('❌ python-dotenv fehlt')

print('\\n--- Virtual Environment Info ---')
print(f'VIRTUAL_ENV: {sys.prefix}')
print(f'Site-packages: {[p for p in sys.path if \"site-packages\" in p]}')
"

echo
echo "=== SETUP ABGESCHLOSSEN ==="
echo "✅ Python 3.12.5 venv erfolgreich erstellt!"
echo
echo "NÄCHSTE SCHRITTE:"
echo "1. Debug test: python quick_debug.py"
echo "2. Ollama starten (neues Terminal): ollama serve"
echo "3. Model laden: ollama pull llama3.1:latest"
echo "4. Index erstellen: python -m indexer.ingest"
echo "5. App starten: python -m chainlit run backend/app.py"
echo
echo "Bei Problemen mit Chainlit:"
echo "  pip install chainlit==1.0.0"