#!/usr/bin/env python3
"""
Website Tree Visualizer - Main Entry Point

Visualize website tree structure from JSON files.
"""

import argparse
import json
import sys

from utils.io_utils import load_tree_from_json
from utils.visualization_utils import (
    print_tree_compact,
    print_tree_summary,
    print_tree_detailed,
    print_tree_with_stats,
    print_tree_by_depth,
    print_tree_clustered,
    print_clusters_summary,
    print_tree_interactive_menu
)


def main():
    parser = argparse.ArgumentParser(
        description='Visualize Website Tree from JSON file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive menu
  python visualize.py data/website_tree.json

  # Compact view
  python visualize.py data/website_tree.json --style compact

  # Detailed view with full info
  python visualize.py data/website_tree.json --style detailed

  # Statistics view
  python visualize.py data/website_tree.json --style stats

  # View organized by depth
  python visualize.py data/website_tree.json --style depth

  # Clustered view (grouped by relationship)
  python visualize.py data/website_tree.json --style clustered
        """
    )

    parser.add_argument('json_file', default='data/website_tree.json', nargs='?',
                       help='Path to the JSON tree file (default: data/website_tree.json)')
    parser.add_argument('--style', '-s',
                       choices=['compact', 'summary', 'detailed', 'stats', 'depth', 'clustered', 'interactive'],
                       default='interactive',
                       help='Visualization style (default: interactive)')
    parser.add_argument('--max-depth', type=int,
                       help='Maximum depth to display (for depth style)')
    parser.add_argument('--show-content', action='store_true',
                       help='Show page content in detailed/clustered views')
    parser.add_argument('--max-content-chars', type=int, default=200,
                       help='Maximum content characters to display (default: 200)')

    args = parser.parse_args()

    try:
        print(f"Loading tree from {args.json_file}...")
        root = load_tree_from_json(args.json_file)
        print(f"Tree loaded successfully!\n")

        if args.style == 'interactive':
            print_tree_interactive_menu(root)
        else:
            print("=" * 80)
            if args.style == 'compact':
                print("COMPACT TREE VIEW")
                print("=" * 80)
                print_tree_compact(root)
            elif args.style == 'summary':
                print("SUMMARY TREE VIEW")
                print("=" * 80)
                print_tree_summary(root)
            elif args.style == 'detailed':
                print("DETAILED TREE VIEW")
                print("=" * 80)
                print_tree_detailed(root, show_urls=True, show_descriptions=True,
                                  show_content=args.show_content,
                                  max_content_chars=args.max_content_chars,
                                  show_link_contexts=True, max_contexts=3)
            elif args.style == 'stats':
                print("TREE WITH STATISTICS")
                print("=" * 80)
                stats = print_tree_with_stats(root)
                print("\n" + "=" * 80)
                print("CUMULATIVE STATISTICS")
                print("=" * 80)
                print(f"Total Nodes:       {stats['total_nodes']}")
                print(f"Crawled Success:   {stats['crawled_nodes']}")
                print(f"Failed Crawls:     {stats['failed_nodes']}")
                print(f"Total Links Found: {stats['total_links']}")
                print(f"Max Depth:         {stats['max_depth']}")
                print(f"Unique Domains:    {len(stats['domains'])}")
            elif args.style == 'depth':
                print_tree_by_depth(root, args.max_depth)
            elif args.style == 'clustered':
                print("CLUSTERED TREE VIEW (Grouped by Relationship)")
                print("=" * 80)
                print_tree_clustered(root, show_details=True,
                                   show_content=args.show_content,
                                   max_content_chars=args.max_content_chars)
                print("\n" + "=" * 80)
                print("RELATIONSHIP DISTRIBUTION")
                print("=" * 80)
                print_clusters_summary(root)

    except FileNotFoundError:
        print(f"Error: File '{args.json_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file. {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
