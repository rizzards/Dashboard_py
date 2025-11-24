"""
Diagnostic Test Script
Run this to identify exactly what's failing in your setup
"""

import os
import sys
from pathlib import Path

def test_1_environment():
    """Test 1: Check environment variables."""
    print("\n" + "="*80)
    print("TEST 1: Environment Variables")
    print("="*80)
    
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_DEPLOYMENT_NAME',
        'AZURE_EMBEDDING_DEPLOYMENT'
    ]
    
    from dotenv import load_dotenv
    load_dotenv()
    
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✓ {var}: {display_value}")
        else:
            print(f"  ✗ {var}: NOT SET")
            all_ok = False
    
    if all_ok:
        print("\n✓ All environment variables set")
    else:
        print("\n✗ Missing environment variables - create .env file")
        return False
    
    return True


def test_2_packages():
    """Test 2: Check required packages."""
    print("\n" + "="*80)
    print("TEST 2: Required Packages")
    print("="*80)
    
    packages = {
        'llama_index': 'llama-index',
        'pdfplumber': 'pdfplumber',
        'dotenv': 'python-dotenv',
    }
    
    all_ok = True
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - Install with: pip install {package}")
            all_ok = False
    
    # Check optional
    try:
        import chromadb
        print(f"  ✓ chromadb (optional)")
    except ImportError:
        print(f"  ℹ chromadb not installed (optional - use local storage)")
    
    if all_ok:
        print("\n✓ All required packages installed")
    else:
        print("\n✗ Missing required packages")
        return False
    
    return True


