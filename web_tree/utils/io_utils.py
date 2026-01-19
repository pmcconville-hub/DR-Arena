"""
Input/Output utilities for website tree data.
"""

import json
from typing import Union
from pathlib import Path

from models.tree_models import WebsiteNode


def save_tree_to_json(node: WebsiteNode, file_path: Union[str, Path]) -> None:
    """
    Save website tree to JSON file.

    Args:
        node: Root node of the tree
        file_path: Path to save the JSON file
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(node.to_dict(), f, indent=2, ensure_ascii=False)


def load_tree_from_json(file_path: Union[str, Path]) -> WebsiteNode:
    """
    Load website tree from JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Root node of the loaded tree
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return WebsiteNode.from_dict(data)
