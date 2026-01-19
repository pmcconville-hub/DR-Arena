"""
Trends parser for sampling topics and subtopics from trends.json
"""

import json
import random
from typing import Dict, List, Tuple, Optional


class TrendsParser:
    """Parse and sample from Google Trends categories"""

    def __init__(self, trends_json_path: str):
        """
        Initialize the trends parser.

        Args:
            trends_json_path: Path to trends.json file
        """
        self.trends_json_path = trends_json_path
        self.categories = self._load_trends()
        self.flattened_categories = self._flatten_categories()

    def _load_trends(self) -> Dict:
        """Load trends from JSON file"""
        with open(self.trends_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _flatten_categories(self) -> List[Tuple[str, str, int]]:
        """
        Flatten the nested category structure into (topic, subtopic, id) tuples.

        Returns:
            List of (topic_path, subtopic_name, category_id) tuples
        """
        result = []

        def traverse(node, path=""):
            """Recursively traverse the category tree"""
            if 'children' in node and node['children']:
                # This is a parent category
                current_name = node.get('name', 'Root')
                new_path = f"{path} > {current_name}" if path else current_name

                for child in node['children']:
                    traverse(child, new_path)
            else:
                # This is a leaf category (subtopic)
                if 'name' in node and 'id' in node:
                    result.append((path, node['name'], node['id']))

        # Start traversal from root
        if 'children' in self.categories:
            for child in self.categories['children']:
                traverse(child, "")

        return result

    def sample_random_subtopic(self) -> Tuple[str, str, int]:
        """
        Sample a random subtopic from the trends.

        Returns:
            Tuple of (topic_path, subtopic_name, category_id)
        """
        return random.choice(self.flattened_categories)

    def get_subtopic_info(self, category_id: int) -> Optional[Tuple[str, str, int]]:
        """
        Get subtopic information by category ID.

        Args:
            category_id: The category ID to look up

        Returns:
            Tuple of (topic_path, subtopic_name, category_id) or None if not found
        """
        for topic, subtopic, cid in self.flattened_categories:
            if cid == category_id:
                return (topic, subtopic, cid)
        return None

    def get_all_subtopics(self) -> List[Tuple[str, str, int]]:
        """
        Get all subtopics.

        Returns:
            List of (topic_path, subtopic_name, category_id) tuples
        """
        return self.flattened_categories

    def count_subtopics(self) -> int:
        """Count total number of subtopics"""
        return len(self.flattened_categories)


if __name__ == '__main__':
    # Test the parser
    parser = TrendsParser('data/trends.json')
    print(f"Total subtopics: {parser.count_subtopics()}")

    # Sample a few random subtopics
    print("\nSample random subtopics:")
    for _ in range(5):
        topic, subtopic, cid = parser.sample_random_subtopic()
        print(f"  Topic: {topic}")
        print(f"  Subtopic: {subtopic}")
        print(f"  ID: {cid}")
        print()
