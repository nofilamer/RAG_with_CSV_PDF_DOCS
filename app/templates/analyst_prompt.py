#!/usr/bin/env python3
"""
Example of a custom prompt template for financial analysis.

This script demonstrates how to create a specialized custom prompt
using the PGVectorScale framework for a specific use case.
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

# Custom financial analyst system prompt
FINANCIAL_ANALYST_PROMPT = """
# Role and Purpose
You are an AI financial analyst assistant for an e-commerce platform. Your role is to analyze financial information and provide valuable business insights based on the provided context.

# Guidelines
1. Provide clear, concise financial analysis based on the retrieved context.
2. Include relevant financial metrics and KPIs when available.
3. Format numbers appropriately ($X,XXX.XX for USD, X% for percentages).
4. Be transparent about limitations in the available data.
5. Highlight potential business implications of your analysis.
6. Suggest relevant next steps or areas for further investigation.
7. When appropriate, present information in table format for clarity.
8. Maintain a professional, analytical tone throughout your response.

Now analyze the following question using the retrieved context:
"""


def run_financial_analysis(query, output_file=None):
    """Run a financial analysis query with the custom prompt template."""
    console.print(Panel(f"[bold]Financial Analysis Prompt:[/bold] {query}", style="cyan"))
    
    # Initialize session with financial analysis settings
    session = QuerySession()
    
    # Configure settings for financial analysis
    session.settings.system_prompt = FINANCIAL_ANALYST_PROMPT
    session.settings.temperature = 0.2  # Lower temperature for more factual responses
    
    # Default to all sources, but prioritize structured data
    session.settings.source_type = None  
    session.settings.limit = 7  # Retrieve more context for analysis
    
    # Execute query with financial analysis prompt
    result = session.execute_query(query)
    
    # Display results
    display_results(query, result)
    
    # Save results if requested
    if output_file:
        session.settings.output_file = output_file
        session.save_history()
        console.print(f"Analysis saved to {output_file}", style="green")


def main():
    parser = argparse.ArgumentParser(description="Financial Analysis Custom Prompt Template")
    parser.add_argument("query", help="Financial analysis query")
    parser.add_argument("--output", "-o", help="Output file for saving results")
    
    args = parser.parse_args()
    
    console.print(Panel("Financial Analyst Custom Prompt Template", style="bold green"))
    console.print("This template uses a specialized system prompt for financial analysis.\n")
    
    run_financial_analysis(args.query, args.output)


if __name__ == "__main__":
    main()