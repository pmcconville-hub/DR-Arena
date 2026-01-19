#!/usr/bin/env python3
"""
Website Tree Expander

Expand existing website trees by adding more width (siblings) or depth (children).
"""

import argparse
import sys
from typing import Optional, Set

from utils.crawler_utils import WebsiteTreeCrawler
from utils.io_utils import save_tree_to_json, load_tree_from_json
from utils.visualization_utils import print_tree_compact, print_tree_clustered
from models.tree_models import WebsiteNode


def find_node_by_url(root: WebsiteNode, url: str) -> Optional[WebsiteNode]:
    """
    Find a node in the tree by URL.

    Args:
        root: Root node to search from
        url: URL to search for

    Returns:
        The node if found, None otherwise
    """
    if root.url == url:
        return root

    for child in root.children:
        result = find_node_by_url(child, url)
        if result:
            return result

    return None


def collect_all_visited_urls(node: WebsiteNode) -> Set[str]:
    """
    Collect all URLs that have been visited in the tree.

    Args:
        node: Root node to collect from

    Returns:
        Set of all visited URLs in the tree
    """
    visited = {node.url}
    for child in node.children:
        visited.update(collect_all_visited_urls(child))
    return visited


def list_nodes_interactive(root: WebsiteNode, current_depth: int = 0, max_depth: int = None,
                          show_expandability: bool = False, visited_urls: Set[str] = None,
                          tree_root: WebsiteNode = None):
    """
    List all nodes in the tree with indices for selection.

    Args:
        root: Root node
        current_depth: Current depth in tree
        max_depth: Maximum depth to display
        show_expandability: Whether to show expansion capabilities
        visited_urls: Set of all visited URLs in the tree (internal use)
        tree_root: Root of entire tree for collecting visited URLs (internal use)
    """
    # Collect visited URLs from entire tree on first call
    if current_depth == 0 and show_expandability and visited_urls is None:
        tree_root = root
        visited_urls = collect_all_visited_urls(root)

    if max_depth is not None and current_depth > max_depth:
        return

    indent = "  " * current_depth
    status = "✓" if root.crawled else "✗"
    title = root.title[:60] + "..." if root.title and len(root.title) > 60 else root.title or "No title"

    print(f"{indent}[{status}] {root.url}")
    print(f"{indent}    Title: {title}")
    print(f"{indent}    Depth: {current_depth}, Children: {len(root.children)}, Links: {len(root.link_contexts)}")

    # Show expandability analysis if requested
    if show_expandability and root.crawled:
        expandability = []

        # Check width expansion - can we add more children beyond current count?
        # Width expansion allows going beyond original max_children limit
        existing_child_urls = {child.url for child in root.children}

        # Find links that aren't already children (may or may not be visited elsewhere)
        available_for_width = []
        for link_ctx in root.link_contexts:
            if link_ctx.url not in existing_child_urls:
                available_for_width.append(link_ctx)

        available_count = len(available_for_width)
        if available_count > 0:
            expandability.append(f"Width: ✓ {available_count} more children possible")
        elif len(root.link_contexts) > len(root.children):
            expandability.append("Width: ✗ links already children")
        else:
            expandability.append("Width: ✗ no more links")

        # Check depth expansion - can children be crawled deeper?
        # Depth means: do children have links that could become grandchildren?
        if len(root.children) > 0:
            # Count children that have links (regardless of whether visited)
            children_with_links = sum(1 for child in root.children if child.crawled and len(child.link_contexts) > 0)
            if children_with_links > 0:
                expandability.append(f"Depth: ✓ {children_with_links}/{len(root.children)} children have links")
            else:
                expandability.append(f"Depth: ✗ children are leaf nodes")
        elif len(root.link_contexts) > 0:
            expandability.append("Depth: ⚠ need width first")
        else:
            expandability.append("Depth: ✗ no links")

        # Color code the expandability status
        expand_str = " | ".join(expandability)
        if "Width: ✓" in expand_str or "Depth: ✓" in expand_str:
            # At least one expansion type is possible
            print(f"{indent}    🟢 Expandable: {expand_str}")
        elif "⚠" in expand_str:
            print(f"{indent}    🟡 Partial: {expand_str}")
        else:
            print(f"{indent}    🔴 Not expandable: {expand_str}")

    for child in root.children:
        list_nodes_interactive(child, current_depth + 1, max_depth, show_expandability, visited_urls, tree_root)



