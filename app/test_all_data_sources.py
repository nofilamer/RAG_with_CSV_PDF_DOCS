#!/usr/bin/env python3
"""
Test script for querying data from all available data sources:
1. Original FAQ dataset (CSV)
2. PDF documents
3. DOCX documents

This script runs multiple sample queries against each data source 
and across all data sources to show how the vector search works.
"""

import logging
import argparse
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel

from database.vector_store import VectorStore
from database.document_store import DocumentStore
from services.synthesizer import Synthesizer
from timescale_vector import client

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
console = Console()

# Initialize vector stores
faq_store = VectorStore()
doc_store = DocumentStore()

def divider(title):
    """Print a divider with a title."""
    console.print(f"\n[bold yellow]{'=' * 20} {title} {'=' * 20}[/bold yellow]\n")

def run_query(query, source_type=None, metadata_filter=None, limit=3):
    """
    Run a query against the specified data source.
    
    Args:
        query: The search query
        source_type: The type of source to query ('faq', 'pdf', 'doc', or None for all)
        metadata_filter: Optional metadata filter
        limit: Maximum number of results
    """
    console.print(f"[bold cyan]Query:[/bold cyan] {query}")
    console.print(f"[bold cyan]Source:[/bold cyan] {source_type if source_type else 'All'}")
    
    if source_type == 'faq':
        # Search in original FAQ dataset
        results = faq_store.search(query, limit=limit, metadata_filter=metadata_filter)
        display_faq_results(results)
        response = Synthesizer.generate_response(question=query, context=results)
    elif source_type == 'pdf':
        # Search in PDF documents
        results = doc_store.search_pdfs(query, limit=limit, metadata_filter=metadata_filter)
        display_doc_results(results)
        response = Synthesizer.generate_response(question=query, context=results)
    elif source_type == 'doc':
        # Search in DOCX documents
        results = doc_store.search_docs(query, limit=limit, metadata_filter=metadata_filter)
        display_doc_results(results)
        response = Synthesizer.generate_response(question=query, context=results)
    else:
        # Search across all data sources
        # First, search in the FAQ dataset
        faq_results = faq_store.search(query, limit=limit, metadata_filter=metadata_filter)
        
        # Then, search in PDF documents
        pdf_results = doc_store.search_pdfs(query, limit=limit, metadata_filter=metadata_filter)
        
        # Then, search in DOCX documents
        doc_results = doc_store.search_docs(query, limit=limit, metadata_filter=metadata_filter)
        
        # Display results from all sources
        console.print("\n[bold green]Results from FAQ dataset:[/bold green]")
        display_faq_results(faq_results)
        
        console.print("\n[bold green]Results from PDF documents:[/bold green]")
        display_doc_results(pdf_results)
        
        console.print("\n[bold green]Results from DOCX documents:[/bold green]")
        display_doc_results(doc_results)
        
        # Combine results for synthesis
        # Take top results from each source based on distance
        # For simplicity, we'll just use the PDF results for the answer
        results = pdf_results if not pdf_results.empty else doc_results
        if not results.empty:
            response = Synthesizer.generate_response(question=query, context=results)
        else:
            response = None
    
    # Display synthesized answer
    if response:
        console.print("\n[bold green]Synthesized Answer:[/bold green]")
        console.print(Panel(Markdown(response.answer)))
        
        console.print("\n[bold green]Thought Process:[/bold green]")
        for thought in response.thought_process:
            console.print(f"- {thought}")
        
        console.print(f"\n[bold cyan]Enough Context:[/bold cyan] {response.enough_context}")


def display_faq_results(results):
    """Display results from the FAQ dataset in a table."""
    if results.empty:
        console.print("[italic]No results found.[/italic]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Distance")
    table.add_column("Question")
    table.add_column("Answer")
    table.add_column("Category")
    
    for _, row in results.iterrows():
        table.add_row(
            f"{row['distance']:.4f}",
            row.get('question', 'N/A'),
            row.get('answer', 'N/A')[:100] + "..." if len(row.get('answer', 'N/A')) > 100 else row.get('answer', 'N/A'),
            row.get('category', 'N/A')
        )
    
    console.print(table)


def display_doc_results(results):
    """Display results from document sources in a table."""
    if results.empty:
        console.print("[italic]No results found.[/italic]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Distance")
    table.add_column("Document")
    table.add_column("Type")
    table.add_column("Content Preview")
    
    for _, row in results.iterrows():
        # Try to get content from various possible column names
        content = ''
        for col_name in ['contents', 'content', 'answer']:
            if col_name in row and row[col_name]:
                content = row[col_name]
                break
                
        # Get filename, trying different metadata options
        filename = row.get('filename', 'Unknown')
        if filename == 'Unknown' and 'question' in row:
            filename = f"FAQ: {row['question'][:30]}..."
                
        # Get filetype
        filetype = row.get('filetype', 'Unknown')
        if filetype == 'Unknown' and 'category' in row:
            filetype = f"FAQ ({row['category']})"
            
        table.add_row(
            f"{row['distance']:.4f}",
            filename,
            filetype,
            content[:100] + "..." if len(content) > 100 else content
        )
    
    console.print(table)


def run_faq_examples():
    """Run sample queries against the FAQ dataset."""
    divider("FAQ DATASET EXAMPLES")
    
    run_query("What are your shipping options?", source_type='faq')
    
    console.print("\n[bold cyan]With Category Filter:[/bold cyan]")
    run_query("How long does shipping take?", source_type='faq', 
              metadata_filter={"category": "Shipping"})


def run_pdf_examples():
    """Run sample queries against the PDF documents."""
    divider("PDF DOCUMENT EXAMPLES")
    
    run_query("What is the database architecture?", source_type='pdf')
    run_query("How is security implemented?", source_type='pdf')
    run_query("What is the disaster recovery plan?", source_type='pdf')


def run_doc_examples():
    """Run sample queries against the DOCX documents."""
    divider("DOCX DOCUMENT EXAMPLES")
    
    run_query("What is the return policy for electronics?", source_type='doc')
    run_query("How long do I have to return items?", source_type='doc')
    run_query("What items cannot be returned?", source_type='doc')


def run_cross_source_examples():
    """Run sample queries across all data sources."""
    divider("CROSS-SOURCE EXAMPLES")
    
    run_query("What are your shipping policies?")
    run_query("Tell me about returns and refunds")
    run_query("How do you handle customer data?")


def main():
    parser = argparse.ArgumentParser(description="Test querying from all data sources.")
    parser.add_argument("--faq", action="store_true", help="Run FAQ examples")
    parser.add_argument("--pdf", action="store_true", help="Run PDF examples")
    parser.add_argument("--doc", action="store_true", help="Run DOCX examples")
    parser.add_argument("--all", action="store_true", help="Run cross-source examples")
    parser.add_argument("--full", action="store_true", help="Run all examples")
    
    args = parser.parse_args()
    
    # If no specific flags are provided, show help
    if not (args.faq or args.pdf or args.doc or args.all or args.full):
        parser.print_help()
        return
    
    console.print("[bold]Testing Queries Across All Data Sources[/bold]")
    
    if args.faq or args.full:
        run_faq_examples()
    
    if args.pdf or args.full:
        run_pdf_examples()
    
    if args.doc or args.full:
        run_doc_examples()
    
    if args.all or args.full:
        run_cross_source_examples()


if __name__ == "__main__":
    main()