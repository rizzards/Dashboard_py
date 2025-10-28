"""
Ready-to-Run Example: Financial RAG System
Complete workflow from setup to queries
"""

import os
from dotenv import load_dotenv
from unified_financial_rag import UnifiedFinancialRAG

# Load environment variables
load_dotenv()


def initialize_rag():
    """Initialize the RAG system."""
    print("="*80)
    print("INITIALIZING FINANCIAL RAG SYSTEM")
    print("="*80)
    
    rag = UnifiedFinancialRAG(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4"),
        azure_embedding_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"),
        persist_dir="./storage",
        cache_dir="./cache",
        use_vector_db="chroma",  # Change to "local" if ChromaDB not installed
        enable_chart_analysis=True  # Set to False to disable chart analysis
    )
    
    print("✓ RAG system initialized")
    return rag


def setup_index(rag, docs_path="./financial_docs"):
    """Set up or load the index."""
    print("\n" + "="*80)
    print("INDEX SETUP")
    print("="*80)
    
    # Try to load existing index
    if rag.load_index():
        print("✓ Loaded existing index from disk")
        
        # Check for new/modified documents
        print("\nChecking for updates...")
        stats = rag.incremental_update(docs_path, extract_images=True)
        
        if stats['new'] > 0 or stats['modified'] > 0:
            print(f"✓ Processed {stats['new']} new and {stats['modified']} modified documents")
        else:
            print("✓ All documents up to date")
    else:
        print("No existing index found. Creating new index...")
        print("⏳ This may take several minutes on first run...\n")
        
        # Create initial index
        rag.create_initial_index(docs_path, extract_images=True)
        print("\n✓ Index created and saved to disk")
        print("   Future runs will load instantly!")
    
    return rag


def demo_queries(rag):
    """Run example queries to demonstrate capabilities."""
    print("\n" + "="*80)
    print("DEMO QUERIES")
    print("="*80)
    
    # Create query engine
    rag.create_query_engine(
        similarity_top_k=5,
        similarity_cutoff=0.7
    )
    
    queries = [
        {
            'name': 'Q1 2024 Revenue Analysis',
            'query': 'What was the revenue performance in Q1 2024? Include key drivers and growth rates.',
            'filters': {'quarter': 'Q1', 'year': '2024'}
        },
        {
            'name': 'Profitability Metrics',
            'query': 'Summarize EBITDA margins and operating efficiency metrics',
            'filters': {'year': '2024', 'slide_type': 'profitability'}
        },
        {
            'name': 'Table Data Extraction',
            'query': 'What financial metrics are shown in the tables? Provide specific numbers.',
            'filters': {'quarter': 'Q2', 'year': '2024'}
        },
        {
            'name': 'Strategic Initiatives',
            'query': 'What were the main strategic initiatives and their expected outcomes?',
            'filters': {'year': '2024', 'slide_type': 'strategy'}
        },
        {
            'name': 'Year-over-Year Comparison',
            'query': 'Compare performance metrics between Q1 and Q2 2024',
            'filters': {'year': '2024'}
        }
    ]
    
    for i, q in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {q['name']}")
        print(f"{'='*80}")
        print(f"Question: {q['query']}")
        
        if q['filters']:
            print(f"Filters: {q['filters']}")
        
        print("\nProcessing...")
        
        try:
            response = rag.query_with_filters(
                query=q['query'],
                use_cache=True,
                **q['filters']
            )
            
            print("\nAnswer:")
            print("-" * 80)
            # Print first 800 characters
            print(response[:800])
            if len(response) > 800:
                print(f"\n... ({len(response) - 800} more characters)")
            print("-" * 80)
            
        except Exception as e:
            print(f"Error: {e}")


