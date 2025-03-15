#!/usr/bin/env python3
"""
Interactive custom prompt application for PGVectorScale.

This script allows users to:
1. Submit custom prompts/questions
2. Configure search settings (source type, results limit, etc.)
3. Configure the LLM response format and behavior
4. Save results to a file

Usage:
    python app/custom_prompt.py [--mode {chat,search}] [--output FILE]
"""

import argparse
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from database.vector_store import VectorStore
from database.document_store import DocumentStore
from services.synthesizer import Synthesizer, SynthesizedResponse
from services.llm_factory import LLMFactory
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
console = Console()

# Initialize vector stores
faq_store = VectorStore()
doc_store = DocumentStore()


class CustomPromptSettings(BaseModel):
    """Settings for custom prompt execution."""
    
    # Search settings
    source_type: Optional[str] = Field(
        None, 
        description="Source type to search ('faq', 'pdf', 'doc', or None for all)"
    )
    limit: int = Field(
        5, 
        description="Maximum number of results to retrieve"
    )
    metadata_filter: Optional[Dict[str, Any]] = Field(
        None, 
        description="Optional metadata filter for search"
    )
    
    # LLM settings
    temperature: float = Field(
        0.0, 
        description="Temperature for LLM generation (0.0-1.0)"
    )
    model: str = Field(
        "gpt-4o", 
        description="LLM model to use (e.g., 'gpt-4o', 'claude-3-opus')"
    )
    provider: str = Field(
        "openai", 
        description="LLM provider to use (e.g., 'openai', 'anthropic')"
    )
    
    # Custom system prompt (optional)
    system_prompt: Optional[str] = Field(
        None, 
        description="Custom system prompt to override default"
    )
    
    # Output settings
    save_results: bool = Field(
        False, 
        description="Whether to save results to a file"
    )
    output_file: Optional[str] = Field(
        None, 
        description="File to save results to (if save_results is True)"
    )


