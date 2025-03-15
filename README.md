# PGVectorScale: Multi-Source RAG with TimescaleDB, pgvector, and LLMs

PGVectorScale is a comprehensive Retrieval-Augmented Generation (RAG) solution that leverages PostgreSQL with TimescaleDB and pgvector for efficient vector search, combined with flexible LLM integration for document processing and question answering.

![PGVectorScale Architecture](https://www.timescale.com/blog/content/images/2023/08/timescale-vector-1.webp)

## ✨ Features

### Multi-Source Document Processing
- **CSV Data Integration**: Process structured FAQ data with categories and metadata
- **PDF Document Extraction**: Extract and chunk text from PDF files
- **DOCX Processing**: Handle Microsoft Word documents with formatting
- **Google Docs Integration**: Connect to Google Drive (requires API setup)

### Advanced Vector Search
- **PostgreSQL-Based Vector Store**: TimescaleDB with pgvector for efficient similarity search
- **ANN (Approximate Nearest Neighbor)**: Fast DiskANN-inspired indexing for large vector collections
- **Metadata Filtering**: Filter search results by custom metadata and categories
- **Cross-Source Search**: Query across multiple document types simultaneously
- **Time-Based Partitioning**: Efficiently manage and query time-series vector data

### LLM Integration & Answer Synthesis
- **Multi-Provider Support**: Integration with OpenAI, Anthropic, and extendable to others
- **Provider Abstraction**: Factory pattern for easy provider switching
- **Interactive Prompts**: Rich interface for submitting custom prompts
- **Prompt Templates**: Domain-specific templates for specialized workflows
- **Answer Synthesis**: Generate coherent answers from retrieved vector matches

### User Experience
- **Interactive CLI**: Rich text formatting with tables and markdown
- **Configuration Persistence**: Save and reload user preferences
- **History Tracking**: Save query history and results
- **Comprehensive Documentation**: Detailed examples and usage instructions

## 🚀 Getting Started

### Prerequisites

- Docker
- Python 3.7+
- OpenAI API key
- PostgreSQL client (optional, for direct database access)

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/pgvectorscale.git
cd pgvectorscale

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file with your API keys
cp .env.example .env
# Edit .env with your OpenAI API key
```

### 2. Start the Database

```bash
# Start the TimescaleDB container
cd docker
docker-compose up -d
cd ..
```

### 3. Run the Complete Demo

```bash
# Run the demo script to process and query all document types
python app/run_complete_demo.py
```

This will:
1. Generate sample PDF and DOCX documents
2. Set up database tables and indexes
3. Process and embed CSV data, PDF files, and DOCX files
4. Run sample queries across all data sources

## 📚 Document Processing

### Process CSV Data

The system can handle structured CSV data:

```bash
# Process CSV data into vector embeddings
python app/insert_vectors.py
```

### Process PDF Documents

```bash
# Process a single PDF file
python app/insert_document_vectors.py pdf path/to/your/document.pdf

# Process all PDFs in a directory
python app/insert_document_vectors.py pdf-dir path/to/pdf/directory
```

### Process DOCX Documents

```bash
# Process a Microsoft Word document
python app/insert_document_vectors.py docx path/to/your/document.docx
```

### Process Google Docs

```bash
# Process a Google Doc by ID (requires API setup)
python app/insert_document_vectors.py gdoc your-google-doc-id
```

## 🔍 Search & Querying

### Basic Search

```bash
# Interactive search
python app/document_search.py interactive

# Direct query with source type filter
python app/document_search.py search "What is the database architecture?" --type pdf
```

### Custom Prompts

The system provides a rich interactive interface for submitting custom prompts with configurable settings:

```bash
# Interactive chat mode
python app/custom_prompt.py

# Single query mode
python app/custom_prompt.py --mode search --query "What is the return policy for electronics?"

# Configure search source and LLM parameters
python app/custom_prompt.py --source pdf --limit 10 --temperature 0.7

# Save results to file
python app/custom_prompt.py --output results.json
```

The custom prompt interface allows you to:
- Choose which data sources to search (CSV, PDF, DOCX, or all)
- Configure LLM parameters (temperature, model, provider)
- Use custom system prompts to guide the AI's response
- Save query history and settings for future sessions

### Specialized Templates

You can use or create specialized prompt templates for specific domains and use cases:

```bash
# Financial analyst template
python app/templates/analyst_prompt.py "What are our shipping costs and margins?"

# Technical documentation template
python app/templates/technical_prompt.py "How is the database architecture structured?"
```

The template system allows you to build domain-specific interfaces with:
- Custom system prompts tailored to specific roles
- Specialized parameter settings
- Targeted metadata filtering
- Domain-appropriate output formatting

### Testing & Evaluation

Test search functionality across all data sources:

```bash
# Test FAQ dataset
python app/test_all_data_sources.py --faq

# Test PDF documents
python app/test_all_data_sources.py --pdf

# Test DOCX documents
python app/test_all_data_sources.py --doc

# Test all sources together
python app/test_all_data_sources.py --all
```

## 🏗️ Architecture

### Core Components

1. **VectorStore**: Handles embedding generation and database operations for FAQ data
2. **DocumentStore**: Processes and embeds PDF and DOCX files
3. **Synthesizer**: Processes retrieved vector matches to generate coherent responses
4. **LLMFactory**: Abstracts LLM provider details with a factory pattern

### Database Structure

- **embeddings**: Main table for FAQ vector data
- **pdf_embeddings**: Table for PDF document vector data 
- **doc_embeddings**: Table for DOCX document vector data

Each table uses TimescaleDB's hypertable architecture with DiskANN-inspired indexes for fast similarity search.

### LLM Integration

The system supports multiple LLM providers through a factory pattern:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Extensible to other providers

## 💡 Example Use Cases

- **Customer Support**: Retrieve accurate answers from product documentation and FAQs
- **Technical Documentation**: Search through complex system architecture and API docs
- **Policy Navigation**: Find specific clauses and sections in policy documents
- **Knowledge Management**: Build a centralized knowledge base across document formats
- **Data Analysis**: Extract insights from structured and unstructured data sources

## 🔧 Customization

### Adding New Document Types

To add support for a new document type:
1. Create a processor in `app/database/document_store.py`
2. Add a storage method for the new type
3. Update the search functionality to include the new source

### Creating Custom Templates

To create a new domain-specific template:
1. Copy an existing template from `app/templates/`
2. Customize the system prompt for your domain
3. Adjust search parameters and output formatting

## 📊 Performance Considerations

- For large document collections (>10K), ensure indexes are created
- Use metadata filtering to narrow search scope when possible
- Adjust chunk size based on document complexity and length
- Configure embedding dimensions based on required precision vs. performance

## 🔗 Resources

- [Pgvector Documentation](https://github.com/pgvector/pgvector)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [Timescale Vector Python Client](https://github.com/timescale/timescale-vector)
- [Blog: PostgreSQL and Pgvector - Faster Than Pinecone](https://www.timescale.com/blog/pgvector-is-now-as-fast-as-pinecone-at-75-less-cost/)
- [YouTube Tutorial](https://youtu.be/hAdEuDBN57g)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- The TimescaleDB and Pgvector teams for their excellent vector search capabilities
- The OpenAI and Anthropic teams for their powerful embedding and completion APIs