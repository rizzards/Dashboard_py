"""
Complete Integrated System
Combines spatial block extraction + entity-aware retrieval
Ready-to-use production system
"""

import os
from dotenv import load_dotenv

# Import both systems
from spatial_block_rag_system import SpatialBlockRAG
from advanced_query_optimizer import integrate_entity_aware_retrieval, EntityExtractor


def main():
    """
    Complete workflow demonstrating the integrated system.
    """
    
    load_dotenv()
    
    print("="*80)
    print("COMPLETE INTEGRATED RAG SYSTEM")
    print("Spatial Block Extraction + Entity-Aware Retrieval")
    print("="*80)
    
    # ==================== STEP 1: Initialize ====================
    print("\n" + "="*80)
    print("STEP 1: Initialize RAG System")
    print("="*80)
    
    rag = SpatialBlockRAG(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4"),
        azure_embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"),
        use_vector_db="local",
        debug=True
    )
    
    # ==================== STEP 2: Load/Create Index ====================
    print("\n" + "="*80)
    print("STEP 2: Load or Create Index")
    print("="*80)
    
    if not rag.load_index():
        print("\nNo existing index found. Creating new index...")
        rag.create_initial_index("./financial_docs")
    else:
        print("\nIndex loaded successfully!")
        print("Checking for updates...")
        # Could add incremental update here if needed
    
    # ==================== STEP 3: Enable Entity-Aware Retrieval ====================
    print("\n" + "="*80)
    print("STEP 3: Enable Entity-Aware Retrieval")
    print("="*80)
    
    integrate_entity_aware_retrieval(rag, debug=True)
    
    print("\n✓ System ready with:")
    print("  - Spatial block extraction (handles mixed-topic slides)")
    print("  - Special character normalization (P&L, M&A, etc.)")
    print("  - Entity-aware retrieval (multi-division, multi-date)")
    
    # ==================== STEP 4: Test Queries ====================
    print("\n" + "="*80)
    print("STEP 4: Test Different Query Types")
    print("="*80)
    
    test_queries = [
        {
            'name': 'Multi-Division Query',
            'query': 'What is the P&L summary for Q4 2024?',
            'expected': 'Should cover ALL divisions'
        },
        {
            'name': 'Specific Query',
            'query': 'Technology division revenue in Q4 2024',
            'expected': 'Should focus on Tech only'
        },
        {
            'name': 'Multi-Date Query',
            'query': 'Compare P&L performance between Q3 and Q4 2024',
            'expected': 'Should cover both quarters for all divisions'
        },
        {
            'name': 'Comprehensive Query',
            'query': 'Show me Tech and Healthcare EBITDA margins for Q3 and Q4',
            'expected': 'Should cover 2 divisions × 2 quarters = 4 combinations'
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'='*80}")
        print(f"Query: {test['query']}")
        print(f"Expected: {test['expected']}")
        print(f"\n{'-'*80}")
        
        # Show entity detection
        entities = EntityExtractor.extract_entities(test['query'])
        query_type = EntityExtractor.detect_query_type(entities)
        
        print(f"\nDetected Query Type: {query_type}")
        if entities.get('divisions'):
            divs = [e.normalized for e in entities['divisions']]
            print(f"Divisions: {divs}")
        if entities.get('quarters'):
            quarters = [e.value for e in entities['quarters']]
            print(f"Quarters: {quarters}")
        if entities.get('years'):
            years = [e.value for e in entities['years']]
            print(f"Years: {years}")
        
        print(f"\n{'-'*80}")
        print("Response:")
        print(f"{'-'*80}\n")
        
        try:
            response = rag.query(test['query'], debug_mode=True)
            
            # Print first 500 chars
            print(response[:500])
            if len(response) > 500:
                print(f"\n... ({len(response) - 500} more characters)")
            
            print(f"\n{'-'*80}")
            print(f"✓ Query {i} completed")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # ==================== STEP 5: Interactive Mode ====================
    print("\n" + "="*80)
    print("STEP 5: Interactive Query Mode")
    print("="*80)
    print("\nYou can now ask questions about your financial data.")
    print("The system will automatically:")
    print("  - Extract entities (divisions, dates)")
    print("  - Choose optimal retrieval strategy")
    print("  - Ensure comprehensive coverage")
    print("\nType 'quit' to exit.\n")
    
    while True:
        try:
            user_query = input("Your question: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if not user_query:
                continue
            
            # Show what the system detected
            print(f"\n{'-'*80}")
            entities = EntityExtractor.extract_entities(user_query)
            query_type = EntityExtractor.detect_query_type(entities)
            print(f"Detected: {query_type} query")
            
            if entities.get('divisions'):
                print(f"  Divisions: {[e.normalized for e in entities['divisions']]}")
            if entities.get('quarters'):
                print(f"  Quarters: {[e.value for e in entities['quarters']]}")
            
            print(f"{'-'*80}\n")
            
            # Execute query
            response = rag.query(user_query, debug_mode=False)  # Less verbose in interactive
            
            print("Response:")
            print(f"{'-'*80}")
            print(response)
            print(f"{'-'*80}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}\n")


def quick_setup():
    """
    Quick setup for first-time users.
    """
    
    print("="*80)
    print("QUICK SETUP")
    print("="*80)
    
    # Check environment
    load_dotenv()
    
    required_vars = {
        'AZURE_OPENAI_ENDPOINT': os.getenv('AZURE_OPENAI_ENDPOINT'),
        'AZURE_OPENAI_API_KEY': os.getenv('AZURE_OPENAI_API_KEY'),
        'AZURE_DEPLOYMENT_NAME': os.getenv('AZURE_DEPLOYMENT_NAME'),
        'AZURE_EMBEDDING_DEPLOYMENT': os.getenv('AZURE_EMBEDDING_DEPLOYMENT')
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    
    if missing:
        print("\n✗ Missing environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease create .env file with your Azure OpenAI credentials")
        return False
    
    print("\n✓ Environment variables configured")
    
    # Check for PDFs
    docs_path = "./financial_docs"
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)
        print(f"\n✓ Created {docs_path} directory")
        print(f"  Please add your PDF files there")
        return False
    
    from pathlib import Path
    pdf_files = list(Path(docs_path).rglob("*.pdf"))
    
    if not pdf_files:
        print(f"\n✗ No PDF files found in {docs_path}")
        print("  Please add PDF files and run again")
        return False
    
    print(f"\n✓ Found {len(pdf_files)} PDF files")
    
    # Check for existing index
    if os.path.exists("./storage/docstore.json"):
        print("\n✓ Existing index found")
    else:
        print("\n⚠ No existing index")
        print("  First run will create index (takes 5-10 minutes)")
    
    print("\n" + "="*80)
    print("Ready to start!")
    print("="*80)
    
    return True


def show_configuration_options():
    """Show available configuration options."""
    
    print("\n" + "="*80)
    print("CONFIGURATION OPTIONS")
    print("="*80)
    
    print("""
# Basic Configuration
rag = SpatialBlockRAG(
    azure_endpoint="...",
    azure_api_key="...",
    azure_deployment_name="gpt-4",
    azure_embedding_deployment="text-embedding-3-large",
    use_vector_db="local",  # or "chroma"
    debug=True              # Enable detailed logging
)

# Entity-Aware Retrieval Settings
from advanced_query_optimizer import EntityAwareRetriever

retriever = EntityAwareRetriever(
    index=rag.index,
    
    # Results per entity (division/date combination)
    entities_per_query=3,
    # - Set to 2 for faster, more concise
    # - Set to 5 for more comprehensive
    
    # Base retrieval for general queries
    base_top_k=5,
    # - Standard: 5
    # - Comprehensive: 10
    
    debug=True
)

# Chunk Size (affects context length)
from llama_index.core import Settings

Settings.chunk_size = 512      # Standard for financial docs
Settings.chunk_overlap = 50    # Good balance

# Query Engine Settings
rag.create_query_engine(
    similarity_top_k=7,         # Number of chunks to retrieve
    similarity_cutoff=0.6       # Minimum similarity threshold
)

# For better coverage, use:
rag.create_query_engine(
    similarity_top_k=10,        # More results
    similarity_cutoff=0.5       # Lower threshold
)
""")


if __name__ == "__main__":
    
    # Check setup first
    if not quick_setup():
        print("\nPlease complete setup and run again.")
        exit(1)
    
    # Show configuration options
    show_configuration = input("\nShow configuration options? (y/n): ").lower()
    if show_configuration == 'y':
        show_configuration_options()
    
    # Run main demo
    run_demo = input("\nRun demo? (y/n): ").lower()
    if run_demo == 'y':
        main()
    else:
        print("\nTo run manually:")
        print("  from complete_integrated_system import main")
        print("  main()")