class QuerySession:
    """Session for managing custom prompt queries."""
    
    def __init__(self, settings: Optional[CustomPromptSettings] = None):
        """Initialize a query session with optional settings."""
        self.settings = settings or CustomPromptSettings()
        self.history: List[Dict[str, Any]] = []
        
    def configure_settings(self) -> None:
        """Interactive configuration of settings."""
        console.print(Panel("Configure Search Settings", style="bold cyan"))
        
        # Source type
        source_options = {
            "1": "All Sources",
            "2": "FAQ Dataset Only", 
            "3": "PDF Documents Only", 
            "4": "DOCX Documents Only"
        }
        console.print("Select source type:")
        for key, value in source_options.items():
            console.print(f"  {key}. {value}")
            
        source_choice = Prompt.ask("Choice", choices=["1", "2", "3", "4"], default="1")
        source_mapping = {"1": None, "2": "faq", "3": "pdf", "4": "doc"}
        self.settings.source_type = source_mapping[source_choice]
        
        # Result limit
        self.settings.limit = int(Prompt.ask("Maximum number of results", default=str(self.settings.limit)))
        
        # Metadata filtering
        if Confirm.ask("Add metadata filters?", default=False):
            category = Prompt.ask("Filter by category (e.g. 'Shipping', 'Returns', leave empty to skip)")
            if category:
                self.settings.metadata_filter = {"category": category}
                
        # LLM settings
        console.print(Panel("Configure LLM Settings", style="bold cyan"))
        self.settings.temperature = float(Prompt.ask(
            "Temperature (0.0-1.0, higher = more creative)", 
            default=str(self.settings.temperature)
        ))
        
        provider_options = {
            "1": "OpenAI",
            "2": "Anthropic (requires API key)" 
        }
        console.print("Select LLM provider:")
        for key, value in provider_options.items():
            console.print(f"  {key}. {value}")
            
        provider_choice = Prompt.ask("Choice", choices=["1", "2"], default="1")
        provider_mapping = {"1": "openai", "2": "anthropic"}
        self.settings.provider = provider_mapping[provider_choice]
        
        if self.settings.provider == "openai":
            model_options = {
                "1": "GPT-4o (Recommended)",
                "2": "GPT-4-Turbo", 
            }
            console.print("Select OpenAI model:")
            for key, value in model_options.items():
                console.print(f"  {key}. {value}")
                
            model_choice = Prompt.ask("Choice", choices=["1", "2"], default="1")
            model_mapping = {"1": "gpt-4o", "2": "gpt-4-turbo-2024-04-09"}
            self.settings.model = model_mapping[model_choice]
        elif self.settings.provider == "anthropic":
            model_options = {
                "1": "Claude 3 Opus (Most capable)",
                "2": "Claude 3 Sonnet (Balanced)", 
                "3": "Claude 3 Haiku (Fastest)"
            }
            console.print("Select Anthropic model:")
            for key, value in model_options.items():
                console.print(f"  {key}. {value}")
                
            model_choice = Prompt.ask("Choice", choices=["1", "2", "3"], default="2")
            model_mapping = {
                "1": "claude-3-opus-20240229", 
                "2": "claude-3-sonnet-20240229",
                "3": "claude-3-haiku-20240307"
            }
            self.settings.model = model_mapping[model_choice]
        
        # Custom system prompt
        if Confirm.ask("Use custom system prompt?", default=False):
            console.print("Enter custom system prompt (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if not line and lines and not lines[-1]:
                    break
                lines.append(line)
            self.settings.system_prompt = "\n".join(lines[:-1])
        
        # Save settings to file
        if Confirm.ask("Save current settings as default for future sessions?", default=False):
            self.save_settings()
            
    def save_settings(self, filepath: Optional[str] = None) -> None:
        """Save current settings to a file."""
        if not filepath:
            filepath = str(Path(__file__).parent.parent / "user_settings.json")
            
        # Convert settings to dict, excluding None values and output-related settings
        settings_dict = {k: v for k, v in self.settings.dict().items() 
                         if v is not None and k not in ["save_results", "output_file"]}
        
        with open(filepath, "w") as f:
            json.dump(settings_dict, f, indent=2)
        
        console.print(f"Settings saved to {filepath}", style="green")
        
    def load_settings(self, filepath: Optional[str] = None) -> None:
        """Load settings from a file."""
        if not filepath:
            filepath = str(Path(__file__).parent.parent / "user_settings.json")
            
        try:
            with open(filepath, "r") as f:
                settings_dict = json.load(f)
                
            # Update only existing fields
            for key, value in settings_dict.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
                    
            console.print(f"Settings loaded from {filepath}", style="green")
        except FileNotFoundError:
            console.print(f"No saved settings found at {filepath}", style="yellow")
        except json.JSONDecodeError:
            console.print(f"Error parsing settings file at {filepath}", style="red")
            
    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a query with current settings."""
        result_entry = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "settings": self.settings.dict(),
            "results": None,
            "response": None,
        }
        
        try:
            # Search based on source type
            if self.settings.source_type == 'faq':
                # Search in original FAQ dataset
                results = faq_store.search(
                    query, 
                    limit=self.settings.limit, 
                    metadata_filter=self.settings.metadata_filter
                )
                
            elif self.settings.source_type == 'pdf':
                # Search in PDF documents
                results = doc_store.search_pdfs(
                    query, 
                    limit=self.settings.limit, 
                    metadata_filter=self.settings.metadata_filter
                )
                
            elif self.settings.source_type == 'doc':
                # Search in DOCX documents
                results = doc_store.search_docs(
                    query, 
                    limit=self.settings.limit, 
                    metadata_filter=self.settings.metadata_filter
                )
                
            else:
                # Combined search from all sources
                faq_results = faq_store.search(
                    query, 
                    limit=self.settings.limit, 
                    metadata_filter=self.settings.metadata_filter
                )
                
                pdf_results = doc_store.search_pdfs(
                    query, 
                    limit=self.settings.limit, 
                    metadata_filter=self.settings.metadata_filter
                )
                
                doc_results = doc_store.search_docs(
                    query, 
                    limit=self.settings.limit, 
                    metadata_filter=self.settings.metadata_filter
                )
                
                # For response generation, use the best results
                # (For simplicity, just prioritize based on source type)
                if not pdf_results.empty:
                    results = pdf_results
                elif not doc_results.empty:
                    results = doc_results
                else:
                    results = faq_results
                    
                # Store all results for history
                result_entry["all_results"] = {
                    "faq": faq_results.to_dict() if not faq_results.empty else None,
                    "pdf": pdf_results.to_dict() if not pdf_results.empty else None,
                    "doc": doc_results.to_dict() if not doc_results.empty else None
                }
            
            # Store results for history
            result_entry["results"] = results.to_dict() if not results.empty else None
            
            # Generate response with custom settings
            if not results.empty:
                response = self._generate_response(query, results)
                result_entry["response"] = {
                    "answer": response.answer,
                    "thought_process": response.thought_process,
                    "enough_context": response.enough_context
                }
            else:
                result_entry["response"] = {
                    "answer": "No relevant information found.",
                    "thought_process": ["No matching documents found in the selected sources."],
                    "enough_context": False
                }
                
            # Add to history
            self.history.append(result_entry)
            
            return result_entry
        
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            result_entry["error"] = str(e)
            self.history.append(result_entry)
            return result_entry
    
    def _generate_response(self, question: str, context: pd.DataFrame) -> SynthesizedResponse:
        """Generate a response using the specified LLM settings."""
        # Create a custom synthesizer for this query
        llm = LLMFactory(self.settings.provider)
        
        # Prepare messages
        system_prompt = self.settings.system_prompt or Synthesizer.SYSTEM_PROMPT
        context_str = Synthesizer.dataframe_to_json(
            context, columns_to_keep=["content", "category"]
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"# User question:\n{question}"},
            {
                "role": "assistant",
                "content": f"# Retrieved information:\n{context_str}",
            },
        ]
        
        # Call the LLM with custom settings
        return llm.create_completion(
            response_model=SynthesizedResponse,
            messages=messages,
            temperature=self.settings.temperature,
            model=self.settings.model,
        )
        
    def save_history(self, filepath: Optional[str] = None) -> None:
        """Save query history to a file."""
        if not filepath and self.settings.output_file:
            filepath = self.settings.output_file
        elif not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = str(Path(__file__).parent.parent / f"query_history_{timestamp}.json")
            
        with open(filepath, "w") as f:
            json.dump(self.history, f, indent=2)
            
        console.print(f"Query history saved to {filepath}", style="green")


def display_results(query: str, result: Dict[str, Any]) -> None:
    """Display query results in a formatted way."""
    console.print(f"\n[bold cyan]Query:[/bold cyan] {query}")
    
    source_type = result["settings"]["source_type"] or "All Sources"
    console.print(f"[bold cyan]Source:[/bold cyan] {source_type}")
    
    # Display search results
    if result["results"]:
        # Convert results back to DataFrame for display
        try:
            results_df = pd.DataFrame.from_dict(result["results"])
            
            if "distance" in results_df.columns:
                console.print("\n[bold green]Search Results:[/bold green]")
                
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Distance")
                
                # Determine what columns to display based on data type
                if "question" in results_df.columns:
                    # FAQ results
                    table.add_column("Question")
                    table.add_column("Answer")
                    
                    for _, row in results_df.iterrows():
                        table.add_row(
                            f"{row['distance']:.4f}",
                            str(row.get('question', 'N/A')),
                            str(row.get('answer', 'N/A'))[:100] + "..." 
                            if len(str(row.get('answer', 'N/A'))) > 100 
                            else str(row.get('answer', 'N/A'))
                        )
                else:
                    # Document results
                    table.add_column("Document")
                    table.add_column("Type")
                    table.add_column("Content Preview")
                    
                    for _, row in results_df.iterrows():
                        # Get content from various possible fields
                        content = ""
                        for field in ["contents", "content"]:
                            if field in row and pd.notna(row[field]):
                                content = str(row[field])
                                break
                        
                        table.add_row(
                            f"{row['distance']:.4f}",
                            str(row.get('filename', 'Unknown')),
                            str(row.get('filetype', 'Unknown')),
                            content[:100] + "..." if len(content) > 100 else content
                        )
                
                console.print(table)
        except Exception as e:
            console.print(f"[yellow]Error displaying results table: {e}[/yellow]")
            console.print("[yellow]Results available but not displayed in table format.[/yellow]")
    
    # Display synthesized answer
    if result["response"] and result["response"]["answer"]:
        console.print("\n[bold green]Synthesized Answer:[/bold green]")
        console.print(Panel(Markdown(result["response"]["answer"])))
        
        if result["response"]["thought_process"]:
            console.print("\n[bold green]Thought Process:[/bold green]")
            for thought in result["response"]["thought_process"]:
                console.print(f"- {thought}")
                
        enough_context = result["response"]["enough_context"]
        color = "green" if enough_context else "yellow"
        console.print(f"\n[bold cyan]Enough Context:[/bold {color}] {enough_context}")
    
    # Display error if present
    if "error" in result:
        console.print(f"\n[bold red]Error:[/bold red] {result['error']}")


def chat_mode(session: QuerySession) -> None:
    """Run an interactive chat session."""
    console.print(Panel("Interactive Query Mode", style="bold cyan"))
    console.print("Type your questions below. Enter 'exit', 'quit', or 'q' to end the session.")
    console.print("Type 'settings' to configure search settings.")
    console.print("Type 'save' to save history to a file.")
    
    while True:
        query = Prompt.ask("\n[bold green]Query[/bold green]")
        
        if query.lower() in ["exit", "quit", "q"]:
            break
            
        if query.lower() == "settings":
            session.configure_settings()
            continue
            
        if query.lower() == "save":
            filepath = Prompt.ask("Save history to file", default="query_history.json")
            session.save_history(filepath)
            continue
            
        # Execute query and display results
        result = session.execute_query(query)
        display_results(query, result)


def search_mode(query: str, session: QuerySession) -> None:
    """Run a single search query."""
    result = session.execute_query(query)
    display_results(query, result)
    
    if session.settings.save_results:
        session.save_history()


def main():
    """Parse arguments and run the appropriate mode."""
    parser = argparse.ArgumentParser(description="Custom prompt interface for PGVectorScale")
    parser.add_argument("--mode", choices=["chat", "search"], default="chat",
                        help="Mode to run in (default: chat)")
    parser.add_argument("--query", type=str, help="Query to run in search mode")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--output", type=str, help="Output file for saving results")
    parser.add_argument("--source", choices=["all", "faq", "pdf", "doc"], default="all",
                        help="Source type to search (default: all)")
    parser.add_argument("--limit", type=int, default=5,
                        help="Maximum number of results (default: 5)")
    parser.add_argument("--temperature", type=float, default=0.0,
                        help="Temperature for LLM generation (default: 0.0)")
    
    args = parser.parse_args()
    
    # Initialize session
    session = QuerySession()
    
    # Try to load saved settings
    if args.config:
        session.load_settings(args.config)
    else:
        session.load_settings()  # Try to load default settings
        
    # Override settings with command-line arguments
    if args.source != "all":
        session.settings.source_type = args.source
    if args.limit != 5:
        session.settings.limit = args.limit
    if args.temperature != 0.0:
        session.settings.temperature = args.temperature
    if args.output:
        session.settings.save_results = True
        session.settings.output_file = args.output
    
    if args.mode == "chat":
        chat_mode(session)
    elif args.mode == "search":
        if not args.query:
            console.print("[red]Error: query argument is required in search mode[/red]")
            parser.print_help()
            return
        search_mode(args.query, session)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()