"""Improved web search tool for Seeker agent using DuckDuckGo."""
from typing import List, Dict

# BaseTool import adjusted for direct execution
try:
    from .base import BaseTool
except ImportError:
    # For direct execution/testing
    class BaseTool:
        pass

class WebSearchImprovedTool(BaseTool):
    """Improved tool for web searching using DuckDuckGo."""
    
    name = "web_search_improved"
    description = "Perform a web search using DuckDuckGo and return results"
    parameters = {
        "query": {
            "type": "string",
            "description": "Search query"
        },
        "max_results": {
            "type": "integer",
            "description": "Maximum number of results to return (default: 5)"
        }
    }
    
    def execute(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Perform web search using DuckDuckGo.
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # Using DuckDuckGo's HTML search interface
            search_url = "https://html.duckduckgo.com/html/"
            params = {
                "q": query,
                "kl": "us-en"  # Set region to US English
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.post(search_url, data=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Parse search results
            for result in soup.find_all('div', class_='result')[:max_results]:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem and snippet_elem:
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get('href')
                    snippet = snippet_elem.get_text(strip=True)
                    
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
            
            if not results:
                return [{"error": "No search results found"}]
                
            return results
            
        except ImportError as e:
            return [{"error": f"Missing required library: {str(e)}. Please install with: pip install requests beautifulsoup4"}]
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]