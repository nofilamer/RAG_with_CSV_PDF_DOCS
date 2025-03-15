import os
import logging
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_command(command, description=None):
    """Run a shell command and print its output."""
    if description:
        print(f"\n{description}")
    
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    return True

def main():
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    
    print("=" * 80)
    print("DOCUMENT EMBEDDING DEMO WORKFLOW")
    print("=" * 80)
    
    print("\nThis script will guide you through the entire workflow of:")
    print("1. Generating sample PDF and DOCX files")
    print("2. Processing and embedding them")
    print("3. Searching the embeddings")
    
    # Step 1: Generate sample documents
    print("\n" + "=" * 30)
    print("STEP 1: GENERATING SAMPLE DOCUMENTS")
    print("=" * 30)
    
    run_command(f"python {project_root}/app/generate_sample_documents.py", 
                "Generating sample PDF and DOCX files...")
    
    pdf_path = data_dir / 'ecommerce_technical_docs.pdf'
    docx_path = data_dir / 'ecommerce_returns_policy.docx'
    
    if not pdf_path.exists() or not docx_path.exists():
        print("Error: Sample documents could not be generated. Exiting.")
        return
    
    # Step 2: Setup document tables and indexes
    print("\n" + "=" * 30)
    print("STEP 2: SETTING UP DATABASE TABLES")
    print("=" * 30)
    
    run_command(f"python {project_root}/app/insert_document_vectors.py setup",
                "Setting up document database tables and indexes...")
    
    # Step 3: Process and embed PDF
    print("\n" + "=" * 30)
    print("STEP 3: PROCESSING PDF DOCUMENT")
    print("=" * 30)
    
    run_command(f"python {project_root}/app/insert_document_vectors.py pdf {pdf_path}",
                "Processing and embedding PDF document...")
    
    # Step 4: Interactive search
    print("\n" + "=" * 30)
    print("STEP 4: INTERACTIVE SEARCH")
    print("=" * 30)
    
    print("\nNow you can search the document embeddings interactively.")
    print("Sample search queries you might try:")
    print("1. 'What is the database architecture?'")
    print("2. 'How does authentication work?'")
    print("3. 'What is the disaster recovery plan?'")
    
    while True:
        choice = input("\nDo you want to start the interactive search? (y/n): ").strip().lower()
        if choice == 'y':
            run_command(f"python {project_root}/app/document_search.py interactive")
            break
        elif choice == 'n':
            print("Skipping interactive search.")
            break
        else:
            print("Please enter 'y' or 'n'.")
    
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)
    
    print("\nSummary of what was accomplished:")
    print("1. Generated sample PDF and DOCX files")
    print("2. Set up document database tables and indexes")
    print("3. Processed and embedded PDF document")
    print("4. Provided interactive search capability")
    
    print("\nTo run the interactive search again later:")
    print(f"python {project_root}/app/document_search.py interactive")

if __name__ == "__main__":
    main()