def visualize_tree_with_highlights(root: WebsiteNode, new_urls: set,
                                   prefix: str = "", is_last: bool = True,
                                   show_details: bool = True):
    """
    Visualize tree with newly added nodes highlighted.

    Args:
        root: Root node of tree
        new_urls: Set of URLs that were newly added
        prefix: Current line prefix for tree drawing
        is_last: Whether this is the last child
        show_details: Whether to show detailed information
    """
    from collections import defaultdict

    connector = "└── " if is_last else "├── "
    status = "✓" if root.crawled else "✗"

    # Check if this node is new
    is_new = root.url in new_urls
    new_marker = " 🆕 NEW" if is_new else ""

    # Use different color/formatting for new nodes
    if is_new:
        # Highlight new nodes with asterisks
        print(f"{prefix}{connector}[{status}] *** {root.domain} ***{new_marker}")
    else:
        print(f"{prefix}{connector}[{status}] {root.domain}{new_marker}")

    if root.title:
        title = root.title[:60] + "..." if len(root.title) > 60 else root.title
        title_prefix = "    📄 *** " if is_new else "    📄 "
        title_suffix = " ***" if is_new else ""
        print(f"{prefix}{'    ' if is_last else '│   '}{title_prefix}{title}{title_suffix}")

    if show_details and root.crawled:
        stats_prefix = "    📊 *** " if is_new else "    📊 "
        stats_suffix = " ***" if is_new else ""
        print(f"{prefix}{'    ' if is_last else '│   '}{stats_prefix}{len(root.children)} children, {len(root.link_contexts)} links{stats_suffix}")

    # Group children by relationship cluster (like clustered view)
    if root.children:
        # Build URL to relationship mapping
        url_to_relationship = {}
        for link_ctx in root.link_contexts:
            url_to_relationship[link_ctx.url] = link_ctx.relationship

        clusters = defaultdict(list)
        for child in root.children:
            relationship = url_to_relationship.get(child.url)
            cluster_name = relationship if relationship else "uncategorized"
            clusters[cluster_name].append(child)

        extension = "    " if is_last else "│   "
        sorted_clusters = sorted(clusters.items())

        for cluster_idx, (cluster_name, children) in enumerate(sorted_clusters):
            is_last_cluster = (cluster_idx == len(sorted_clusters) - 1)
            cluster_connector = "└─" if is_last_cluster else "├─"
            cluster_extension = "  " if is_last_cluster else "│ "

            # Count new nodes in this cluster
            new_count = sum(1 for child in children if child.url in new_urls)
            cluster_marker = f" ({new_count} new)" if new_count > 0 else ""

            print(f"{prefix}{extension}{cluster_connector} 🏷️  {cluster_name} ({len(children)}){cluster_marker}")

            for child_idx, child in enumerate(children):
                is_last_child = (child_idx == len(children) - 1)
                child_prefix = f"{prefix}{extension}{cluster_extension}   "
                visualize_tree_with_highlights(child, new_urls, child_prefix,
                                              is_last_child, show_details)


def print_expansion_summary(new_urls: set, expansion_type: str, node_url: str):
    """
    Print a summary of what was added.

    Args:
        new_urls: Set of newly added URLs
        expansion_type: "width" or "depth"
        node_url: URL of the expanded node
    """
    print("\n" + "=" * 80)
    print("EXPANSION SUMMARY")
    print("=" * 80)
    print(f"Expansion Type: {expansion_type.upper()}")
    print(f"Expanded Node: {node_url}")
    print(f"Total New Nodes: {len(new_urls)}")
    print("\nNewly Added URLs:")
    for i, url in enumerate(sorted(new_urls), 1):
        print(f"  {i}. {url}")
    print("=" * 80)



