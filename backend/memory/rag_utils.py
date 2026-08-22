import uuid
from .vector_db import vector_db

def is_duplicate_insight(new_summary: str, threshold_distance: float = 0.3) -> bool:
    """Checks if we already reported this news before."""
    results = vector_db.query_similar(query_text=new_summary, n_results=1)
    
    if results and results.get("distances") and len(results["distances"][0]) > 0:
        top_distance = results["distances"][0][0]
        if top_distance < threshold_distance:
            return True  # Yes, it's a duplicate!
    return False  # No, it's new!

def store_new_insight(summary: str, source: str, category: str, impact_score: int):
    """Saves new news into memory."""
    insight_id = str(uuid.uuid4())
    metadata = {
        "source": source,
        "category": category,
        "impact_score": impact_score
    }
    vector_db.add_insight(insight_id=insight_id, text=summary, metadata=metadata)
    return insight_id

def get_historical_context(query: str) -> str:
    """Fetches past context about a topic."""
    results = vector_db.query_similar(query_text=query, n_results=3)
    documents = results.get("documents", [[]])[0]
    
    if not documents:
        return "No past historical data found on this topic."
    
    return "\n---\n".join(documents)
