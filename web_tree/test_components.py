#!/usr/bin/env python3
"""
Test script to verify all components are working correctly.

Run this before generating the full dataset to ensure everything is set up properly.
"""

import sys
import os


def test_trends_parser():
    """Test the trends parser"""
    print("\n" + "="*60)
    print("Testing Trends Parser")
    print("="*60)

    try:
        from utils.trends_parser import TrendsParser

        parser = TrendsParser('data/trends.json')
        print(f"✓ Loaded trends.json")
        print(f"✓ Found {parser.count_subtopics()} subtopics")

        # Sample a few
        print("\nSample subtopics:")
        for i in range(3):
            topic, subtopic, cid = parser.sample_random_subtopic()
            print(f"  {i+1}. {topic} > {subtopic} (ID: {cid})")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_llm_agent():
    """Test the LLM agent"""
    print("\n" + "="*60)
    print("Testing LLM Agent")
    print("="*60)

    if not os.getenv('ANTHROPIC_API_KEY'):
        print("✗ ANTHROPIC_API_KEY not set")
        print("  Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return False

    try:
        from utils.llm_agent import LLMAgent

        agent = LLMAgent()
        print("✓ LLM agent initialized")

        # Test query crafting
        print("\nTesting query crafting...")
        query = agent.craft_search_query(
            "Arts & Entertainment > Music & Audio",
            "Jazz"
        )
        print(f"✓ Generated query: '{query}'")

        # Test website selection
        print("\nTesting website selection...")
        mock_results = [
            {
                "title": "Jazz - Wikipedia",
                "link": "https://en.wikipedia.org/wiki/Jazz",
                "snippet": "Jazz is a music genre..."
            },
            {
                "title": "Buy Jazz Music",
                "link": "https://example.com/buy-jazz",
                "snippet": "Shop for jazz albums..."
            }
        ]

        url, reasoning = agent.select_best_website(
            mock_results,
            "Music",
            "Jazz"
        )
        print(f"✓ Selected: {url}")
        print(f"  Reasoning: {reasoning[:100]}...")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_api():
    """Test the search API"""
    print("\n" + "="*60)
    print("Testing Search API")
    print("="*60)

    if not os.getenv('SERPAPI_API_KEY'):
        print("✗ SERPAPI_API_KEY not set")
        print("  Set it with: export SERPAPI_API_KEY='your-key-here'")
        return False

    try:
        from utils.search_api import SearchAPI

        search = SearchAPI()
        print("✓ Search API initialized")

        print("\nTesting search (this will use 1 API credit)...")
        results = search.search("python programming tutorial", num_results=5)

        if results:
            print(f"✓ Found {len(results)} results")
            print(f"  First result: {results[0]['title']}")
            return True
        else:
            print("✗ No results returned")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crawler():
    """Test the crawler on a simple page"""
    print("\n" + "="*60)
    print("Testing Crawler")
    print("="*60)

    try:
        from utils.crawler_utils import WebsiteTreeCrawler

        crawler = WebsiteTreeCrawler(
            filter_meaningful=True,
            allow_all_domains=True
        )
        print("✓ Crawler initialized")

        print("\nTesting crawl on example.com (depth=1, children=3)...")
        tree = crawler.crawl_tree(
            root_url="https://example.com",
            max_depth=1,
            max_children=3,
            delay=0.5
        )

        print(f"✓ Crawled successfully")
        print(f"  Title: {tree.title}")
        print(f"  Children: {len(tree.children)}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validator():
    """Test the tree validator"""
    print("\n" + "="*60)
    print("Testing Tree Validator")
    print("="*60)

    try:
        from utils.tree_validator import TreeValidator
        from models.tree_models import WebsiteNode

        validator = TreeValidator()
        print("✓ Validator initialized")

        # Create a mock tree
        root = WebsiteNode(url="https://example.com", domain="example.com", depth=0, crawled=True)
        child1 = WebsiteNode(url="https://example.com/page1", domain="example.com", depth=1, crawled=True)
        child2 = WebsiteNode(url="https://example.com/page2", domain="example.com", depth=1, crawled=True)
        grandchild = WebsiteNode(url="https://example.com/page1/sub", domain="example.com", depth=2, crawled=True)
        child1.children.append(grandchild)
        root.children.extend([child1, child2])

        print("\nTesting validation on mock tree...")
        is_valid, reason, stats = validator.validate_tree(root, min_depth=2, min_width=2)

        print(f"✓ Validation completed")
        print(f"  Valid: {is_valid}")
        print(f"  Reason: {reason}")
        print(f"  Max depth: {stats['max_depth']}")
        print(f"  Total nodes: {stats['total_nodes']}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dataset_manager():
    """Test the dataset manager"""
    print("\n" + "="*60)
    print("Testing Dataset Manager")
    print("="*60)

    try:
        from utils.dataset_manager import DatasetManager

        manager = DatasetManager("data/test_dataset")
        print("✓ Dataset manager initialized")
        print(f"  Dataset dir: {manager.dataset_dir}")
        print(f"  Current trees: {manager.get_tree_count()}")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# Component Testing Suite")
    print("#"*60)

    results = {
        "Trends Parser": test_trends_parser(),
        "LLM Agent": test_llm_agent(),
        "Search API": test_search_api(),
        "Crawler": test_crawler(),
        "Validator": test_validator(),
        "Dataset Manager": test_dataset_manager()
    }

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    all_passed = True
    for component, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {component}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n✓ All tests passed! You're ready to generate the dataset.")
        print("\nRun: python generate_dataset.py --target 100")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please fix the issues above before proceeding.")
        sys.exit(1)


if __name__ == '__main__':
    main()
