import argparse
import logging
import os
import tempfile
import uuid
from pathlib import Path
import pandas as pd

from database.document_store import DocumentStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def setup_document_store():
    """Initialize and set up the document store tables and indexes."""
    doc_store = DocumentStore()
    doc_store.create_tables()
    doc_store.create_indexes()
    return doc_store


def process_pdf_directory(doc_store, directory_path):
    """
    Process all PDF files in the specified directory.
    
    Args:
        doc_store: The DocumentStore instance
        directory_path: Path to directory containing PDF files
    """
    directory = Path(directory_path)
    if not directory.exists():
        logging.error(f"Directory not found: {directory}")
        return
    
    pdf_files = list(directory.glob("*.pdf"))
    logging.info(f"Found {len(pdf_files)} PDF files in {directory}")
    
    for pdf_file in pdf_files:
        logging.info(f"Processing PDF: {pdf_file.name}")
        try:
            # Process the PDF file
            pdf_df = doc_store.process_pdf(pdf_file)
            logging.info(f"Extracted {len(pdf_df)} chunks from {pdf_file.name}")
            
            # Store the embeddings
            doc_store.store_pdf_embeddings(pdf_df)
            logging.info(f"Stored embeddings for {pdf_file.name}")
        except Exception as e:
            logging.error(f"Error processing {pdf_file.name}: {e}")


def process_single_pdf(doc_store, pdf_path):
    """
    Process a single PDF file.
    
    Args:
        doc_store: The DocumentStore instance
        pdf_path: Path to the PDF file
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        logging.error(f"PDF file not found: {pdf_path}")
        return
    
    logging.info(f"Processing PDF: {pdf_path.name}")
    try:
        # Process the PDF file
        pdf_df = doc_store.process_pdf(pdf_path)
        logging.info(f"Extracted {len(pdf_df)} chunks from {pdf_path.name}")
        
        # Store the embeddings
        doc_store.store_pdf_embeddings(pdf_df)
        logging.info(f"Stored embeddings for {pdf_path.name}")
    except Exception as e:
        logging.error(f"Error processing {pdf_path.name}: {e}")

def process_single_docx(doc_store, docx_path):
    """
    Process a single DOCX file.
    
    Args:
        doc_store: The DocumentStore instance
        docx_path: Path to the DOCX file
    """
    docx_path = Path(docx_path)
    if not docx_path.exists():
        logging.error(f"DOCX file not found: {docx_path}")
        return
    
    logging.info(f"Processing DOCX: {docx_path.name}")
    try:
        # For now, we'll process DOCX files as PDF files since we don't have
        # a specific DOCX processor yet
        import docx
        
        # Extract text from DOCX
        doc = docx.Document(docx_path)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        
        # Create temporary file with the extracted text
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp:
            temp.write(full_text)
            temp_path = temp.name
            
        # Create fake PDF path for metadata
        pdf_path = docx_path
        
        # Get metadata
        metadata = {
            "filename": docx_path.name,
            "filesize": docx_path.stat().st_size,
            "filetype": "docx",
            "last_modified": os.path.getmtime(docx_path)
        }
        
        # Process text in chunks
        chunk_size = 1000
        chunks = []
        
        for i in range(0, len(full_text), chunk_size):
            chunk_text = full_text[i:i+chunk_size]
            if chunk_text.strip():  # Skip empty chunks
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_id"] = i // chunk_size
                chunk_metadata["char_start"] = i
                chunk_metadata["char_end"] = min(i + chunk_size, len(full_text))
                
                # Get embedding for this chunk
                embedding = doc_store.get_embedding(chunk_text)
                
                # Use UUID version 1 (time-based) for TimescaleDB compatibility
                chunks.append({
                    "id": str(uuid.uuid1()),
                    "metadata": chunk_metadata,
                    "contents": chunk_text,
                    "embedding": embedding
                })
        
        docx_df = pd.DataFrame(chunks)
        logging.info(f"Extracted {len(docx_df)} chunks from {docx_path.name}")
        
        # Store the embeddings
        doc_store.store_doc_embeddings(docx_df)
        logging.info(f"Stored embeddings for {docx_path.name}")
        
        # Clean up temporary file
        os.unlink(temp_path)
        
    except Exception as e:
        logging.error(f"Error processing {docx_path.name}: {e}")


def process_google_doc(doc_store, doc_id):
    """
    Process a Google Doc by its ID.
    
    Args:
        doc_store: The DocumentStore instance
        doc_id: The Google Doc ID
    """
    logging.info(f"Processing Google Doc with ID: {doc_id}")
    try:
        # Process the Google Doc
        doc_df = doc_store.process_gdoc(doc_id)
        logging.info(f"Extracted {len(doc_df)} chunks from Google Doc {doc_id}")
        
        # Store the embeddings
        doc_store.store_doc_embeddings(doc_df)
        logging.info(f"Stored embeddings for Google Doc {doc_id}")
    except NotImplementedError:
        logging.error("Google Docs API credentials not configured. Please set up credentials first.")
    except Exception as e:
        logging.error(f"Error processing Google Doc {doc_id}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Process and embed documents.")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up document database tables and indexes")
    
    # PDF directory command
    pdf_dir_parser = subparsers.add_parser("pdf-dir", help="Process all PDFs in a directory")
    pdf_dir_parser.add_argument("directory", help="Directory containing PDF files")
    
    # Single PDF command
    pdf_parser = subparsers.add_parser("pdf", help="Process a single PDF file")
    pdf_parser.add_argument("file", help="Path to PDF file")
    
    # Single DOCX command
    docx_parser = subparsers.add_parser("docx", help="Process a single DOCX file")
    docx_parser.add_argument("file", help="Path to DOCX file")
    
    # Google Doc command
    gdoc_parser = subparsers.add_parser("gdoc", help="Process a Google Doc")
    gdoc_parser.add_argument("doc_id", help="Google Doc ID")
    
    args = parser.parse_args()
    
    # Initialize document store
    doc_store = DocumentStore()
    
    if args.command == "setup":
        logging.info("Setting up document store tables and indexes...")
        doc_store.create_tables()
        doc_store.create_indexes()
        logging.info("Setup complete.")
    
    elif args.command == "pdf-dir":
        process_pdf_directory(doc_store, args.directory)
    
    elif args.command == "pdf":
        process_single_pdf(doc_store, args.file)
        
    elif args.command == "docx":
        process_single_docx(doc_store, args.file)
    
    elif args.command == "gdoc":
        process_google_doc(doc_store, args.doc_id)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()