def test_3_pdf_files():
    """Test 3: Check for PDF files."""
    print("\n" + "="*80)
    print("TEST 3: PDF Files")
    print("="*80)
    
    docs_path = "./financial_docs"
    
    if not os.path.exists(docs_path):
        print(f"  ✗ Directory {docs_path} does not exist")
        print(f"  Creating directory...")
        os.makedirs(docs_path)
        print(f"  ✓ Directory created")
        print(f"\n  ⚠ Please add PDF files to {docs_path} and run again")
        return False
    
    pdf_files = list(Path(docs_path).rglob("*.pdf"))
    
    if not pdf_files:
        print(f"  ✗ No PDF files found in {docs_path}")
        print(f"\n  ⚠ Please add PDF files and run again")
        return False
    
    print(f"  ✓ Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files[:5]:  # Show first 5
        print(f"    - {pdf.name} ({pdf.stat().st_size / 1024:.1f} KB)")
    
    if len(pdf_files) > 5:
        print(f"    ... and {len(pdf_files) - 5} more")
    
    return True


def test_4_pdf_extraction():
    """Test 4: Test PDF text extraction."""
    print("\n" + "="*80)
    print("TEST 4: PDF Text Extraction")
    print("="*80)
    
    try:
        import pdfplumber
    except ImportError:
        print("  ✗ pdfplumber not installed")
        return False
    
    docs_path = "./financial_docs"
    pdf_files = list(Path(docs_path).rglob("*.pdf"))
    
    if not pdf_files:
        print("  ⚠ No PDF files to test")
        return False
    
    test_pdf = pdf_files[0]
    print(f"  Testing: {test_pdf.name}")
    
    try:
        with pdfplumber.open(test_pdf) as pdf:
            print(f"  ✓ PDF opened successfully")
            print(f"  ✓ Pages: {len(pdf.pages)}")
            
            if len(pdf.pages) > 0:
                page = pdf.pages[0]
                
                # Test text extraction
                text = page.extract_text()
                if text:
                    print(f"  ✓ Text extraction works ({len(text)} characters)")
                    print(f"\n  Sample text:")
                    print(f"    {text[:200]}...")
                else:
                    print(f"  ⚠ No text extracted (may be scanned PDF)")
                
                # Test word extraction
                words = page.extract_words()
                if words:
                    print(f"  ✓ Word extraction works ({len(words)} words)")
                else:
                    print(f"  ⚠ No words extracted")
                
                # Test table extraction
                tables = page.extract_tables()
                print(f"  ✓ Table extraction works ({len(tables)} tables)")
                
                return True
    
    except Exception as e:
        print(f"  ✗ PDF extraction failed: {e}")
        return False


def test_5_azure_connection():
    """Test 5: Test Azure OpenAI connection."""
    print("\n" + "="*80)
    print("TEST 5: Azure OpenAI Connection")
    print("="*80)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from llama_index.llms.azure_openai import AzureOpenAI
        
        llm = AzureOpenAI(
            model="gpt-4",
            deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-02-15-preview",
            max_tokens=50
        )
        
        print("  ✓ LLM initialized")
        
        # Test completion
        print("  Testing LLM call...")
        response = llm.complete("Say 'hello' in one word")
        print(f"  ✓ LLM responds: {str(response).strip()}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Azure OpenAI connection failed: {e}")
        print(f"\n  Check:")
        print(f"    - Endpoint URL is correct")
        print(f"    - API key is valid")
        print(f"    - Deployment name matches Azure portal")
        return False


def test_6_embeddings():
    """Test 6: Test embeddings."""
    print("\n" + "="*80)
    print("TEST 6: Azure OpenAI Embeddings")
    print("="*80)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
        
        embed_model = AzureOpenAIEmbedding(
            model="text-embedding-3-large",
            deployment_name=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-02-15-preview"
        )
        
        print("  ✓ Embedding model initialized")
        
        # Test embedding
        print("  Testing embedding call...")
        embedding = embed_model.get_text_embedding("test")
        print(f"  ✓ Embedding created (dimension: {len(embedding)})")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Embeddings failed: {e}")
        print(f"\n  Check:")
        print(f"    - Embedding deployment name is correct")
        print(f"    - Model supports embeddings")
        return False


def test_7_full_pipeline():
    """Test 7: Test full RAG pipeline."""
    print("\n" + "="*80)
    print("TEST 7: Full RAG Pipeline")
    print("="*80)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        from spatial_block_rag_system import SpatialBlockRAG
        
        print("  Creating RAG system...")
        rag = SpatialBlockRAG(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
            azure_embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT"),
            use_vector_db="local",
            debug=False  # Less verbose for test
        )
        
        print("  ✓ RAG system created")
        
        # Try to load or create index
        print("\n  Checking for existing index...")
        if rag.load_index():
            print("  ✓ Index loaded from disk")
        else:
            print("  Creating new index (this will take a few minutes)...")
            rag.create_initial_index("./financial_docs")
            print("  ✓ Index created")
        
        # Test query
        print("\n  Creating query engine...")
        rag.create_query_engine()
        print("  ✓ Query engine created")
        
        print("\n  Testing query...")
        response = rag.query("What is the revenue?", debug=False)
        
        if response and len(response) > 10:
            print(f"  ✓ Query successful")
            print(f"\n  Response preview:")
            print(f"    {response[:200]}...")
            return True
        else:
            print(f"  ⚠ Query returned empty or short response")
            print(f"    Response: {response}")
            return False
        
    except Exception as e:
        print(f"  ✗ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all diagnostic tests."""
    
    print("\n" + "="*80)
    print("RAG SYSTEM DIAGNOSTIC TEST")
    print("="*80)
    print("\nThis script will test your setup step-by-step")
    print("to identify any issues.\n")
    
    tests = [
        ("Environment Variables", test_1_environment),
        ("Required Packages", test_2_packages),
        ("PDF Files", test_3_pdf_files),
        ("PDF Extraction", test_4_pdf_extraction),
        ("Azure OpenAI Connection", test_5_azure_connection),
        ("Embeddings", test_6_embeddings),
        ("Full Pipeline", test_7_full_pipeline),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            
            if not result:
                print(f"\n⚠ Test failed: {name}")
                print(f"  Fix this issue before continuing to next tests")
                
                # Ask if user wants to continue
                if input("\nContinue to next test? (y/n): ").lower() != 'y':
                    break
        
        except Exception as e:
            print(f"\n✗ Test crashed: {name}")
            print(f"  Error: {e}")
            results.append((name, False))
            
            if input("\nContinue to next test? (y/n): ").lower() != 'y':
                break
    
    # Summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Your setup is working correctly.")
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Missing .env file: Create one with Azure credentials")
        print("  - No PDFs: Add PDF files to ./financial_docs/")
        print("  - Packages missing: pip install -r requirements.txt")
        print("  - API errors: Check Azure credentials and deployment names")


if __name__ == "__main__":
    main()