def expand_width(node: WebsiteNode, crawler: WebsiteTreeCrawler,
                 additional_children: int, delay: float = 1.0) -> tuple[int, set]:
    """
    Expand the width of a node by adding more children from available links.

    Args:
        node: The node to expand
        crawler: Crawler instance
        additional_children: Number of additional children to add
        delay: Delay between requests

    Returns:
        Tuple of (number of children added, set of new URLs)
    """
    new_urls = set()

    if not node.crawled:
        print(f"Error: Node {node.url} was not successfully crawled.")
        return 0, new_urls

    print(f"\nExpanding width of: {node.url}")
    print(f"Current children: {len(node.children)}")
    print(f"Available links: {len(node.link_contexts)}")

    # Get URLs of existing children
    existing_urls = {child.url for child in node.children}

    # Find links that aren't already children of this node
    # Note: We don't check crawler.visited_urls here - width expansion
    # can add nodes even if they exist elsewhere in the tree
    available_links = []
    for link_ctx in node.link_contexts:
        if link_ctx.url not in existing_urls:
            available_links.append(link_ctx)

    print(f"Links not yet children of this node: {len(available_links)}")

    if not available_links:
        print("No more links available to expand width.")
        return 0, new_urls

    # Limit to requested number
    links_to_add = available_links[:additional_children]
    print(f"Adding {len(links_to_add)} new children...")

    added = 0
    for i, link_ctx in enumerate(links_to_add):
        if i > 0:
            import time
            time.sleep(delay)

        print(f"  [{i+1}/{len(links_to_add)}] Crawling: {link_ctx.url}")

        # Check if this URL was already crawled elsewhere (will appear as visited)
        already_visited = link_ctx.url in crawler.visited_urls

        # Create child node
        child_node = WebsiteNode(
            url=link_ctx.url,
            domain=crawler._extract_domain(link_ctx.url),
            depth=node.depth + 1,
            relationship_cluster=link_ctx.relationship
        )

        # If already visited, we need to crawl it again to get fresh data
        # (or we could try to find and copy the existing node, but re-crawling is simpler)
        if already_visited:
            print(f"    (Note: URL was crawled elsewhere in tree, re-crawling for this branch)")
            # Remove from visited temporarily to allow re-crawling
            crawler.visited_urls.discard(child_node.url)

        # Crawl the child (only 1 level - no recursion)
        crawler.visited_urls.add(child_node.url)

        soup, error = crawler._crawl_page(child_node.url)

        if error or soup is None:
            child_node.error = error or "Unknown error"
            child_node.crawled = False
            print(f"    Error: {child_node.error}")
        else:
            child_node.title, child_node.description = crawler._extract_metadata(soup)
            child_node.crawled = True
            child_node.content = crawler._extract_content(soup)
            child_node.link_contexts = crawler._extract_links(soup, child_node.url, child_node.title)
            print(f"    ✓ Success: {child_node.title}")

        node.children.append(child_node)
        new_urls.add(child_node.url)  # Track new URL
        added += 1

    print(f"✓ Added {added} children. Total children: {len(node.children)}")
    return added, new_urls


