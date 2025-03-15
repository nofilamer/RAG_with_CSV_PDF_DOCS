from datetime import datetime
import os
from pathlib import Path
import logging
import pandas as pd
from database.vector_store import VectorStore
from timescale_vector.client import uuid_from_time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize VectorStore
vec = VectorStore()

# Get the path to the data directory relative to this script
data_dir = Path(__file__).parent.parent / 'data'
csv_path = data_dir / 'faq_dataset.csv'

# Read the CSV file
df = pd.read_csv(csv_path, sep=";")


# Prepare data for insertion
def prepare_record(row):
    """Prepare a record for insertion into the vector store.

    This function creates a record with a UUID version 1 as the ID, which captures
    the current time or a specified time.

    Note:
        - By default, this function uses the current time for the UUID.
        - To use a specific time:
          1. Import the datetime module.
          2. Create a datetime object for your desired time.
          3. Use uuid_from_time(your_datetime) instead of uuid_from_time(datetime.now()).

        Example:
            from datetime import datetime
            specific_time = datetime(2023, 1, 1, 12, 0, 0)
            id = str(uuid_from_time(specific_time))

        This is useful when your content already has an associated datetime.
    """
    content = f"Question: {row['question']}\nAnswer: {row['answer']}"
    embedding = vec.get_embedding(content)
    return pd.Series(
        {
            "id": str(uuid_from_time(datetime.now())),
            "metadata": {
                "category": row["category"],
                "created_at": datetime.now().isoformat(),
            },
            "contents": content,
            "embedding": embedding,
        }
    )


records_df = df.apply(prepare_record, axis=1)

# Create tables and insert data
try:
    logging.info("Creating tables...")
    vec.create_tables()
    logging.info("Creating index...")
    vec.create_index()  # DiskAnnIndex
    logging.info(f"Inserting {len(records_df)} FAQ records...")
    vec.upsert(records_df)
    logging.info(f"Successfully inserted {len(records_df)} FAQ records.")
except Exception as e:
    logging.error(f"Error during data insertion: {e}")
    # If the error is about tables or indexes already existing, continue
    if "already exists" in str(e):
        logging.info("Tables or indexes already exist. Continuing with insertion...")
        try:
            vec.upsert(records_df)
            logging.info(f"Successfully inserted {len(records_df)} FAQ records.")
        except Exception as e2:
            logging.error(f"Error during fallback insertion: {e2}")
    else:
        raise