def show_statistics(rag):
    """Show statistics about the indexed documents."""
    print("\n" + "="*80)
    print("SYSTEM STATISTICS")
    print("="*80)
    
    if not rag.doc_registry:
        print("No documents indexed yet.")
        return
    
    total_docs = len(rag.doc_registry)
    total_slides = sum(doc.get('num_slides', 0) for doc in rag.doc_registry.values())
    
    print(f"Total PDF Documents: {total_docs}")
    print(f"Total Slides: {total_slides}")
    print(f"Average Slides per Document: {total_slides/total_docs:.1f}")
    
    # Quarter breakdown
    quarters = {}
    for doc_info in rag.doc_registry.values():
        quarter_year = doc_info['metadata'].get('quarter_year', 'Unknown')
        quarters[quarter_year] = quarters.get(quarter_year, 0) + 1
    
    if quarters:
        print("\nDocuments by Quarter:")
        for qy, count in sorted(quarters.items()):
            print(f"  {qy}: {count} document(s)")
    
    # Document types
    doc_types = {}
    for doc_info in rag.doc_registry.values():
        dtype = doc_info['metadata'].get('doc_type', 'Unknown')
        doc_types[dtype] = doc_types.get(dtype, 0) + 1
    
    if doc_types:
        print("\nDocuments by Type:")
        for dtype, count in sorted(doc_types.items()):
            print(f"  {dtype}: {count} document(s)")
    
    print(f"\nCache Entries: {len(rag.query_cache)}")


def interactive_mode(rag):
    """Interactive query mode."""
    print("\n" + "="*80)
    print("INTERACTIVE MODE")
    print("="*80)
    print("Ask questions about your financial documents.")
    print("Type 'quit' or 'exit' to stop.")
    print("Type 'stats' to see statistics.")
    print("="*80)
    
    rag.create_query_engine()
    
    while True:
        print("\n" + "-"*80)
        user_query = input("Your question: ").strip()
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if user_query.lower() == 'stats':
            show_statistics(rag)
            continue
        
        if not user_query:
            continue
        
        # Optional: Ask for filters
        print("\nOptional filters (press Enter to skip):")
        quarter = input("  Quarter (Q1, Q2, Q3, Q4): ").strip().upper() or None
        year = input("  Year (e.g., 2024): ").strip() or None
        
        print("\nSearching...")
        
        try:
            response = rag.query_with_filters(
                query=user_query,
                quarter=quarter,
                year=year,
                use_cache=True
            )
            
            print("\nAnswer:")
            print("="*80)
            print(response)
            print("="*80)
            
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main workflow."""
    
    # Check environment
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        print("ERROR: Please set up your .env file with Azure credentials!")
        print("See the installation guide for details.")
        return
    
    # Check for documents
    docs_path = "./financial_docs"
    if not os.path.exists(docs_path):
        os.makedirs(docs_path)
        print(f"\nCreated {docs_path} directory.")
        print("Please add your PDF files there and run again.")
        return
    
    pdf_files = list(Path(docs_path).rglob("*.pdf"))
    if not pdf_files:
        print(f"\nNo PDF files found in {docs_path}")
        print("Please add your financial slide PDFs and run again.")
        return
    
    print(f"\nFound {len(pdf_files)} PDF file(s) in {docs_path}")
    
    # Initialize
    rag = initialize_rag()
    
    # Setup index
    rag = setup_index(rag, docs_path)
    
    # Show statistics
    show_statistics(rag)
    
    # Demo queries
    print("\n" + "="*80)
    print("DEMO MODE")
    print("="*80)
    print("1. Run demo queries")
    print("2. Interactive mode")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        demo_queries(rag)
    elif choice == "2":
        interactive_mode(rag)
    else:
        print("Exiting...")
    
    print("\n" + "="*80)
    print("SESSION COMPLETE")
    print("="*80)
    print("Key points:")
    print("- Index is saved to ./storage/ (no need to re-index)")
    print("- Queries are cached in ./cache/ (faster on repeat)")
    print("- Run again anytime - it will load instantly!")
    print("\nNext time:")
    print("- Add new PDFs to ./financial_docs/")
    print("- Run this script - only new files will be processed")


if __name__ == "__main__":
    from pathlib import Path
    main()