def expand_depth(node: WebsiteNode, crawler: WebsiteTreeCrawler,
                 additional_depth: int, max_children: int, delay: float = 1.0) -> tuple[int, set]:
    """
    Expand the depth of a node by crawling its children deeper.

    Args:
        node: The node to expand
        crawler: Crawler instance
        additional_depth: Number of additional depth levels to add
        max_children: Maximum children per node
        delay: Delay between requests

    Returns:
        Tuple of (number of new nodes added, set of new URLs)
    """
    new_urls = set()

    if not node.crawled:
        print(f"Error: Node {node.url} was not successfully crawled.")
        return 0, new_urls

    print(f"\nExpanding depth from: {node.url}")
    print(f"Current depth: {node.depth}")

    # Find current maximum depth in the subtree
    def find_max_depth(n):
        if not n.children:
            return n.depth
        return max(find_max_depth(child) for child in n.children)

    current_max_depth = find_max_depth(node)
    target_depth = current_max_depth + additional_depth

    print(f"Current maximum depth in subtree: {current_max_depth}")
    print(f"Will expand to depth: {target_depth}")

    # Count initial nodes
    def count_nodes(n):
        count = 1
        for child in n.children:
            count += count_nodes(child)
        return count

    initial_count = count_nodes(node)

    # Crawl children recursively - use the target_depth calculated above
    # (not node.depth + additional_depth)

    def crawl_children_recursive(parent_node: WebsiteNode, max_depth: int):
        """Recursively crawl children up to max_depth"""
        if parent_node.depth >= max_depth:
            return

        # Get existing child URLs
        existing_child_urls = {child.url for child in parent_node.children}

        # If this is a leaf node (no link_contexts), we need to re-crawl it to get links
        if parent_node.crawled and not parent_node.link_contexts and parent_node.depth < max_depth:
            print(f"  Re-crawling leaf node to extract links: {parent_node.url} (depth {parent_node.depth})")
            soup, error = crawler._crawl_page(parent_node.url)
            if error or soup is None:
                print(f"    Error re-crawling: {error}")
            else:
                parent_node.link_contexts = crawler._extract_links(soup, parent_node.url, parent_node.title)
                print(f"    Found {len(parent_node.link_contexts)} links")

        # If node has link contexts but not all are children, create more children
        if parent_node.link_contexts:
            # Find links that aren't already children (similar to width expansion)
            available_links = []
            for link_ctx in parent_node.link_contexts:
                if link_ctx.url not in existing_child_urls:
                    available_links.append(link_ctx)

            # Limit to max_children total (not additional)
            needed = max_children - len(parent_node.children)
            if needed > 0 and available_links:
                links_to_add = available_links[:needed]
                print(f"  Adding {len(links_to_add)} children to: {parent_node.url} (depth {parent_node.depth})")

                for i, link_ctx in enumerate(links_to_add):
                    if i > 0 or len(parent_node.children) > 0:
                        import time
                        time.sleep(delay)

                    # Check if already visited elsewhere
                    already_visited = link_ctx.url in crawler.visited_urls
                    if already_visited:
                        # Remove temporarily to allow re-crawling
                        crawler.visited_urls.discard(link_ctx.url)

                    child_node = WebsiteNode(
                        url=link_ctx.url,
                        domain=crawler._extract_domain(link_ctx.url),
                        depth=parent_node.depth + 1,
                        relationship_cluster=link_ctx.relationship
                    )

                    # Crawl child
                    crawler.visited_urls.add(child_node.url)
                    soup, error = crawler._crawl_page(child_node.url)

                    if error or soup is None:
                        child_node.error = error or "Unknown error"
                        child_node.crawled = False
                        print(f"    Error crawling {link_ctx.url}: {child_node.error}")
                    else:
                        child_node.title, child_node.description = crawler._extract_metadata(soup)
                        child_node.crawled = True
                        child_node.content = crawler._extract_content(soup)
                        child_node.link_contexts = crawler._extract_links(soup, child_node.url, child_node.title)
                        print(f"    ✓ Added: {child_node.title}")

                    parent_node.children.append(child_node)
                    new_urls.add(child_node.url)  # Track new URL

        # Recursively process existing children to go deeper
        for child in parent_node.children:
            crawl_children_recursive(child, max_depth)

    # Start recursive crawl
    crawl_children_recursive(node, target_depth)

    final_count = count_nodes(node)
    added = final_count - initial_count

    print(f"✓ Added {added} nodes. Total nodes in subtree: {final_count}")
    return added, new_urls


