import argparse
import logging
from database.document_store import DocumentStore
from services.synthesizer import Synthesizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def search_documents(query, doc_type=None, limit=5):
    """
    Search document embeddings for the given query.
    
    Args:
        query: The search query
        doc_type: Type of document to search ('pdf', 'doc', or None for both)
        limit: Maximum number of results to return
    """
    doc_store = DocumentStore()
    
    logging.info(f"Searching for: {query}")
    logging.info(f"Document type: {doc_type if doc_type else 'All'}")
    
    if doc_type == "pdf":
        results = doc_store.search_pdfs(query, limit=limit)
    elif doc_type == "doc":
        results = doc_store.search_docs(query, limit=limit)
    else:
        results = doc_store.search_all_documents(query, limit=limit)
    
    if results.empty:
        print("No results found.")
        return
    
    # Display search results
    print("\n===== Search Results =====")
    for idx, row in results.iterrows():
        print(f"\n--- Result {idx+1} (Distance: {row['distance']:.4f}) ---")
        print(f"Document: {row.get('filename', 'Unknown')}")
        print(f"Type: {row.get('filetype', 'Unknown')}")
        
        # Print a preview of the content (first 200 chars)
        content_preview = row['content'][:200] + "..." if len(row['content']) > 200 else row['content']
        print(f"Content Preview: {content_preview}")
    
    # Generate synthesized response
    response = Synthesizer.generate_response(question=query, context=results)
    
    print("\n===== Synthesized Answer =====")
    print(response.answer)
    
    print("\nThought process:")
    for thought in response.thought_process:
        print(f"- {thought}")
    
    print(f"\nEnough context: {response.enough_context}")


def interactive_search():
    """Run an interactive search session."""
    doc_store = DocumentStore()
    
    print("\n===== Document Search System =====")
    print("Type 'exit' to quit")
    
    while True:
        query = input("\nEnter your query: ").strip()
        if query.lower() == 'exit':
            break
        
        doc_type = input("Search in (pdf/doc/all): ").strip().lower()
        if doc_type not in ['pdf', 'doc', 'all', '']:
            print("Invalid document type. Using 'all'.")
            doc_type = None
        elif doc_type == 'all' or doc_type == '':
            doc_type = None
        
        limit = input("Number of results (default: 5): ").strip()
        try:
            limit = int(limit) if limit else 5
        except ValueError:
            print("Invalid limit. Using default: 5")
            limit = 5
        
        if doc_type == "pdf":
            results = doc_store.search_pdfs(query, limit=limit)
        elif doc_type == "doc":
            results = doc_store.search_docs(query, limit=limit)
        else:
            results = doc_store.search_all_documents(query, limit=limit)
        
        if results.empty:
            print("No results found.")
            continue
        
        # Display search results
        print("\n===== Search Results =====")
        for idx, row in results.iterrows():
            print(f"\n--- Result {idx+1} (Distance: {row['distance']:.4f}) ---")
            print(f"Document: {row.get('filename', 'Unknown')}")
            print(f"Type: {row.get('filetype', 'Unknown')}")
            
            # Print a preview of the content (first 200 chars)
            content_preview = row['content'][:200] + "..." if len(row['content']) > 200 else row['content']
            print(f"Content Preview: {content_preview}")
        
        # Generate synthesized response
        response = Synthesizer.generate_response(question=query, context=results)
        
        print("\n===== Synthesized Answer =====")
        print(response.answer)
        
        print("\nThought process:")
        for thought in response.thought_process:
            print(f"- {thought}")
        
        print(f"\nEnough context: {response.enough_context}")


def main():
    parser = argparse.ArgumentParser(description="Search document embeddings.")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search document embeddings")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", choices=["pdf", "doc"], help="Document type to search")
    search_parser.add_argument("--limit", type=int, default=5, help="Maximum number of results")
    
    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Interactive search session")
    
    args = parser.parse_args()
    
    if args.command == "search":
        search_documents(args.query, args.type, args.limit)
    
    elif args.command == "interactive":
        interactive_search()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()