#!/usr/bin/env python3
"""
Generate a dataset of crawled website trees.

This script:
1. Samples random topics/subtopics from trends.json
2. Uses an LLM to craft relevant search queries
3. Uses SerpAPI to search Google
4. Uses an LLM to select the best website from results
5. Crawls the website to build a tree
6. Validates the tree meets quality criteria
7. Saves valid trees to a dataset
8. Repeats until target number of trees is reached
"""

import argparse
import sys
import time
from typing import Optional

from utils.trends_parser import TrendsParser
from utils.llm_agent import LLMAgent
from utils.search_api import SearchAPI
from utils.crawler_utils import WebsiteTreeCrawler
from utils.tree_validator import TreeValidator
from utils.dataset_manager import DatasetManager


def generate_single_tree(
    trends_parser: TrendsParser,
    llm_agent: LLMAgent,
    search_api: SearchAPI,
    crawler: WebsiteTreeCrawler,
    validator: TreeValidator,
    max_depth: int,
    max_children: int,
    crawl_delay: float,
    min_tree_depth: int,
    min_tree_width: int,
    max_search_attempts: int = 3
) -> tuple:
    """
    Generate a single valid tree.

    Returns:
        Tuple of (success, result, error_type) where:
        - success: bool indicating if generation succeeded
        - result: (tree, metadata) if successful, None otherwise
        - error_type: 'llm', 'search', 'crawl', 'validation', or None
    """
    # 1. Sample a random topic and subtopic
    topic_path, subtopic, category_id = trends_parser.sample_random_subtopic()
    print(f"\n{'='*60}")
    print(f"Topic: {topic_path}")
    print(f"Subtopic: {subtopic}")
    print(f"Category ID: {category_id}")
    print('='*60)

    # 2. Craft search query using LLM
    print("\n[1/6] Crafting search query with LLM...")
    try:
        search_query = llm_agent.craft_search_query(topic_path, subtopic)
        print(f"✓ Search query: '{search_query}'")
    except Exception as e:
        print(f"✗ Error crafting search query: {e}")
        return (False, None, 'llm')

    # 3. Search with Google (SerpAPI)
    print("\n[2/6] Searching Google...")
    try:
        search_results = search_api.search(search_query, num_results=10)
        print(f"✓ Found {len(search_results)} results")
    except Exception as e:
        print(f"✗ Error searching: {e}")
        return (False, None, 'search')

    if not search_results:
        print("✗ No search results found")
        return (False, None, 'search')

    # 4. Use LLM to select the best website
    print("\n[3/6] Selecting best website with LLM...")
    try:
        selected_url, reasoning = llm_agent.select_best_website(
            search_results, topic_path, subtopic
        )
        if not selected_url:
            print(f"✗ No suitable website found: {reasoning}")
            return (False, None, 'llm')
        print(f"✓ Selected: {selected_url}")
        print(f"  Reasoning: {reasoning}")
    except Exception as e:
        print(f"✗ Error selecting website: {e}")
        return (False, None, 'llm')

    # 5. Crawl the website
    print(f"\n[4/6] Crawling website (max_depth={max_depth}, max_children={max_children})...")
    try:
        tree = crawler.crawl_tree(
            root_url=selected_url,
            max_depth=max_depth,
            max_children=max_children,
            delay=crawl_delay
        )
        print(f"✓ Crawl completed")
    except Exception as e:
        print(f"✗ Error crawling: {e}")
        return (False, None, 'crawl')

    # 6. Validate the tree
    print(f"\n[5/6] Validating tree (min_depth={min_tree_depth}, min_width={min_tree_width})...")
    try:
        is_valid, reason, stats = validator.validate_tree(
            tree, min_depth=min_tree_depth, min_width=min_tree_width
        )

        if is_valid:
            print(f"✓ Tree is valid: {reason}")
            validator.print_tree_stats(stats)
        else:
            print(f"✗ Tree is invalid: {reason}")
            validator.print_tree_stats(stats)
            return (False, None, 'validation')

    except Exception as e:
        print(f"✗ Error validating tree: {e}")
        return (False, None, 'validation')

    # Create metadata
    metadata = {
        "topic": topic_path,
        "subtopic": subtopic,
        "category_id": category_id,
        "search_query": search_query,
        "search_results": search_results,  # Save all search results
        "selected_url": selected_url,
        "llm_reasoning": reasoning,
        "stats": stats
    }

    return (True, (tree, metadata), None)


