"""
Visualization utilities for website tree data.
"""

import sys
from typing import Dict, Optional
from collections import defaultdict
from io import StringIO

from models.tree_models import WebsiteNode


def print_tree_summary(node: WebsiteNode, prefix: str = "", is_last: bool = True):
    """Print a text summary of the tree"""
    connector = "└── " if is_last else "├── "
    
    status = "✓" if node.crawled else "✗"
    title = node.title[:50] + "..." if node.title and len(node.title) > 50 else node.title
    
    print(f"{prefix}{connector}[{status}] {node.domain}")
    if title:
        print(f"{prefix}{'    ' if is_last else '│   '}    Title: {title}")
    if node.error:
        print(f"{prefix}{'    ' if is_last else '│   '}    Error: {node.error}")
    if node.link_contexts:
        print(f"{prefix}{'    ' if is_last else '│   '}    Links found: {len(node.link_contexts)}")
    
    extension = "    " if is_last else "│   "
    for i, child in enumerate(node.children):
        is_last_child = (i == len(node.children) - 1)
        print_tree_summary(child, prefix + extension, is_last_child)


def print_tree_detailed(node: WebsiteNode, prefix: str = "", is_last: bool = True,
                       show_urls: bool = True, show_descriptions: bool = False,
                       show_content: bool = False, max_content_chars: int = 200,
                       show_link_contexts: bool = False, max_contexts: int = 3):
    """Print a detailed tree visualization"""
    connector = "└── " if is_last else "├── "
    extension = "    " if is_last else "│   "
    
    status = "✓" if node.crawled else "✗"
    depth_marker = f"[D{node.depth}]"
    print(f"{prefix}{connector}{status} {depth_marker} {node.domain}")
    
    if node.title:
        title = node.title[:80] + "..." if len(node.title) > 80 else node.title
        print(f"{prefix}{extension}  📄 {title}")
    
    if show_urls:
        url_display = node.url[:100] + "..." if len(node.url) > 100 else node.url
        print(f"{prefix}{extension}  🔗 {url_display}")
    
    if show_descriptions and node.description:
        desc = node.description[:150] + "..." if len(node.description) > 150 else node.description
        print(f"{prefix}{extension}  📝 {desc}")
    
    if show_content and node.content:
        content_display = node.content[:max_content_chars]
        if len(node.content) > max_content_chars:
            content_display += "..."
        print(f"{prefix}{extension}  📖 Content ({len(node.content)} chars): {content_display}")
    
    if node.error:
        error_display = node.error[:100] + "..." if len(node.error) > 100 else node.error
        print(f"{prefix}{extension}  ❌ {error_display}")
    
    if node.crawled:
        stats = f"Children: {len(node.children)}, Links: {len(node.link_contexts)}"
        print(f"{prefix}{extension}  📊 {stats}")
    
    if show_link_contexts and node.link_contexts:
        contexts_to_show = node.link_contexts[:max_contexts]
        print(f"{prefix}{extension}  🔍 Link Contexts ({len(contexts_to_show)}/{len(node.link_contexts)}):")
        for i, ctx in enumerate(contexts_to_show):
            is_last_ctx = (i == len(contexts_to_show) - 1)
            ctx_connector = "└─" if is_last_ctx else "├─"
            ctx_extension = "  " if is_last_ctx else "│ "
            
            anchor = ctx.anchor_text[:50] + "..." if len(ctx.anchor_text) > 50 else ctx.anchor_text
            print(f"{prefix}{extension}     {ctx_connector} \"{anchor}\"")
            
            if ctx.surrounding_text:
                context = ctx.surrounding_text[:80].replace('\n', ' ')
                if len(ctx.surrounding_text) > 80:
                    context += "..."
                print(f"{prefix}{extension}     {ctx_extension}   Context: {context}")
    
    for i, child in enumerate(node.children):
        is_last_child = (i == len(node.children) - 1)
        print_tree_detailed(child, prefix + extension, is_last_child,
                          show_urls, show_descriptions, show_content, max_content_chars,
                          show_link_contexts, max_contexts)


