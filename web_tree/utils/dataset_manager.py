"""
Dataset manager for organizing and tracking crawled trees
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

from models.tree_models import WebsiteNode
from utils.io_utils import save_tree_to_json


class DatasetManager:
    """Manage a dataset of crawled website trees"""

    def __init__(self, dataset_dir: str = "data/dataset"):
        """
        Initialize the dataset manager.

        Args:
            dataset_dir: Directory to store the dataset
        """
        self.dataset_dir = Path(dataset_dir)
        self.dataset_dir.mkdir(parents=True, exist_ok=True)

        self.trees_dir = self.dataset_dir / "trees"
        self.trees_dir.mkdir(exist_ok=True)

        self.metadata_file = self.dataset_dir / "metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load metadata about the dataset"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "total_trees": 0,
                "trees": []
            }

    def _save_metadata(self):
        """Save metadata to file"""
        self.metadata["updated_at"] = datetime.now().isoformat()
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, indent=2, fp=f)

    def add_tree(self, tree: WebsiteNode, metadata: Dict, auto_save: bool = True) -> str:
        """
        Add a tree to the dataset.

        Args:
            tree: The WebsiteNode tree to add
            metadata: Additional metadata (topic, subtopic, search_query, etc.)
            auto_save: Whether to automatically save metadata after adding (default: True)

        Returns:
            The tree ID (filename without extension)
        """
        # Generate tree ID
        tree_id = f"tree_{self.metadata['total_trees'] + 1:04d}"
        tree_file = self.trees_dir / f"{tree_id}.json"

        # Save tree to file
        save_tree_to_json(tree, str(tree_file))

        # Add to metadata
        tree_metadata = {
            "tree_id": tree_id,
            "filename": f"{tree_id}.json",
            "root_url": tree.url,
            "domain": tree.domain,
            "crawled_at": datetime.now().isoformat(),
            **metadata
        }

        self.metadata["trees"].append(tree_metadata)
        self.metadata["total_trees"] += 1

        # Save metadata if auto_save is enabled
        if auto_save:
            self._save_metadata()

        return tree_id

    def save(self):
        """Manually save metadata to file"""
        self._save_metadata()

    def get_tree_count(self) -> int:
        """Get the total number of trees in the dataset"""
        return self.metadata["total_trees"]

    def get_tree_metadata(self, tree_id: str) -> Optional[Dict]:
        """Get metadata for a specific tree"""
        for tree_meta in self.metadata["trees"]:
            if tree_meta["tree_id"] == tree_id:
                return tree_meta
        return None

    def get_all_metadata(self) -> List[Dict]:
        """Get metadata for all trees"""
        return self.metadata["trees"]

    def export_summary(self, output_file: Optional[str] = None) -> Dict:
        """
        Export a summary of the dataset.

        Args:
            output_file: Optional path to save summary JSON

        Returns:
            Summary dictionary
        """
        summary = {
            "dataset_info": {
                "created_at": self.metadata["created_at"],
                "updated_at": self.metadata["updated_at"],
                "total_trees": self.metadata["total_trees"],
                "dataset_dir": str(self.dataset_dir)
            },
            "trees_by_topic": {},
            "trees_by_domain": {},
            "trees": []
        }

        # Analyze trees
        for tree_meta in self.metadata["trees"]:
            # Add to trees list
            summary["trees"].append({
                "tree_id": tree_meta["tree_id"],
                "root_url": tree_meta["root_url"],
                "topic": tree_meta.get("topic", "Unknown"),
                "subtopic": tree_meta.get("subtopic", "Unknown"),
                "stats": tree_meta.get("stats", {})
            })

            # Group by topic
            topic = tree_meta.get("topic", "Unknown")
            if topic not in summary["trees_by_topic"]:
                summary["trees_by_topic"][topic] = 0
            summary["trees_by_topic"][topic] += 1

            # Group by domain
            domain = tree_meta.get("domain", "Unknown")
            if domain not in summary["trees_by_domain"]:
                summary["trees_by_domain"][domain] = 0
            summary["trees_by_domain"][domain] += 1

        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, indent=2, fp=f)

        return summary

    def print_summary(self):
        """Print a summary of the dataset"""
        summary = self.export_summary()

        print("\n" + "=" * 60)
        print("DATASET SUMMARY")
        print("=" * 60)
        print(f"Total Trees: {summary['dataset_info']['total_trees']}")
        print(f"Dataset Directory: {summary['dataset_info']['dataset_dir']}")
        print(f"Created: {summary['dataset_info']['created_at']}")
        print(f"Updated: {summary['dataset_info']['updated_at']}")

        print("\n--- Trees by Topic ---")
        for topic, count in sorted(summary['trees_by_topic'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {topic}: {count}")

        print("\n--- Trees by Domain ---")
        for domain, count in sorted(summary['trees_by_domain'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {domain}: {count}")

        print("=" * 60)


if __name__ == '__main__':
    # Test the dataset manager
    manager = DatasetManager("data/test_dataset")
    print(f"Dataset initialized at: {manager.dataset_dir}")
    print(f"Current tree count: {manager.get_tree_count()}")
