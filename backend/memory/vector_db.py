import os
import chromadb

# Creates a folder named "chroma_storage" to save memory files locally
DB_DIR = os.path.join(os.path.dirname(__file__), "../../chroma_storage")

class VectorDBClient:
    def __init__(self):
        # Open or create the local database
        self.client = chromadb.PersistentClient(path=DB_DIR)
        # Create a table/collection named "competitor_insights"
        self.collection = self.client.get_or_create_collection(name="competitor_insights")

    def add_insight(self, insight_id: str, text: str, metadata: dict):
        """Saves a sentence or summary into memory."""
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[insight_id]
        )

    def query_similar(self, query_text: str, n_results: int = 3):
        """Searches memory for similar topics."""
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

# Create a single database instance to use across the project
vector_db = VectorDBClient()