def print_tree_compact(node: WebsiteNode, prefix: str = "", is_last: bool = True):
    """Print a compact tree view"""
    connector = "└─ " if is_last else "├─ "
    status = "✓" if node.crawled else "✗"
    
    domain_display = node.domain[:40] + "..." if len(node.domain) > 40 else node.domain
    
    if node.title:
        title_short = node.title[:30] + "..." if len(node.title) > 30 else node.title
        print(f"{prefix}{connector}[{status}] {domain_display} - {title_short}")
    else:
        print(f"{prefix}{connector}[{status}] {domain_display}")
    
    extension = "   " if is_last else "│  "
    for i, child in enumerate(node.children):
        is_last_child = (i == len(node.children) - 1)
        print_tree_compact(child, prefix + extension, is_last_child)


def print_tree_with_stats(node: WebsiteNode, stats: Dict = None, prefix: str = "",
                         is_last: bool = True) -> Dict:
    """Print tree with accumulated statistics"""
    if stats is None:
        stats = {
            'total_nodes': 0,
            'crawled_nodes': 0,
            'failed_nodes': 0,
            'total_links': 0,
            'max_depth': 0,
            'domains': set()
        }
    
    stats['total_nodes'] += 1
    if node.crawled:
        stats['crawled_nodes'] += 1
    else:
        stats['failed_nodes'] += 1
    stats['total_links'] += len(node.link_contexts)
    stats['max_depth'] = max(stats['max_depth'], node.depth)
    stats['domains'].add(node.domain)
    
    connector = "└── " if is_last else "├── "
    status = "✓" if node.crawled else "✗"
    
    info = f"[{status}] {node.domain}"
    if node.title:
        title = node.title[:40] + "..." if len(node.title) > 40 else node.title
        info += f" - {title}"
    if node.crawled:
        info += f" ({len(node.children)} children, {len(node.link_contexts)} links)"
    
    print(f"{prefix}{connector}{info}")
    
    extension = "    " if is_last else "│   "
    for i, child in enumerate(node.children):
        is_last_child = (i == len(node.children) - 1)
        print_tree_with_stats(child, stats, prefix + extension, is_last_child)
    
    return stats


def print_tree_by_depth(node: WebsiteNode, max_display_depth: Optional[int] = None):
    """Print tree organized by depth levels"""
    nodes_by_depth = defaultdict(list)
    
    def collect_nodes(n: WebsiteNode):
        if max_display_depth is None or n.depth <= max_display_depth:
            nodes_by_depth[n.depth].append(n)
            for child in n.children:
                collect_nodes(child)
    
    collect_nodes(node)
    
    print("\n" + "=" * 80)
    print("TREE ORGANIZED BY DEPTH")
    print("=" * 80)
    
    for depth in sorted(nodes_by_depth.keys()):
        nodes = nodes_by_depth[depth]
        print(f"\n{'─' * 80}")
        print(f"DEPTH {depth} ({len(nodes)} nodes)")
        print(f"{'─' * 80}")
        
        for i, n in enumerate(nodes, 1):
            status = "✓" if n.crawled else "✗"
            print(f"\n  [{i}] [{status}] {n.domain}")
            
            if n.title:
                title = n.title[:70] + "..." if len(n.title) > 70 else n.title
                print(f"      Title: {title}")
            
            if n.crawled:
                print(f"      Stats: {len(n.children)} children, {len(n.link_contexts)} links found")
            
            if n.error:
                error = n.error[:100] + "..." if len(n.error) > 100 else n.error
                print(f"      Error: {error}")


