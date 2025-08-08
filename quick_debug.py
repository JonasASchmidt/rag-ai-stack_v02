#!/usr/bin/env python3
"""
Quick RAG Stack Debug - Tests current setup
"""
import sys
import os
import subprocess

def test_imports():
    """Test critical imports"""
    print("=== IMPORT TESTS ===")
    
    # Python version check
    print(f"Python version: {sys.version}")
    if sys.version_info >= (3, 13):
        print("⚠️  WARNING: Python 3.13+ may cause issues with Chainlit")
        print("   Recommended: Python 3.11 or 3.12")
    
    # Test imports one by one
    imports = [
        ("dotenv", "from dotenv import load_dotenv"),
        ("requests", "import requests"),
        ("llama_index", "import llama_index"),
        ("chainlit", "import chainlit"),
        ("watchdog", "from watchdog.observers import Observer"),
    ]
    
    for name, import_cmd in imports:
        try:
            exec(import_cmd)
            print(f"✓ {name}")
        except ImportError as e:
            print(f"❌ {name}: {e}")
        except Exception as e:
            print(f"⚠️  {name}: {e}")

def test_ollama():
    """Test Ollama connection"""
    print("\n=== OLLAMA TEST ===")
    
    try:
        import requests
        
        # Load .env if exists
        if os.path.exists('.env'):
            from dotenv import load_dotenv
            load_dotenv()
        
        ollama_url = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
        print(f"Testing Ollama at: {ollama_url}")
        
        # Test connection
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✓ Ollama connected, {len(models)} models available")
            
            target_model = os.getenv('LLM_MODEL', 'llama3.1:latest')
            model_names = [m['name'] for m in models]
            
            if target_model in model_names:
                print(f"✓ Target model '{target_model}' available")
            else:
                print(f"❌ Target model '{target_model}' not found")
                print(f"   Available: {model_names}")
                print(f"   Install with: ollama pull {target_model}")
        else:
            print(f"❌ Ollama API returned status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama")
        print("   Start with: ollama serve")
    except ImportError:
        print("❌ requests module not available")
    except Exception as e:
        print(f"❌ Ollama test error: {e}")

def test_directories():
    """Test directory structure"""
    print("\n=== DIRECTORY TEST ===")
    
    # Load .env
    docs_dir = os.getenv('DOCS_DIR', 'docs')
    index_dir = os.getenv('INDEX_DIR', 'storage')
    
    # Test docs directory
    if os.path.exists(docs_dir):
        doc_count = len([f for f in os.listdir(docs_dir) 
                        if f.endswith(('.txt', '.md', '.pdf'))])
        print(f"✓ {docs_dir}/ exists with {doc_count} documents")
    else:
        print(f"❌ {docs_dir}/ directory missing")
    
    # Test index directory  
    if os.path.exists(index_dir):
        index_files = len([f for f in os.listdir(index_dir) if os.path.isfile(os.path.join(index_dir, f))])
        print(f"✓ {index_dir}/ exists with {index_files} index files")
        if index_files == 0:
            print("   ⚠️  No index files - run: python -m indexer.ingest")
    else:
        print(f"❌ {index_dir}/ directory missing")

def test_backend_imports():
    """Test backend specific imports"""
    print("\n=== BACKEND IMPORT TEST ===")
    
    # Add current directory to path
    sys.path.insert(0, '.')
    
    try:
        from core.interfaces import QueryEngine
        print("✓ core.interfaces imported")
    except ImportError as e:
        print(f"❌ core.interfaces: {e}")
    
    try:
        from core.adapters.llama_index import LlamaIndexQueryEngine  
        print("✓ core.adapters.llama_index imported")
    except ImportError as e:
        print(f"❌ core.adapters.llama_index: {e}")
    
    try:
        # Check if backend app exists and can be imported
        if os.path.exists('backend/app.py'):
            print("✓ backend/app.py exists")
        else:
            print("❌ backend/app.py not found")
    except Exception as e:
        print(f"❌ backend test error: {e}")

def main():
    print("RAG STACK QUICK DEBUG")
    print("=" * 30)
    
    test_imports()
    test_ollama()  
    test_directories()
    test_backend_imports()
    
    print("\n" + "=" * 30)
    print("RECOMMENDATIONS:")
    
    if sys.version_info >= (3, 13):
        print("1. 🔧 CRITICAL: Recreate venv with Python 3.12")
        print("   pyenv install 3.12.5")
        print("   pyenv local 3.12.5") 
        print("   rm -rf .venv")
        print("   python -m venv .venv")
        print("   source .venv/bin/activate")
        print("   pip install -r indexer/requirements.txt -r backend/requirements.txt")
    
    print("2. 📝 Ensure Ollama is running: ollama serve")
    print("3. 📚 Add documents to docs/ directory")
    print("4. 🔄 Build index: python -m indexer.ingest")
    print("5. 🚀 Start backend: python -m chainlit run backend/app.py")

if __name__ == "__main__":
    main()