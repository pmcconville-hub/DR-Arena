"""
LLM Agent for crafting search queries and selecting websites
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from anthropic import Anthropic


class LLMAgent:
    """LLM agent for query generation and website selection"""

    def __init__(self, api_key: Optional[str] = None, model: str = ""):
        """
        Initialize the LLM agent.

        Args:
            api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)
            model: Model to use for generation
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def craft_search_query(self, topic: str, subtopic: str) -> str:
        """
        Craft a relevant search query for a given topic and subtopic.

        Args:
            topic: The main topic path (e.g., "Arts & Entertainment > Music & Audio")
            subtopic: The specific subtopic (e.g., "Jazz")

        Returns:
            A search query string optimized for finding informative websites
        """
        prompt = f"""You are a search query expert. Given a topic and subtopic, craft a single, focused search query that will find informative, content-rich websites with good hyperlink structures.

Topic path: {topic}
Subtopic: {subtopic}

The search query should:
1. Be specific enough to find quality information sources
2. Target websites that are likely to have good internal linking structure (like Wikipedia-style sites, educational resources, comprehensive guides)
3. Avoid overly commercial or news sites
4. Be 3-7 words long

Examples:
- For "Coffee > Types": "coffee varieties comprehensive guide"
- For "Programming > Python": "python programming tutorial documentation"
- For "History > Ancient Rome": "ancient rome history encyclopedia"

Return ONLY the search query text, nothing else."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=100,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        query = message.content[0].text.strip().strip('"\'')
        return query

    def select_best_website(self, search_results: List[Dict], topic: str, subtopic: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Select the best website from search results for crawling.

        Args:
            search_results: List of search result dictionaries with 'title', 'link', 'snippet'
            topic: The topic path
            subtopic: The subtopic

        Returns:
            Tuple of (selected_url, reasoning) or (None, reason_for_none)
        """
        if not search_results:
            return None, "No search results provided"

        # Format search results for the LLM
        results_text = ""
        for i, result in enumerate(search_results[:10], 1):  # Only show top 10
            results_text += f"\n{i}. Title: {result.get('title', 'N/A')}\n"
            results_text += f"   URL: {result.get('link', 'N/A')}\n"
            results_text += f"   Snippet: {result.get('snippet', 'N/A')}\n"

        prompt = f"""You are a website quality evaluator. Select the BEST website from these search results for web crawling to build an informative tree structure.

Topic: {topic}
Subtopic: {subtopic}

Search Results:
{results_text}

Criteria for selection:
1. **Content richness**: Sites with comprehensive, educational content (wikis, encyclopedias, educational sites, detailed guides)
2. **Link structure**: Sites likely to have good internal linking with hierarchical structure
3. **Depth**: Sites that likely have multiple levels of content organization
4. **Avoid**: E-commerce sites, social media, news sites, blogs, sites with paywalls
5. **Prefer**: .edu, .org, Wikipedia-style sites, documentation sites, comprehensive guides

Return your response in this EXACT JSON format:
{{
    "selected_index": <number from 1-10, or null if none suitable>,
    "reasoning": "<brief explanation of why this site is best, or why none are suitable>"
}}

Return ONLY the JSON, nothing else."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response
        try:
            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            response = json.loads(response_text)
            selected_index = response.get('selected_index')
            reasoning = response.get('reasoning', 'No reasoning provided')

            if selected_index is None or selected_index < 1 or selected_index > len(search_results):
                return None, reasoning

            selected_result = search_results[selected_index - 1]
            selected_url = selected_result.get('link')

            return selected_url, reasoning

        except json.JSONDecodeError as e:
            return None, f"Failed to parse LLM response: {response_text[:200]}"
        except Exception as e:
            return None, f"Error processing LLM response: {str(e)}"


if __name__ == '__main__':
    # Test the LLM agent
    agent = LLMAgent()

    # Test query crafting
    print("Testing query crafting:")
    query = agent.craft_search_query(
        "Arts & Entertainment > Music & Audio",
        "Jazz"
    )
    print(f"Query: {query}\n")

    # Test website selection
    print("Testing website selection:")
    mock_results = [
        {
            "title": "Jazz - Wikipedia",
            "link": "https://en.wikipedia.org/wiki/Jazz",
            "snippet": "Jazz is a music genre that originated in the African-American communities..."
        },
        {
            "title": "Buy Jazz Albums on Amazon",
            "link": "https://amazon.com/jazz",
            "snippet": "Shop for jazz albums, CDs, and vinyl records..."
        },
        {
            "title": "All About Jazz - Jazz Music Portal",
            "link": "https://allaboutjazz.com",
            "snippet": "Comprehensive jazz music portal with artist profiles, reviews..."
        }
    ]

    url, reasoning = agent.select_best_website(mock_results, "Music", "Jazz")
    print(f"Selected URL: {url}")
    print(f"Reasoning: {reasoning}")
