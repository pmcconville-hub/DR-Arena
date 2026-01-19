"""
Tree validation utilities for checking tree quality
"""

from typing import Tuple, Dict
from models.tree_models import WebsiteNode


class TreeValidator:
    """Validate tree quality based on depth and width criteria"""

    @staticmethod
    def get_tree_stats(root: WebsiteNode) -> Dict:
        """
        Calculate statistics about the tree.

        Args:
            root: Root node of the tree

        Returns:
            Dictionary with tree statistics
        """
        stats = {
            'max_depth': 0,
            'total_nodes': 0,
            'crawled_nodes': 0,
            'failed_nodes': 0,
            'nodes_by_depth': {},
            'min_width_at_depth': {},
            'max_width_at_depth': {},
            'avg_width': 0.0
        }

        def traverse(node: WebsiteNode, depth: int = 0):
            """Recursively traverse tree and collect stats"""
            stats['total_nodes'] += 1
            stats['max_depth'] = max(stats['max_depth'], depth)

            if node.crawled:
                stats['crawled_nodes'] += 1
            else:
                stats['failed_nodes'] += 1

            # Track nodes by depth
            if depth not in stats['nodes_by_depth']:
                stats['nodes_by_depth'][depth] = 0
            stats['nodes_by_depth'][depth] += 1

            # Track width (number of children) at each depth
            if node.children:
                child_count = len(node.children)
                if depth not in stats['min_width_at_depth']:
                    stats['min_width_at_depth'][depth] = child_count
                    stats['max_width_at_depth'][depth] = child_count
                else:
                    stats['min_width_at_depth'][depth] = min(
                        stats['min_width_at_depth'][depth], child_count
                    )
                    stats['max_width_at_depth'][depth] = max(
                        stats['max_width_at_depth'][depth], child_count
                    )

                # Recurse to children
                for child in node.children:
                    traverse(child, depth + 1)

        traverse(root)

        # Calculate average width
        if stats['nodes_by_depth']:
            total_width = sum(stats['nodes_by_depth'].values())
            stats['avg_width'] = total_width / len(stats['nodes_by_depth'])

        return stats

    @staticmethod
    def validate_tree(root: WebsiteNode, min_depth: int = 3, min_width: int = 2) -> Tuple[bool, str, Dict]:
        """
        Validate if a tree meets quality criteria.

        Args:
            root: Root node of the tree
            min_depth: Minimum required depth (inclusive, so min_depth=3 means depth must be >= 3)
            min_width: Minimum width (children count) required at intermediate levels

        Returns:
            Tuple of (is_valid, reason, stats)
        """
        stats = TreeValidator.get_tree_stats(root)

        # Check if tree has minimum depth
        if stats['max_depth'] < min_depth:
            return False, f"Tree depth {stats['max_depth']} is less than minimum {min_depth}", stats

        # Check if tree has reasonable width
        # We check that at least one level (excluding leaf level) has min_width children
        has_sufficient_width = False
        for depth in range(stats['max_depth']):  # Exclude leaf level
            if depth in stats['min_width_at_depth']:
                if stats['min_width_at_depth'][depth] >= min_width:
                    has_sufficient_width = True
                    break

        if not has_sufficient_width:
            return False, f"Tree does not have sufficient width (min {min_width} children at any level)", stats

        # Check if enough nodes were successfully crawled
        crawl_success_rate = stats['crawled_nodes'] / stats['total_nodes'] if stats['total_nodes'] > 0 else 0
        if crawl_success_rate < 0.5:
            return False, f"Too many failed crawls ({stats['failed_nodes']}/{stats['total_nodes']})", stats

        # Check if tree has reasonable number of nodes
        if stats['total_nodes'] < min_depth + min_width:
            return False, f"Tree has too few nodes ({stats['total_nodes']})", stats

        return True, "Tree meets quality criteria", stats

    @staticmethod
    def print_tree_stats(stats: Dict):
        """Pretty print tree statistics"""
        print("\n=== Tree Statistics ===")
        print(f"Max Depth: {stats['max_depth']}")
        print(f"Total Nodes: {stats['total_nodes']}")
        print(f"Crawled Nodes: {stats['crawled_nodes']}")
        print(f"Failed Nodes: {stats['failed_nodes']}")
        print(f"Success Rate: {stats['crawled_nodes']/stats['total_nodes']*100:.1f}%")
        print(f"Average Width: {stats['avg_width']:.2f}")
        print("\nNodes per depth:")
        for depth in sorted(stats['nodes_by_depth'].keys()):
            count = stats['nodes_by_depth'][depth]
            width_info = ""
            if depth in stats['min_width_at_depth']:
                width_info = f" (width: {stats['min_width_at_depth'][depth]}-{stats['max_width_at_depth'][depth]})"
            print(f"  Depth {depth}: {count} nodes{width_info}")


if __name__ == '__main__':
    # This would be used with actual tree data
    print("Tree validator module loaded successfully")
