#!/usr/bin/env python3
"""
Complete demo script that:
1. Creates sample documents (PDF, DOCX)
2. Processes and embeds the CSV data, PDF, and DOCX files
3. Runs sample queries against all data sources

This is a comprehensive end-to-end demonstration.
"""

import os
import subprocess
import time
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
console = Console()


def run_command(command, description=None, ignore_errors=False):
    """Run a shell command and print its output."""
    if description:
        console.print(Panel(description, style="bold cyan"))
    
    console.print(f"[bold yellow]Running:[/bold yellow] {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    
    if result.stdout:
        console.print(result.stdout)
    
    if result.returncode != 0 and not ignore_errors:
        console.print(f"[bold red]Error:[/bold red] {result.stderr}")
        return False
    
    return True


def display_header(title):
    """Display a header with a title."""
    console.print("\n")
    console.print(Panel(f"[bold magenta]{title}[/bold magenta]", expand=False))
    console.print("\n")


def check_prerequisites():
    """Check if all prerequisites are met."""
    display_header("CHECKING PREREQUISITES")
    
    # Check if Docker is running and TimescaleDB container is up
    if not run_command("docker ps | grep timescaledb", 
                     "Checking if TimescaleDB container is running...",
                     ignore_errors=True):
        console.print("[bold red]TimescaleDB container is not running.[/bold red]")
        console.print("Please start the container with: cd docker && docker-compose up -d")
        return False
    
    # Check if .env file exists
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        console.print("[bold red].env file not found.[/bold red]")
        console.print("Please create a .env file in the project root with your OpenAI API key.")
        console.print("Example content:")
        console.print("OPENAI_API_KEY=your-api-key-here")
        console.print("TIMESCALE_SERVICE_URL=postgres://postgres:password@localhost:5433/postgres")
        return False
    
    with open(env_path, 'r') as f:
        env_content = f.read()
        if 'OPENAI_API_KEY=sk-your-api-key-here' in env_content:
            console.print("[bold red]Please update your OpenAI API key in the .env file.[/bold red]")
            return False
        
        if not 'OPENAI_API_KEY' in env_content:
            console.print("[bold red]OPENAI_API_KEY not found in .env file.[/bold red]")
            return False
    
    console.print("[bold green]All prerequisites met![/bold green]")
    return True


def step1_generate_documents():
    """Generate sample PDF and DOCX documents."""
    display_header("STEP 1: GENERATING SAMPLE DOCUMENTS")
    
    return run_command(
        "python app/generate_sample_documents.py",
        "Generating sample PDF and DOCX files..."
    )


def step2_setup_database():
    """Set up database tables and indexes."""
    display_header("STEP 2: SETTING UP DATABASE TABLES")
    
    # Run the setup command but ignore errors about tables already existing
    result = run_command(
        "python app/insert_document_vectors.py setup",
        "Setting up document database tables and indexes...",
        ignore_errors=True
    )
    
    # Check if the error is just about tables already existing
    if not result:
        console.print("[yellow]Tables may already exist. Continuing anyway...[/yellow]")
    
    return True


def step3_process_csv_data():
    """Process and insert the CSV data."""
    display_header("STEP 3: PROCESSING CSV DATA")
    
    # Run the command but ignore errors
    result = run_command(
        "python app/insert_vectors.py",
        "Processing and inserting FAQ data from CSV...",
        ignore_errors=True
    )
    
    if not result:
        console.print("[yellow]Error processing CSV data. This may be because the data was already inserted.[/yellow]")
        console.print("[yellow]Continuing with the demo...[/yellow]")
    
    return True


def step4_process_pdf_document():
    """Process and embed the PDF document."""
    display_header("STEP 4: PROCESSING PDF DOCUMENT")
    
    pdf_path = Path(__file__).parent.parent / 'data' / 'ecommerce_technical_docs.pdf'
    return run_command(
        f"python app/insert_document_vectors.py pdf {pdf_path}",
        "Processing and embedding PDF document..."
    )


def step5_process_docx_document():
    """Process and embed the DOCX document."""
    display_header("STEP 5: PROCESSING DOCX DOCUMENT")
    
    docx_path = Path(__file__).parent.parent / 'data' / 'ecommerce_returns_policy.docx'
    return run_command(
        f"python app/insert_document_vectors.py docx {docx_path}",
        "Processing and embedding DOCX document..."
    )


def step6_run_sample_queries():
    """Run sample queries against all data sources."""
    display_header("STEP 6: RUNNING SAMPLE QUERIES")
    
    return run_command(
        "python app/test_all_data_sources.py --full",
        "Running sample queries against all data sources..."
    )


def main():
    """Run the complete demo."""
    console.print(Panel("[bold]COMPLETE DEMO: CSV, PDF, and DOC EMBEDDINGS[/bold]", 
                       style="bold green", expand=False))
    
    if not check_prerequisites():
        return
    
    steps = [
        step1_generate_documents,
        step2_setup_database,
        step3_process_csv_data,
        step4_process_pdf_document,
        step5_process_docx_document,
        step6_run_sample_queries
    ]
    
    for step_func in steps:
        if not step_func():
            console.print(f"[bold red]Failed at step: {step_func.__name__}[/bold red]")
            console.print("Please check the error message above and try again.")
            return
    
    display_header("DEMO COMPLETED SUCCESSFULLY")
    console.print("""
    You have successfully:
    
    1. Generated sample PDF and DOCX documents
    2. Set up database tables and indexes
    3. Processed and embedded CSV data
    4. Processed and embedded PDF document
    5. Processed and embedded DOCX document
    6. Run sample queries against all data sources
    
    You can now:
    - Modify the sample documents or add new ones
    - Run specific queries with: python app/document_search.py search "your query"
    - Run interactive search with: python app/document_search.py interactive
    - Explore different data sources with: python app/test_all_data_sources.py --help
    
    Thank you for trying out this demo!
    """)


if __name__ == "__main__":
    main()