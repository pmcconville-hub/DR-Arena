"""
Google Search API integration using SerpAPI
"""

import os
from typing import List, Dict, Optional
from serpapi import GoogleSearch


class SearchAPI:
    """Google search API wrapper using SerpAPI"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the search API.

        Args:
            api_key: SerpAPI key (if None, reads from SERPAPI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('SERPAPI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "SerpAPI key not provided. Set SERPAPI_API_KEY environment variable "
                "or pass api_key parameter."
            )

    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Search Google and return results.

        Args:
            query: The search query string
            num_results: Number of results to return (max 10)

        Returns:
            List of result dictionaries with 'title', 'link', 'snippet'
        """
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": min(num_results, 10),  # SerpAPI typically returns max 10 organic results
                "engine": "google"
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            # Extract organic results
            organic_results = results.get("organic_results", [])

            # Format results
            formatted_results = []
            for result in organic_results[:num_results]:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position", 0)
                })

            return formatted_results

        except Exception as e:
            print(f"Error searching: {e}")
            return []


if __name__ == '__main__':
    # Test the search API
    search = SearchAPI()

    query = "jazz music history comprehensive guide"
    print(f"Searching for: {query}")
    print()

    results = search.search(query)

    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['link']}")
        print(f"   Snippet: {result['snippet'][:100]}...")
