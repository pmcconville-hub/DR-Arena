#!/usr/bin/env python3
"""
Website Tree Crawler - Main Entry Point

Crawl websites and build a tree structure showing hyperlink relationships.
"""

import argparse
import sys

from utils.crawler_utils import WebsiteTreeCrawler
from utils.io_utils import save_tree_to_json


def main():
    parser = argparse.ArgumentParser(
        description='Crawl websites and build a tree structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl a URL with default settings
  python crawl.py https://example.com

  # Crawl with custom depth and children limits
  python crawl.py https://example.com --max-depth 3 --max-children 5

  # Save to specific output file
  python crawl.py https://example.com --output my_tree.json

  # Disable meaningful link filtering
  python crawl.py https://example.com --no-filter

  # Restrict to top 100 domains
  python crawl.py https://example.com --no-allow-all --moz-csv data/moz_websites.csv
        """
    )

    parser.add_argument('url', help='Starting URL to crawl')
    parser.add_argument('--max-depth', type=int, default=2,
                       help='Maximum crawl depth (default: 2)')
    parser.add_argument('--max-children', type=int, default=10,
                       help='Maximum children per node (default: 10)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--output', '-o', default='data/website_tree.json',
                       help='Output JSON file (default: data/website_tree.json)')
    parser.add_argument('--no-filter', action='store_true',
                       help='Disable meaningful link filtering')
    parser.add_argument('--no-allow-all', action='store_true',
                       help='Restrict crawling to top N domains from MOZ CSV')
    parser.add_argument('--moz-csv', default='data/moz_websites.csv',
                       help='Path to MOZ domains CSV (default: data/moz_websites.csv)')
    parser.add_argument('--top-n', type=int, default=100,
                       help='Number of top domains to allow (default: 100)')
    parser.add_argument('--no-random-sampling', action='store_true',
                       help='Disable random link sampling (take links in order)')

    args = parser.parse_args()

    # Create crawler
    print("Initializing crawler...")
    crawler = WebsiteTreeCrawler(
        moz_csv_path=args.moz_csv,
        top_n=args.top_n,
        filter_meaningful=not args.no_filter,
        allow_all_domains=not args.no_allow_all,
        random_sampling=not args.no_random_sampling
    )

    print(f"\nCrawling: {args.url}")
    print(f"Max Depth: {args.max_depth}")
    print(f"Max Children per Node: {args.max_children}")
    print(f"Delay: {args.delay}s")
    print(f"Filter Meaningful Links: {not args.no_filter}")
    print(f"Allow All Domains: {not args.no_allow_all}")
    print(f"Random Link Sampling: {not args.no_random_sampling}")
    print()

    try:
        # Crawl the tree
        root = crawler.crawl_tree(
            root_url=args.url,
            max_depth=args.max_depth,
            max_children=args.max_children,
            delay=args.delay
        )

        # Save to JSON
        print(f"\nSaving tree to {args.output}...")
        save_tree_to_json(root, args.output)
        print(f"✓ Tree saved successfully!")

        # Print summary statistics
        def count_nodes(node):
            total = 1
            crawled = 1 if node.crawled else 0
            for child in node.children:
                child_total, child_crawled = count_nodes(child)
                total += child_total
                crawled += child_crawled
            return total, crawled

        total_nodes, crawled_nodes = count_nodes(root)
        print(f"\nCrawl Summary:")
        print(f"  Total Nodes: {total_nodes}")
        print(f"  Successfully Crawled: {crawled_nodes}")
        print(f"  Failed: {total_nodes - crawled_nodes}")
        print(f"\nTo visualize the tree, run:")
        print(f"  python visualize.py {args.output}")

    except KeyboardInterrupt:
        print("\n\nCrawl interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