def main():
    parser = argparse.ArgumentParser(
        description='Generate a dataset of crawled website trees',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 100 trees with default settings
  python generate_dataset.py --target 100

  # Generate 50 trees with custom depth and width
  python generate_dataset.py --target 50 --max-depth 4 --max-children 8

  # Generate trees with custom validation criteria
  python generate_dataset.py --target 100 --min-tree-depth 4 --min-tree-width 3

Environment Variables Required:
  ANTHROPIC_API_KEY - Your Anthropic API key for LLM
  SERPAPI_API_KEY - Your SerpAPI key for Google search
        """
    )

    parser.add_argument('--target', type=int, default=100,
                       help='Target number of valid trees to generate (default: 100)')
    parser.add_argument('--max-depth', type=int, default=3,
                       help='Maximum crawl depth (default: 3)')
    parser.add_argument('--max-children', type=int, default=10,
                       help='Maximum children per node (default: 10)')
    parser.add_argument('--crawl-delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--min-tree-depth', type=int, default=2,
                       help='Minimum tree depth for validation (default: 3)')
    parser.add_argument('--min-tree-width', type=int, default=2,
                       help='Minimum tree width for validation (default: 3)')
    parser.add_argument('--trends-file', default='data/trends.json',
                       help='Path to trends JSON file (default: data/trends.json)')
    parser.add_argument('--dataset-dir', default='data/dataset',
                       help='Directory to save dataset (default: data/dataset)')
    parser.add_argument('--max-attempts-per-tree', type=int, default=3,
                       help='Maximum attempts to generate a valid tree before giving up (default: 3)')
    parser.add_argument('--anthropic-model', default='claude-haiku-4-5',
                       help='Anthropic model to use (default: claude-haiku-4-5)')
    parser.add_argument('--no-random-sampling', action='store_true',
                       help='Disable random link sampling (take links in order)')
    parser.add_argument('--save-steps', type=int, default=3,
                       help='Save dataset metadata every N successful trees (default: 3)')
    parser.add_argument('--max-api-failures', type=int, default=3,
                       help='Maximum consecutive API failures before stopping (default: 3)')

    args = parser.parse_args()

    # Initialize components
    print("Initializing components...")
    try:
        trends_parser = TrendsParser(args.trends_file)
        print(f"✓ Trends parser loaded ({trends_parser.count_subtopics()} subtopics)")

        llm_agent = LLMAgent(model=args.anthropic_model)
        print(f"✓ LLM agent initialized (model: {args.anthropic_model})")

        search_api = SearchAPI()
        print("✓ Search API initialized")

        crawler = WebsiteTreeCrawler(
            filter_meaningful=True,
            allow_all_domains=True,
            random_sampling=not args.no_random_sampling
        )
        sampling_mode = "random" if not args.no_random_sampling else "sequential"
        print(f"✓ Crawler initialized (link sampling: {sampling_mode})")

        validator = TreeValidator()
        print("✓ Validator initialized")

        dataset_manager = DatasetManager(args.dataset_dir)
        print(f"✓ Dataset manager initialized (current: {dataset_manager.get_tree_count()} trees)")

    except Exception as e:
        print(f"\n✗ Error initializing components: {e}")
        print("\nMake sure you have set the required environment variables:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("  export SERPAPI_API_KEY='your-key-here'")
        sys.exit(1)

    # Main generation loop
    print(f"\n{'='*60}")
    print(f"Starting dataset generation")
    print(f"Target: {args.target} valid trees")
    print(f"Current: {dataset_manager.get_tree_count()} trees")
    print(f"{'='*60}\n")

    trees_to_generate = args.target - dataset_manager.get_tree_count()
    if trees_to_generate <= 0:
        print(f"✓ Target already reached! Dataset has {dataset_manager.get_tree_count()} trees.")
        dataset_manager.print_summary()
        sys.exit(0)

    attempt_count = 0
    success_count = 0
    failure_count = 0

    # Track consecutive API failures
    consecutive_llm_failures = 0
    consecutive_search_failures = 0

    start_time = time.time()

    try:
        while success_count < trees_to_generate:
            attempt_count += 1
            current_total = dataset_manager.get_tree_count()

            print(f"\n{'#'*60}")
            print(f"ATTEMPT {attempt_count} | SUCCESS: {success_count}/{trees_to_generate} | TOTAL: {current_total}/{args.target}")
            print(f"{'#'*60}")

            success, result, error_type = generate_single_tree(
                trends_parser=trends_parser,
                llm_agent=llm_agent,
                search_api=search_api,
                crawler=crawler,
                validator=validator,
                max_depth=args.max_depth,
                max_children=args.max_children,
                crawl_delay=args.crawl_delay,
                min_tree_depth=args.min_tree_depth,
                min_tree_width=args.min_tree_width,
                max_search_attempts=args.max_attempts_per_tree
            )

            if success:
                tree, metadata = result
                print("\n[6/6] Saving tree to dataset...")
                tree_id = dataset_manager.add_tree(tree, metadata, auto_save=False)
                print(f"✓ Tree saved as {tree_id}")
                success_count += 1
                failure_count = 0  # Reset failure count on success

                # Reset API failure counters on success
                consecutive_llm_failures = 0
                consecutive_search_failures = 0

                # Save metadata every save_steps trees
                if success_count % args.save_steps == 0:
                    dataset_manager.save()
                    print(f"💾 Checkpoint: Saved metadata ({dataset_manager.get_tree_count()} trees total)")
                    # Also export summary at checkpoints
                    summary_file = f"{args.dataset_dir}/summary.json"
                    dataset_manager.export_summary(summary_file)
                    print(f"📊 Exported summary to {summary_file}")
            else:
                print("\n✗ Failed to generate valid tree")
                failure_count += 1

                # Track API failures
                if error_type == 'llm':
                    consecutive_llm_failures += 1
                    consecutive_search_failures = 0  # Reset other counter
                    print(f"⚠️  LLM failure count: {consecutive_llm_failures}/{args.max_api_failures}")

                    if consecutive_llm_failures >= args.max_api_failures:
                        raise Exception(
                            f"Stopping: {args.max_api_failures} consecutive LLM API failures. "
                            f"Check your ANTHROPIC_API_KEY and API quota."
                        )

                elif error_type == 'search':
                    consecutive_search_failures += 1
                    consecutive_llm_failures = 0  # Reset other counter
                    print(f"⚠️  Search API failure count: {consecutive_search_failures}/{args.max_api_failures}")

                    if consecutive_search_failures >= args.max_api_failures:
                        raise Exception(
                            f"Stopping: {args.max_api_failures} consecutive SerpAPI failures. "
                            f"Check your SERPAPI_API_KEY and API quota."
                        )

                else:
                    # Reset API counters for non-API failures (crawl, validation)
                    consecutive_llm_failures = 0
                    consecutive_search_failures = 0

                # If we have too many consecutive failures, add a longer delay
                if failure_count >= 5:
                    print(f"\n⚠ {failure_count} consecutive failures. Waiting 10 seconds...")
                    time.sleep(10)

            # Add delay between attempts to avoid rate limiting
            if success_count < trees_to_generate:
                time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n⚠ Generation interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    # Final save to ensure all trees are saved
    if success_count > 0:
        dataset_manager.save()
        print(f"\n💾 Final save: Saved metadata ({dataset_manager.get_tree_count()} trees total)")

    # Print final summary
    elapsed_time = time.time() - start_time
    print(f"\n{'='*60}")
    print("GENERATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total attempts: {attempt_count}")
    print(f"Successful trees: {success_count}")
    print(f"Time elapsed: {elapsed_time/60:.1f} minutes")
    print(f"Average time per tree: {elapsed_time/success_count:.1f} seconds" if success_count > 0 else "N/A")

    dataset_manager.print_summary()

    # Export summary
    summary_file = f"{args.dataset_dir}/summary.json"
    dataset_manager.export_summary(summary_file)
    print(f"\n✓ Summary exported to {summary_file}")


if __name__ == '__main__':
    main()
