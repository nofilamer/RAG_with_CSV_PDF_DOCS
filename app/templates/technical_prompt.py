#!/usr/bin/env python3
"""
Example of a custom prompt template for technical documentation analysis.

This script demonstrates how to create a specialized custom prompt
using the PGVectorScale framework for technical documentation queries.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.custom_prompt import QuerySession, display_results
from rich.console import Console
from rich.panel import Panel

console = Console()

# Custom technical documentation system prompt
TECHNICAL_PROMPT = """
# Role and Purpose
You are an AI technical documentation assistant. Your role is to provide accurate and concise information about system architecture, APIs, configuration, and technical procedures based on the available documentation.

# Guidelines
1. Provide clear, technically precise answers based strictly on the retrieved documentation.
2. Use proper formatting for code blocks, command-line examples, and technical terminology.
3. Include relevant API signatures, parameters, return types, and examples when appropriate.
4. Maintain a clear structure with sections and subsections for complex technical explanations.
5. If technical information is incomplete, clearly state what is missing and avoid speculation.
6. Provide step-by-step instructions for procedural information.
7. When relevant, include information about error handling, edge cases, and performance considerations.
8. Adjust the level of technical detail based on the specificity of the query.

Now address the following technical question using the retrieved documentation:
"""


def run_technical_query(query, output_file=None):
    """Run a technical documentation query with the custom prompt template."""
    console.print(Panel(f"[bold]Technical Query:[/bold] {query}", style="cyan"))
    
    # Initialize session with technical documentation settings
    session = QuerySession()
    
    # Configure settings for technical documentation queries
    session.settings.system_prompt = TECHNICAL_PROMPT
    session.settings.temperature = 0.0  # Zero temperature for most deterministic responses
    
    # Default to PDF documentation (typically contains technical docs)
    session.settings.source_type = "pdf"  
    session.settings.limit = 5  
    
    # Execute query with technical documentation prompt
    result = session.execute_query(query)
    
    # Display results
    display_results(query, result)
    
    # Save results if requested
    if output_file:
        session.settings.output_file = output_file
        session.save_history()
        console.print(f"Technical documentation saved to {output_file}", style="green")


def main():
    parser = argparse.ArgumentParser(description="Technical Documentation Custom Prompt Template")
    parser.add_argument("query", help="Technical documentation query")
    parser.add_argument("--output", "-o", help="Output file for saving results")
    parser.add_argument("--all-sources", "-a", action="store_true", 
                      help="Search all sources (not just PDF documentation)")
    
    args = parser.parse_args()
    
    console.print(Panel("Technical Documentation Custom Prompt Template", style="bold green"))
    console.print("This template uses a specialized system prompt for technical documentation queries.\n")
    
    # Initialize session and set up the query
    session = QuerySession()
    session.settings.system_prompt = TECHNICAL_PROMPT
    session.settings.temperature = 0.0
    
    # Use all sources if specified, otherwise default to PDF
    if args.all_sources:
        session.settings.source_type = None
    else:
        session.settings.source_type = "pdf"
    
    # Execute and display
    result = session.execute_query(args.query)
    display_results(args.query, result)
    
    # Save if requested
    if args.output:
        session.settings.output_file = args.output
        session.save_history()
        console.print(f"Technical documentation saved to {args.output}", style="green")


if __name__ == "__main__":
    main()