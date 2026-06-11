import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time

class WebSearchManager:
    def search(self, query: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """Search DuckDuckGo via the HTML interface."""
        try:
            url = f"https://html.duckduckgo.com/html/?q={query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # DuckDuckGo HTML results are in 'result__a' class
            for a in soup.find_all('a', class_='result__a', limit=num_results):
                href = a.get('href')
                # DDG links sometimes are redirected /l/?kh=-1&uddg=URL
                if href and 'uddg=' in href:
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                    href = parsed.get('uddg', [href])[0]
                
                results.append({
                    "href": href,
                    "title": a.get_text().strip()
                })
            
            return results
        except Exception as e:
            print(f"Search failed: {e}")
            return []

    def extract_content(self, url: str) -> Dict[str, str]:
        """Extract title and text content from a URL with robust headers."""
        if not url or not url.startswith("http"):
            return {"title": "Invalid URL", "text": ""}
            
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.google.com/",
                "DNT": "1"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else url
            
            # Remove high-noise areas
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
                element.decompose()
            
            # Focus on main content if possible
            main_content = soup.find('main') or soup.find('article') or soup.body
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
                
            # Limit to first 5000 chars to save on embedding tokens and rate limits
            return {
                "title": title.strip() if title else url,
                "text": text[:5000] 
            }
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return {"title": url, "text": ""}

    def search_and_process(self, query: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """Search and extract content from top results."""
        search_results = self.search(query, num_results)
        processed_docs = []
        for res in search_results:
            url = res.get('href')
            if url:
                data = self.extract_content(url)
                if data["text"]:
                    processed_docs.append({
                        "text": f"Title: {data['title']}\nURL: {url}\nContent: {data['text']}",
                        "metadata": {
                            "source": url,
                            "title": data["title"],
                            "type": "web_search"
                        }
                    })
                time.sleep(1) # Avoid slamming sites
        return processed_docs