def main():
    parser = argparse.ArgumentParser(
        description='Expand existing website trees by width or depth',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode - select node and expansion type
  python expand_tree.py data/website_tree.json

  # List all nodes with expandability analysis
  python expand_tree.py data/coffee_tree.json --list-nodes --show-expandability

  # Expand width - add more children to a specific node
  python expand_tree.py data/coffee_tree.json \
    --url "https://varieties.worldcoffeeresearch.org/about-the-catalog/whats-included" \
    --width 5 \
    --output data/wider_tree.json

  # Expand depth - make tree deeper from a specific node
  python expand_tree.py data/website_tree.json \\
    --url "https://example.com" \\
    --depth 2 \\
    --max-children 5 \\
    --output data/deeper_tree.json

  # Expand and visualize with highlights
  python expand_tree.py data/website_tree.json \\
    --url "https://example.com/page" \\
    --width 3 \\
    --visualize

  # List all nodes to find URLs
  python expand_tree.py data/website_tree.json --list-nodes
        """
    )

    parser.add_argument('input_file', help='Input JSON tree file')
    parser.add_argument('--url', help='URL of node to expand')
    parser.add_argument('--width', type=int,
                       help='Expand width: add N additional children to the node')
    parser.add_argument('--depth', type=int,
                       help='Expand depth: add N additional depth levels')
    parser.add_argument('--max-children', type=int, default=10,
                       help='Maximum children per node when expanding depth (default: 10)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--output', '-o',
                       help='Output JSON file (default: overwrite input)')
    parser.add_argument('--list-nodes', action='store_true',
                       help='List all nodes in the tree and exit')
    parser.add_argument('--max-list-depth', type=int,
                       help='Maximum depth to display when listing nodes')
    parser.add_argument('--show-expandability', action='store_true',
                       help='Show expansion capabilities when listing nodes (use with --list-nodes)')
    parser.add_argument('--preview', action='store_true',
                       help='Preview the expanded tree without saving')
    parser.add_argument('--visualize', action='store_true',
                       help='Visualize the expanded tree with new nodes highlighted')

    args = parser.parse_args()

    try:
        # Load tree
        print(f"Loading tree from {args.input_file}...")
        root = load_tree_from_json(args.input_file)
        print(f"✓ Tree loaded successfully!")

        # List nodes mode
        if args.list_nodes:
            print("\n" + "=" * 80)
            if args.show_expandability:
                print("NODES IN TREE (with Expandability Analysis)")
                print("=" * 80)
                print("\nLegend:")
                print("  🟢 Expandable - Can expand (width and/or depth)")
                print("  🟡 Partial - Can expand width first, then depth")
                print("  🔴 Not expandable - Leaf node with no links")
                print("  ✓ = Available | ✗ = Not available | ⚠ = Conditional")
            else:
                print("NODES IN TREE")
                print("=" * 80)
                print("\nTip: Use --show-expandability to see which nodes can be expanded")
            print()
            list_nodes_interactive(root, max_depth=args.max_list_depth,
                                 show_expandability=args.show_expandability)
            return

        # Interactive mode
        if not args.url:
            print("\n" + "=" * 80)
            print("INTERACTIVE EXPANSION MODE")
            print("=" * 80)

            # Show current tree
            print("\nCurrent tree structure:")
            print("-" * 80)
            print_tree_compact(root)
            print("-" * 80)

            # Get URL
            print("\nAvailable nodes:")
            list_nodes_interactive(root, max_depth=2)

            url = input("\nEnter the URL of the node to expand: ").strip()
            if not url:
                print("No URL provided. Exiting.")
                return

            # Get expansion type
            print("\nExpansion options:")
            print("  1. Width  - Add more sibling nodes (more children to this node)")
            print("  2. Depth  - Make tree deeper (crawl children's children)")

            choice = input("\nChoose expansion type (1 or 2): ").strip()

            if choice == '1':
                amount = input("How many additional children to add? ").strip()
                try:
                    args.width = int(amount)
                    args.url = url
                except ValueError:
                    print("Invalid number. Exiting.")
                    return
            elif choice == '2':
                amount = input("How many additional depth levels to add? ").strip()
                try:
                    args.depth = int(amount)
                    args.url = url
                    max_children = input(f"Max children per node (default: {args.max_children}): ").strip()
                    if max_children:
                        args.max_children = int(max_children)
                except ValueError:
                    print("Invalid number. Exiting.")
                    return
            else:
                print("Invalid choice. Exiting.")
                return

        # Validate arguments
        if not args.url:
            print("Error: --url is required (or use interactive mode)")
            sys.exit(1)

        if not args.width and not args.depth:
            print("Error: Either --width or --depth must be specified")
            sys.exit(1)

        if args.width and args.depth:
            print("Error: Cannot expand both width and depth simultaneously")
            sys.exit(1)

        # Find the node
        print(f"\nSearching for node: {args.url}")
        node = find_node_by_url(root, args.url)

        if not node:
            print(f"Error: Node with URL '{args.url}' not found in tree.")
            print("\nUse --list-nodes to see all available nodes.")
            sys.exit(1)

        print(f"✓ Found node: {node.title or 'No title'}")
        print(f"  Depth: {node.depth}")
        print(f"  Children: {len(node.children)}")
        print(f"  Links: {len(node.link_contexts)}")

        # Initialize crawler
        print("\nInitializing crawler...")
        crawler = WebsiteTreeCrawler(allow_all_domains=True)

        # Restore visited URLs from tree
        def collect_visited(n: WebsiteNode):
            crawler.visited_urls.add(n.url)
            for child in n.children:
                collect_visited(child)

        collect_visited(root)
        print(f"Restored {len(crawler.visited_urls)} visited URLs from tree")

        # Perform expansion
        added = 0
        new_urls = set()
        expansion_type = ""

        if args.width:
            added, new_urls = expand_width(node, crawler, args.width, args.delay)
            expansion_type = "width"
        elif args.depth:
            added, new_urls = expand_depth(node, crawler, args.depth, args.max_children, args.delay)
            expansion_type = "depth"

        if added == 0:
            print("\nNo nodes were added.")
            return

        # Show expansion summary
        print_expansion_summary(new_urls, expansion_type, args.url)

        # Visualize with highlights if requested
        if args.visualize:
            print("\n" + "=" * 80)
            print("EXPANDED TREE WITH NEW NODES HIGHLIGHTED")
            print("=" * 80)
            print("Legend: *** NEW NODE *** = Newly added node 🆕\n")
            visualize_tree_with_highlights(root, new_urls, show_details=True)

        # Preview or save
        if args.preview:
            print("\n" + "=" * 80)
            print("PREVIEW: Expanded Tree (Clustered View)")
            print("=" * 80)
            print_tree_clustered(root, show_details=True)

            save = input("\nSave this tree? (y/n): ").strip().lower()
            if save != 'y':
                print("Tree not saved.")
                return

        # Save the expanded tree
        output_file = args.output or args.input_file
        print(f"\nSaving expanded tree to {output_file}...")
        save_tree_to_json(root, output_file)
        print(f"✓ Tree saved successfully!")

        # Final summary
        print("\n" + "=" * 80)
        print("SAVE COMPLETE")
        print("=" * 80)
        print(f"Output file: {output_file}")
        print(f"Total new nodes: {added}")

        print("\nNext steps:")
        print(f"  # Visualize with standard clustered view:")
        print(f"  python visualize.py {output_file} --style clustered")
        print(f"\n  # Or visualize with highlights (run expand_tree.py again):")
        print(f"  python expand_tree.py {output_file} --visualize")
        print("=" * 80)

    except FileNotFoundError:
        print(f"Error: File '{args.input_file}' not found.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nExpansion interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
