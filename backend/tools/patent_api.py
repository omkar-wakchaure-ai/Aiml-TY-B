import requests
from crewai.tools import tool

@tool("Patent Search Tool")
def search_patents(keyword: str, max_results: int = 3) -> str:
    """Searches USPTO patent records for patents matching the given keyword."""
    url = f"https://api.patentsview.org/patents/query"
    
    # Query structure for PatentsView API
    query_payload = {
        "q": {"_text_any": {"patent_title": keyword}},
        "f": ["patent_number", "patent_title", "patent_date", "patent_abstract"],
        "o": {"per_page": max_results}
    }
    
    try:
        response = requests.post(url, json=query_payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            patents = data.get("patents", [])
            
            if not patents:
                return f"No patents found for keyword: {keyword}"
            
            output = []
            for p in patents:
                output.append(
                    f"Patent ID: {p.get('patent_number')}\n"
                    f"Title: {p.get('patent_title')}\n"
                    f"Date: {p.get('patent_date')}\n"
                    f"Abstract: {p.get('patent_abstract')[:250]}...\n"
                    "----------------------------------------"
                )
            return "\n\n".join(output)
        else:
            return f"Patent API returned status code {response.status_code}."
    except Exception as e:
        return f"Error performing patent search: {str(e)}"