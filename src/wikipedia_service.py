import wikipedia
from typing import Optional, Dict

class WikipediaManager:
    def __init__(self, language: str = "en"):
        wikipedia.set_lang(language)

    def get_summary(self, query: str, sentences: int = 3) -> Optional[Dict[str, str]]:
        """Fetch a summary from Wikipedia for the given query."""
        try:
            # Search for the most relevant page first
            search_results = wikipedia.search(query)
            if not search_results:
                return None
            
            page_title = search_results[0]
            
            # Use auto_suggest=False to get the exact match if possible
            summary = wikipedia.summary(page_title, sentences=sentences, auto_suggest=False)
            page = wikipedia.page(page_title, auto_suggest=False)
            
            return {
                "title": page.title,
                "summary": summary,
                "url": page.url
            }
        except wikipedia.exceptions.DisambiguationError as e:
            # If multiple pages match, try the first option
            try:
                first_option = e.options[0]
                summary = wikipedia.summary(first_option, sentences=sentences, auto_suggest=False)
                page = wikipedia.page(first_option, auto_suggest=False)
                return {
                    "title": page.title,
                    "summary": summary,
                    "url": page.url
                }
            except Exception:
                return None
        except wikipedia.exceptions.PageError:
            return None
        except Exception as e:
            print(f"Wikipedia search failed for {query}: {e}")
            return None