def print_tree_clustered(node: WebsiteNode, prefix: str = "", is_last: bool = True,
                        show_details: bool = True, show_content: bool = False,
                        max_content_chars: int = 200):
    """Print tree with children grouped by relationship clusters"""
    connector = "└── " if is_last else "├── "
    status = "✓" if node.crawled else "✗"
    
    print(f"{prefix}{connector}[{status}] {node.domain}")
    
    if node.title:
        title = node.title[:60] + "..." if len(node.title) > 60 else node.title
        print(f"{prefix}{'    ' if is_last else '│   '}    📄 {title}")
    
    if show_details and node.crawled:
        print(f"{prefix}{'    ' if is_last else '│   '}    📊 {len(node.children)} children, {len(node.link_contexts)} links")
    
    if show_content and node.content:
        content_display = node.content[:max_content_chars]
        if len(node.content) > max_content_chars:
            content_display += "..."
        print(f"{prefix}{'    ' if is_last else '│   '}    📖 Content ({len(node.content)} chars): {content_display}")
    
    if node.children:
        # Build URL to relationship mapping
        url_to_relationship = {}
        for link_ctx in node.link_contexts:
            url_to_relationship[link_ctx.url] = link_ctx.relationship
        
        clusters = defaultdict(list)
        for child in node.children:
            relationship = url_to_relationship.get(child.url)
            cluster_name = relationship if relationship else "uncategorized"
            clusters[cluster_name].append(child)
        
        extension = "    " if is_last else "│   "
        sorted_clusters = sorted(clusters.items())
        
        for cluster_idx, (cluster_name, children) in enumerate(sorted_clusters):
            is_last_cluster = (cluster_idx == len(sorted_clusters) - 1)
            cluster_connector = "└─" if is_last_cluster else "├─"
            cluster_extension = "  " if is_last_cluster else "│ "
            
            print(f"{prefix}{extension}{cluster_connector} 🏷️  {cluster_name} ({len(children)})")
            
            for child_idx, child in enumerate(children):
                is_last_child = (child_idx == len(children) - 1)
                child_prefix = f"{prefix}{extension}{cluster_extension}   "
                print_tree_clustered(child, child_prefix, is_last_child, show_details,
                                   show_content, max_content_chars)


def print_clusters_summary(node: WebsiteNode, max_display_depth: Optional[int] = None):
    """Print summary of relationship clusters at each depth level"""
    nodes_by_depth = defaultdict(list)
    
    def collect_nodes(n: WebsiteNode, parent_relationship: Optional[str] = None):
        if max_display_depth is None or n.depth <= max_display_depth:
            nodes_by_depth[n.depth].append((n, parent_relationship))
            
            url_to_relationship = {}
            for link_ctx in n.link_contexts:
                url_to_relationship[link_ctx.url] = link_ctx.relationship
            
            for child in n.children:
                child_relationship = url_to_relationship.get(child.url)
                collect_nodes(child, child_relationship)
    
    collect_nodes(node)
    
    print("\n" + "=" * 80)
    print("RELATIONSHIP CLUSTERS SUMMARY")
    print("=" * 80)
    
    for depth in sorted(nodes_by_depth.keys()):
        if depth == 0:
            continue
        
        nodes_with_relationships = nodes_by_depth[depth]
        
        cluster_counts = defaultdict(int)
        for n, relationship in nodes_with_relationships:
            cluster = relationship if relationship else "uncategorized"
            cluster_counts[cluster] += 1
        
        print(f"\n{'─' * 80}")
        print(f"DEPTH {depth} - Relationship Distribution ({len(nodes_with_relationships)} nodes)")
        print(f"{'─' * 80}")
        
        sorted_clusters = sorted(cluster_counts.items(), key=lambda x: x[1], reverse=True)
        
        for cluster, count in sorted_clusters:
            percentage = (count / len(nodes_with_relationships)) * 100
            bar_length = int(percentage / 2)
            bar = "█" * bar_length
            print(f"  {cluster:.<30} {count:>3} ({percentage:>5.1f}%) {bar}")


