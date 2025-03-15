import logging
import os
import time
import tempfile
import uuid
from typing import Dict, List, Optional, Union
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd
from config.settings import get_settings
from openai import OpenAI
from timescale_vector import client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io


class DocumentStore:
    """A class for handling document processing and vector storage for PDFs and Google Docs."""

    def __init__(self):
        """Initialize the DocumentStore with settings, OpenAI client, and Timescale Vector client."""
        self.settings = get_settings()
        self.openai_client = OpenAI(api_key=self.settings.openai.api_key)
        self.embedding_model = self.settings.openai.embedding_model
        
        # PDF client setup
        self.pdf_client = client.Sync(
            self.settings.database.service_url,
            "pdf_embeddings",
            self.settings.vector_store.embedding_dimensions,
            time_partition_interval=self.settings.vector_store.time_partition_interval,
        )
        
        # Doc client setup
        self.doc_client = client.Sync(
            self.settings.database.service_url,
            "doc_embeddings",
            self.settings.vector_store.embedding_dimensions,
            time_partition_interval=self.settings.vector_store.time_partition_interval,
        )

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for the given text.

        Args:
            text: The input text to generate an embedding for.

        Returns:
            A list of floats representing the embedding.
        """
        text = text.replace("\n", " ")
        start_time = time.time()
        embedding = (
            self.openai_client.embeddings.create(
                input=[text],
                model=self.embedding_model,
            )
            .data[0]
            .embedding
        )
        elapsed_time = time.time() - start_time
        logging.info(f"Embedding generated in {elapsed_time:.3f} seconds")
        return embedding

    def create_tables(self) -> None:
        """Create the necessary tables in the database"""
        self.pdf_client.create_tables()
        self.doc_client.create_tables()
        logging.info("Created PDF and DOC embedding tables")

    def create_indexes(self) -> None:
        """Create the StreamingDiskANN indexes to speed up similarity search"""
        self.pdf_client.create_embedding_index(client.DiskAnnIndex())
        self.doc_client.create_embedding_index(client.DiskAnnIndex())
        logging.info("Created PDF and DOC embedding indexes")

    def process_pdf(self, pdf_path: Union[str, Path], chunk_size: int = 1000) -> pd.DataFrame:
        """
        Process a PDF file and extract text in chunks.
        
        Args:
            pdf_path: Path to the PDF file
            chunk_size: Number of characters per chunk
            
        Returns:
            DataFrame with extracted text chunks and metadata
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        # Extract text from PDF
        doc = fitz.open(pdf_path)
        text = ""
        
        # Extract metadata
        metadata = {
            "filename": pdf_path.name,
            "filesize": pdf_path.stat().st_size,
            "pages": len(doc),
            "filetype": "pdf",
            "last_modified": os.path.getmtime(pdf_path)
        }
        
        # Extract text page by page
        for page_num, page in enumerate(doc):
            text += page.get_text() + "\n\n"

        # Chunk the text
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk_text = text[i:i+chunk_size]
            if chunk_text.strip():  # Skip empty chunks
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_id"] = i // chunk_size
                chunk_metadata["char_start"] = i
                chunk_metadata["char_end"] = min(i + chunk_size, len(text))
                
                # Get embedding for this chunk
                embedding = self.get_embedding(chunk_text)
                
                # Use UUID version 1 (time-based) for TimescaleDB compatibility
                chunks.append({
                    "id": str(uuid.uuid1()),
                    "metadata": chunk_metadata,
                    "content": chunk_text,
                    "embedding": embedding
                })
        
        return pd.DataFrame(chunks)

    def process_gdoc(self, doc_id: str, chunk_size: int = 1000) -> pd.DataFrame:
        """
        Process a Google Doc and extract text in chunks.
        
        Args:
            doc_id: Google Doc ID
            chunk_size: Number of characters per chunk
            
        Returns:
            DataFrame with extracted text chunks and metadata
        """
        try:
            # Setup Google Docs API client
            creds = self._get_google_credentials()
            docs_service = build('docs', 'v1', credentials=creds)
            drive_service = build('drive', 'v3', credentials=creds)
            
            # Get document content
            document = docs_service.documents().get(documentId=doc_id).execute()
            
            # Get file metadata from Drive API
            file_metadata = drive_service.files().get(fileId=doc_id, fields="name,size,modifiedTime").execute()
            
            # Extract text from the document content
            text = ""
            for content in document.get('body').get('content'):
                if 'paragraph' in content:
                    for element in content.get('paragraph').get('elements'):
                        if 'textRun' in element:
                            text += element.get('textRun').get('content', '')
            
            # Create metadata
            metadata = {
                "filename": file_metadata.get('name', f"gdoc_{doc_id}"),
                "filesize": file_metadata.get('size', 0),
                "filetype": "gdoc",
                "doc_id": doc_id,
                "last_modified": file_metadata.get('modifiedTime')
            }
            
            # Chunk the text
            chunks = []
            for i in range(0, len(text), chunk_size):
                chunk_text = text[i:i+chunk_size]
                if chunk_text.strip():  # Skip empty chunks
                    chunk_metadata = metadata.copy()
                    chunk_metadata["chunk_id"] = i // chunk_size
                    chunk_metadata["char_start"] = i
                    chunk_metadata["char_end"] = min(i + chunk_size, len(text))
                    
                    # Get embedding for this chunk
                    embedding = self.get_embedding(chunk_text)
                    
                    # Use UUID version 1 (time-based) for TimescaleDB compatibility
                    chunks.append({
                        "id": str(uuid.uuid1()),
                        "metadata": chunk_metadata,
                        "content": chunk_text,
                        "embedding": embedding
                    })
            
            return pd.DataFrame(chunks)
        except Exception as e:
            logging.error(f"Error processing Google Doc {doc_id}: {e}")
            raise

    def _get_google_credentials(self) -> Credentials:
        """
        Get Google API credentials from environment.
        In a production environment, this would use a more secure method.
        """
        # This is a placeholder for credential handling
        # In production, you should implement proper OAuth flow or service account auth
        raise NotImplementedError(
            "Google Docs API credentials need to be implemented. "
            "Please set up OAuth credentials or implement service account auth."
        )

    def store_pdf_embeddings(self, df: pd.DataFrame) -> None:
        """
        Store PDF embeddings in the database.
        
        Args:
            df: DataFrame with PDF chunks and embeddings
        """
        # Rename content to contents to match TimescaleDB client expectations
        if 'content' in df.columns and 'contents' not in df.columns:
            df = df.rename(columns={'content': 'contents'})
            
        records = df.to_records(index=False)
        self.pdf_client.upsert(list(records))
        logging.info(f"Inserted {len(df)} PDF chunk embeddings")

    def store_doc_embeddings(self, df: pd.DataFrame) -> None:
        """
        Store Google Doc embeddings in the database.
        
        Args:
            df: DataFrame with Doc chunks and embeddings
        """
        # Rename content to contents to match TimescaleDB client expectations
        if 'content' in df.columns and 'contents' not in df.columns:
            df = df.rename(columns={'content': 'contents'})
            
        records = df.to_records(index=False)
        self.doc_client.upsert(list(records))
        logging.info(f"Inserted {len(df)} Google Doc chunk embeddings")

    def search_pdfs(
        self,
        query_text: str,
        limit: int = 5,
        metadata_filter: Optional[Dict] = None,
        return_dataframe: bool = True,
    ):
        """
        Search PDF embeddings for the query text.
        
        Args:
            query_text: The query text
            limit: Maximum number of results
            metadata_filter: Optional filters for metadata
            return_dataframe: Whether to return results as DataFrame
            
        Returns:
            Search results
        """
        query_embedding = self.get_embedding(query_text)
        
        search_args = {
            "limit": limit,
        }
        
        if metadata_filter:
            search_args["filter"] = metadata_filter
            
        results = self.pdf_client.search(query_embedding, **search_args)
        
        if return_dataframe:
            return self._create_dataframe_from_results(results)
        else:
            return results

    def search_docs(
        self,
        query_text: str,
        limit: int = 5,
        metadata_filter: Optional[Dict] = None,
        return_dataframe: bool = True,
    ):
        """
        Search Google Doc embeddings for the query text.
        
        Args:
            query_text: The query text
            limit: Maximum number of results
            metadata_filter: Optional filters for metadata
            return_dataframe: Whether to return results as DataFrame
            
        Returns:
            Search results
        """
        query_embedding = self.get_embedding(query_text)
        
        search_args = {
            "limit": limit,
        }
        
        if metadata_filter:
            search_args["filter"] = metadata_filter
            
        results = self.doc_client.search(query_embedding, **search_args)
        
        if return_dataframe:
            return self._create_dataframe_from_results(results)
        else:
            return results

    def search_all_documents(
        self,
        query_text: str,
        limit: int = 5,
        metadata_filter: Optional[Dict] = None,
        return_dataframe: bool = True,
    ):
        """
        Search both PDF and Google Doc embeddings for the query text.
        
        Args:
            query_text: The query text
            limit: Maximum number of results
            metadata_filter: Optional filters for metadata
            return_dataframe: Whether to return results as DataFrame
            
        Returns:
            Combined search results
        """
        pdf_results = self.search_pdfs(
            query_text, 
            limit=limit, 
            metadata_filter=metadata_filter, 
            return_dataframe=return_dataframe
        )
        
        doc_results = self.search_docs(
            query_text, 
            limit=limit, 
            metadata_filter=metadata_filter, 
            return_dataframe=return_dataframe
        )
        
        if return_dataframe:
            # Combine the two dataframes
            combined_df = pd.concat([pdf_results, doc_results], ignore_index=True)
            # Sort by distance
            combined_df = combined_df.sort_values('distance').head(limit)
            return combined_df
        else:
            # Combine and sort the results
            combined_results = pdf_results + doc_results
            combined_results.sort(key=lambda x: x[4])  # Sort by distance (5th element)
            return combined_results[:limit]

    def _create_dataframe_from_results(self, results: List) -> pd.DataFrame:
        """
        Create a DataFrame from search results.
        
        Args:
            results: Search results from TimescaleVector
            
        Returns:
            DataFrame with formatted results
        """
        # Convert results to DataFrame
        df = pd.DataFrame(
            results, columns=["id", "metadata", "content", "embedding", "distance"]
        )
        
        # Expand metadata column if there are results
        if not df.empty:
            df = pd.concat(
                [df.drop(["metadata"], axis=1), df["metadata"].apply(pd.Series)], axis=1
            )
            
            # Convert id to string for better readability
            df["id"] = df["id"].astype(str)
            
        return df