import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from crewai.tools import tool

@tool("Academic Research Tool")
def search_research_papers(query: str) -> str:
    """
    Use this tool to find recent scientific research papers related to a technology.
    """
    try:
        # Properly encode spaces and special characters for the URL
        encoded_query = urllib.parse.quote(f"all:{query}")
        url = f"http://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results=3"
        
        with urllib.request.urlopen(url) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        papers = []
        # Parse Atom feed entries
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip().replace('\n', ' ')
            summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip().replace('\n', ' ')
            papers.append(f"Title: {title}\nSummary: {summary}\n")
            
        return "\n---\n".join(papers) if papers else "No papers found."
    except Exception as e:
        return f"ArXiv search error: {str(e)}"