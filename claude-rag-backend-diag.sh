#!/usr/bin/env python3
"""
RAG Backend Debug Script
Testet alle kritischen Verbindungen und Komponenten
"""
import os
import sys
import json
import time
import asyncio
import requests
from pathlib import Path
from typing import Optional

def print_status(message: str, success: bool = True):
    """Formatierte Statusausgabe"""
    icon = "✓" if success else "❌"
    print(f"{icon} {message}")

def print_warning(message: str):
    """Warnung ausgeben"""
    print(f"⚠️  {message}")

def test_ollama_connection():
    """Teste Ollama API Verbindung"""
    print("\n=== OLLAMA CONNECTION TEST ===")
    
    api_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    print(f"Testing: {api_url}")
    
    try:
        # Test API availability
        response = requests.get(f"{api_url}/api/tags", timeout=10)
        response.raise_for_status()
        
        models = response.json().get("models", [])
        print_status("Ollama API is reachable")
        print(f"Available models: {len(models)}")
        
        target_model = os.getenv("LLM_MODEL", "llama3.1:latest")
        model_names = [m["name"] for m in models]
        
        if target_model in model_names:
            print_status(f"Target model '{target_model}' is available")
            
            # Test model generation
            test_payload = {
                "model": target_model,
                "prompt": "Test: Say 'Hello World' in one word.",
                "stream": False
            }
            
            print("Testing model generation...")
            gen_response = requests.post(
                f"{api_url}/api/generate",
                json=test_payload,
                timeout=30
            )
            
            if gen_response.status_code == 200:
                result = gen_response.json()
                print_status("Model generation test successful")
                print(f"Response: {result.get('response', 'N/A')[:100]}...")
                return True
            else:
                print_status(f"Model generation failed: {gen_response.status_code}", False)
                
        else:
            print_status(f"Target model '{target_model}' not found", False)
            print(f"Available: {model_names}")
            print(f"Install with: ollama pull {target_model}")
            
    except requests.exceptions.ConnectionError:
        print_status("Cannot connect to Ollama API", False)
        print("Solutions:")
        print("- Start Ollama: 'ollama serve'")
        print("- Check if running: 'ollama list'")
        return False
        
    except Exception as e:
        print_status(f"Ollama test error: {e}", False)
        return False
    
    return True

def test_index_loading():
    """Teste das Laden des Vector Index"""
    print("\n=== INDEX LOADING TEST ===")
    
    index_dir = os.getenv("INDEX_DIR", "storage")
    
    if not os.path.exists(index_dir):
        print_status(f"Index directory '{index_dir}' doesn't exist", False)
        print("Run: python -m indexer.ingest")
        return False
    
    # Check for index files
    index_files = list(Path(index_dir).rglob("*"))
    if not index_files:
        print_status("No index files found", False)
        print("Run: python -m indexer.ingest")
        return False
    
    print_status(f"Found {len(index_files)} index files")
    
    # Test loading with LlamaIndex
    try:
        sys.path.append(".")
        from llama_index.core import StorageContext, load_index_from_storage
        
        print("Loading vector index...")
        storage_context = StorageContext.from_defaults(persist_dir=index_dir)
        index = load_index_from_storage(storage_context)
        
        print_status("Vector index loaded successfully")
        
        # Test query engine creation
        query_engine = index.as_query_engine()
        print_status("Query engine created successfully")
        
        return True
        
    except ImportError as e:
        print_status(f"Missing dependencies: {e}", False)
        print("Install: pip install llama-index")
        return False
        
    except Exception as e:
        print_status(f"Index loading error: {e}", False)
        return False

def test_documents():
    """Teste Dokument-Verfügbarkeit"""
    print("\n=== DOCUMENTS TEST ===")
    
    docs_dir = os.getenv("DOCS_DIR", "docs")
    
    if not os.path.exists(docs_dir):
        print_status(f"Documents directory '{docs_dir}' doesn't exist", False)
        os.makedirs(docs_dir, exist_ok=True)
        print(f"Created {docs_dir} directory")
        return False
    
    # Check for documents
    doc_extensions = ['.txt', '.pdf', '.md', '.docx']
    docs = []
    for ext in doc_extensions:
        docs.extend(Path(docs_dir).rglob(f"*{ext}"))
    
    if not docs:
        print_status("No documents found for indexing", False)
        print(f"Add documents to {docs_dir}/ directory")
        return False
    
    print_status(f"Found {len(docs)} documents")
    for doc in docs[:5]:  # Show first 5
        print(f"  - {doc.name}")
    if len(docs) > 5:
        print(f"  ... and {len(docs) - 5} more")
    
    return True

async def test_backend_components():
    """Teste Backend-Komponenten"""
    print("\n=== BACKEND COMPONENTS TEST ===")
    
    try:
        sys.path.append(".")
        
        # Test core imports
        print("Testing core imports...")
        from core.interfaces import QueryEngine, Retriever
        print_status("Core interfaces imported")
        
        from core.adapters.llama_index import LlamaIndexQueryEngine
        print_status("LlamaIndex adapter imported")
        
        import chainlit as cl
        print_status("Chainlit imported")
        
        # Test environment loading
        if os.path.exists(".env"):
            from dotenv import load_dotenv
            load_dotenv()
            print_status(".env loaded")
        
        return True
        
    except ImportError as e:
        print_status(f"Import error: {e}", False)
        return False
    except Exception as e:
        print_status(f"Backend component error: {e}", False)
        return False

def create_test_document():
    """Erstelle ein Test-Dokument wenn keines vorhanden"""
    docs_dir = os.getenv("DOCS_DIR", "docs")
    test_file = Path(docs_dir) / "test_document.md"
    
    if not test_file.exists():
        os.makedirs(docs_dir, exist_ok=True)
        
        content = """# Test Document

This is a test document for the RAG AI Stack.

## About RAG
Retrieval-Augmented Generation (RAG) combines information retrieval with generative AI models to provide accurate, context-aware responses based on your own documents.

## Features
- Document ingestion and vector indexing
- Semantic search and retrieval  
- AI-powered response generation
- Real-time chat interface

This document can be used to test the system's ability to answer questions about RAG and the stack's capabilities.
"""
        
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(content)
            
        print_status(f"Created test document: {test_file}")
        return True
    
    return False

def main():
    """Hauptfunktion für alle Tests"""
    print("RAG AI STACK DEBUG & CONNECTION TEST")
    print("=" * 50)
    
    # Load environment
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
        print_status(".env file loaded")
    else:
        print_warning("No .env file found - using defaults")
    
    test_results = []
    
    # Run tests
    test_results.append(("Ollama Connection", test_ollama_connection()))
    test_results.append(("Documents", test_documents()))
    test_results.append(("Index Loading", test_index_loading()))
    test_results.append(("Backend Components", asyncio.run(test_backend_components())))
    
    # Create test document if needed
    if not any(Path(os.getenv("DOCS_DIR", "docs")).rglob("*.md")):
        create_test_document()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in test_results:
        print_status(f"{test_name}: {'PASS' if result else 'FAIL'}", result)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Your RAG stack should work.")
        print("\nNext steps:")
        print("1. Run indexing: python -m indexer.ingest")
        print("2. Start backend: python -m chainlit run backend/app.py")
        print("3. Open http://localhost:8000")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Fix issues above first.")

if __name__ == "__main__":
    main()