def print_tree_interactive_menu(root: WebsiteNode):
    """Interactive menu to explore the tree"""
    while True:
        print("\n" + "=" * 80)
        print("WEBSITE TREE VISUALIZATION MENU")
        print("=" * 80)
        print("\n1. Compact View (minimal info)")
        print("2. Summary View (basic info)")
        print("3. Detailed View (full info)")
        print("4. View with Statistics")
        print("5. View by Depth Levels")
        print("6. Clustered View (grouped by relationship)")
        print("7. Clusters Summary (distribution stats)")
        print("8. Custom Detailed View (choose what to show)")
        print("9. Export current view to file")
        print("0. Exit\n")
        
        try:
            choice = input("Select visualization option (0-9): ").strip()
            
            if choice == '0':
                print("\nExiting visualization menu.")
                break
            
            print("\n" + "=" * 80)
            
            if choice == '1':
                print("COMPACT TREE VIEW")
                print("=" * 80)
                print_tree_compact(root)
            
            elif choice == '2':
                print("SUMMARY TREE VIEW")
                print("=" * 80)
                print_tree_summary(root)
            
            elif choice == '3':
                print("DETAILED TREE VIEW")
                print("=" * 80)
                print_tree_detailed(root, show_urls=True, show_descriptions=True,
                                  show_link_contexts=True, max_contexts=3)
            
            elif choice == '4':
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
            
            elif choice == '5':
                max_depth_input = input("\nEnter max depth to display (press Enter for all): ").strip()
                max_depth = int(max_depth_input) if max_depth_input else None
                print_tree_by_depth(root, max_depth)
            
            elif choice == '6':
                print("CLUSTERED TREE VIEW (Grouped by Relationship)")
                print("=" * 80)
                show_content = input("\nShow content? (y/n): ").strip().lower() == 'y'
                max_content = 200
                if show_content:
                    max_content_input = input("Max content chars (default 200): ").strip()
                    max_content = int(max_content_input) if max_content_input else 200
                print_tree_clustered(root, show_details=True, show_content=show_content,
                                   max_content_chars=max_content)
            
            elif choice == '7':
                print("RELATIONSHIP CLUSTERS SUMMARY")
                print("=" * 80)
                max_depth_input = input("\nEnter max depth to analyze (press Enter for all): ").strip()
                max_depth = int(max_depth_input) if max_depth_input else None
                print_clusters_summary(root, max_depth)
            
            elif choice == '8':
                print("\nCustom Detailed View Options:")
                show_urls = input("Show full URLs? (y/n): ").strip().lower() == 'y'
                show_desc = input("Show descriptions? (y/n): ").strip().lower() == 'y'
                show_content = input("Show content? (y/n): ").strip().lower() == 'y'
                show_ctx = input("Show link contexts? (y/n): ").strip().lower() == 'y'
                
                max_content = 200
                if show_content:
                    max_content_input = input("Max content chars (default 200): ").strip()
                    max_content = int(max_content_input) if max_content_input else 200
                
                max_ctx = 3
                if show_ctx:
                    max_ctx_input = input("Max contexts per node (default 3): ").strip()
                    max_ctx = int(max_ctx_input) if max_ctx_input else 3
                
                print("\n" + "=" * 80)
                print("CUSTOM DETAILED TREE VIEW")
                print("=" * 80)
                print_tree_detailed(root, show_urls=show_urls, show_descriptions=show_desc,
                                  show_content=show_content, max_content_chars=max_content,
                                  show_link_contexts=show_ctx, max_contexts=max_ctx)
            
            elif choice == '9':
                filename = input("\nEnter filename (default: tree_view.txt): ").strip()
                filename = filename if filename else "tree_view.txt"
                
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                
                print_tree_detailed(root, show_urls=True, show_descriptions=True,
                                  show_content=True, max_content_chars=300,
                                  show_link_contexts=True, max_contexts=5)
                
                output = sys.stdout.getvalue()
                sys.stdout = old_stdout
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(output)
                
                print(f"\nTree view exported to: {filename}")
            
            else:
                print("Invalid choice. Please select 0-9.")
            
            input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\nExiting visualization menu.")
            break
        except Exception as e:
            print(f"\nError: {e}")
            input("\nPress Enter to continue...")
