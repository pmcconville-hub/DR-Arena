# Website Tree Crawler

## Project Structure

```
web_tree/
├── models/                 # Data models
│   ├── __init__.py
│   └── tree_models.py     # LinkContext and WebsiteNode classes
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── crawler_utils.py   # Web crawling functionality
│   ├── visualization_utils.py  # Tree visualization functions
│   └── io_utils.py        # JSON save/load utilities
├── examples/               # Example scripts
│   └── example_usage.py   # Programmatic usage examples
├── data/                   # Data directory (JSON files, CSV files)
│   └── coffee_tree.json   # Example crawled tree
├── crawl.py               # Main crawler entry point
├── visualize.py           # Main visualization entry point
├── expand_tree.py         # Tree expansion tool (add width/depth)
└── README.md              # This file
```

## Installation

### Prerequisites

- Python 3.8+
- Required packages:

```bash
pip install requests beautifulsoup4
```


## Quick Start

### 1. Crawl a Website

```bash
# Basic usage
python crawl.py https://coffeeblog.co.uk/types-of-coffee-difference-between-them/ --output data/coffee_tree.json
```

### 2. Visualize the Tree

```bash
# Interactive menu (default)
python visualize.py data/coffee_tree.json
# Direct visualization styles (recommended setting: clustered)
python visualize.py data/coffee_tree.json --style compact
python visualize.py data/coffee_tree.json --style clustered
python visualize.py data/coffee_tree.json --style stats
```

### 3. Expand an Existing Tree

```bash
# List nodes with expandability analysis (recommended!)
python expand_tree.py data/coffee_tree.json --list-nodes --show-expandability

# Expand width - add more children (siblings) to a node
python expand_tree.py data/coffee_tree.json \
  --url "https://coffeeblog.co.uk/ristretto-vs-espresso-vs-lungo/" \
  --width 5 \
  --output data/wider_tree.json

# Expand depth - make tree deeper from a node
python expand_tree.py data/coffee_tree.json \
  --url "https://coffeeblog.co.uk/ristretto-vs-espresso-vs-lungo/" \
  --depth 2 \
  --max-children 3 \
  --output data/deeper_tree.json \
  --visualize
```

### 4. Programmatic Usage

```python
from utils.crawler_utils import WebsiteTreeCrawler
from utils.io_utils import save_tree_to_json, load_tree_from_json
from utils.visualization_utils import print_tree_clustered

# Initialize crawler
crawler = WebsiteTreeCrawler(allow_all_domains=True)

# Crawl website
root = crawler.crawl_tree(
    root_url="https://example.com",
    max_depth=2,
    max_children=10
)

# Save to JSON
save_tree_to_json(root, "my_tree.json")

# Load and visualize
loaded_root = load_tree_from_json("my_tree.json")
print_tree_clustered(loaded_root)
```

## Command-Line Reference

### crawl.py

Crawl websites and build tree structures.

```bash
python crawl.py <url> [options]

Options:
  --max-depth N          Maximum crawl depth (default: 2)
  --max-children N       Maximum children per node (default: 10)
  --delay SECONDS        Delay between requests (default: 1.0)
  --output FILE          Output JSON file (default: data/website_tree.json)
  --no-filter            Disable meaningful link filtering
  --no-allow-all         Restrict to top N domains from MOZ CSV
  --moz-csv FILE         Path to MOZ domains CSV
  --top-n N              Number of top domains to allow (default: 100)
```

### visualize.py

Visualize website tree structures from JSON files.

```bash
python visualize.py [json_file] [options]

Styles:
  --style compact        Minimal tree view
  --style summary        Basic info tree view
  --style detailed       Full information tree view
  --style stats          Tree with statistics
  --style depth          Organized by depth levels
  --style clustered      Grouped by relationship types
  --style interactive    Interactive menu (default)

Options:
  --max-depth N          Maximum depth to display
  --show-content         Show page content
  --max-content-chars N  Max content characters (default: 200)
```

### expand_tree.py

Expand existing trees by adding more width (siblings) or depth (children).

```bash
python expand_tree.py <input_file> [options]

Options:
  --url URL              URL of node to expand
  --width N              Expand width: add N additional children
  --depth N              Expand depth: add N additional depth levels
  --max-children N       Max children per node when expanding depth (default: 10)
  --delay SECONDS        Delay between requests (default: 1.0)
  --output FILE, -o      Output JSON file (default: overwrite input)
  --list-nodes           List all nodes in the tree and exit
  --max-list-depth N     Maximum depth to display when listing nodes
  --show-expandability   Show expansion capabilities when listing nodes
  --preview              Preview the expanded tree before saving
  --visualize            Visualize the expanded tree with new nodes highlighted

Expandability Analysis (--show-expandability):
  When listing nodes with --show-expandability, each node shows:
  - 🟢 Expandable: Can expand via width and/or depth
  - 🟡 Partial: Can expand width first, then depth
  - 🔴 Not expandable: Leaf node with no links
  - Details: "Width: ✓ N available" or "Depth: ✓ N/M children have links"

Visualization (--visualize):
  When using --visualize, newly added nodes are marked with:
  - *** surrounding the node name ***
  - 🆕 NEW indicator
  - Cluster headers show "(N new)" count
  - Summary of all new URLs at the end
```

## Semantic Relationship Categories

The crawler automatically categorizes links into semantic relationships:

- **origins/locations**: Geographic origins and locations
- **types/varieties**: Different types, varieties, or categories
- **processes/methods**: Methods, techniques, and processes
- **products/drinks**: Related products and beverages
- **components/ingredients**: Parts, ingredients, and chemical components
- **history/timeline**: Historical information and timeline
- **people/organizations**: People, companies, and organizations
- **health/effects**: Health effects, benefits, and risks
- **culture/economics**: Cultural practices and economic aspects
- **equipment/tools**: Equipment, tools, and machinery
- **related topics**: General related topics

## Visualization Styles

### 1. Compact View
Minimal information, great for quick overview:
```
└─ [✓] example.com - Page Title
   ├─ [✓] subdomain.example.com - Another Page
   └─ [✓] other.com - External Link
```

### 2. Clustered View
Groups children by semantic relationship:
```
└── [✓] coffee-site.com
    ├─ 🏷️  types/varieties (3)
    │   ├── Arabica Coffee
    │   ├── Robusta Coffee
    │   └── Liberica Coffee
    └─ 🏷️  processes/methods (2)
        ├── Roasting
        └── Brewing
```

### 3. Statistical View
Shows comprehensive statistics:
```
Total Nodes:       42
Crawled Success:   38
Failed Crawls:     4
Total Links Found: 156
Max Depth:         2
Unique Domains:    15
```

### 4. Depth View
Organizes nodes by depth level:
```
────────────────────────────────────────────────
DEPTH 0 (1 nodes)
────────────────────────────────────────────────
  [1] [✓] example.com
      Title: Example Website
      Stats: 10 children, 25 links found

────────────────────────────────────────────────
DEPTH 1 (10 nodes)
────────────────────────────────────────────────
  [1] [✓] subdomain.example.com
      ...
```

## API Reference

### Classes

#### `WebsiteNode`
Represents a node in the website tree.

**Attributes:**
- `url`: The webpage URL
- `domain`: Domain name
- `title`: Page title
- `description`: Meta description
- `content`: Cleaned text content
- `crawled`: Whether successfully crawled
- `depth`: Depth in tree (0 = root)
- `children`: List of child nodes
- `link_contexts`: List of link contexts found on page
- `error`: Error message if crawl failed

#### `LinkContext`
Context information around a hyperlink.

**Attributes:**
- `url`: Link URL
- `anchor_text`: Link text
- `surrounding_text`: Text context around link
- `relationship`: Semantic relationship category

#### `WebsiteTreeCrawler`
Main crawler class.

**Methods:**
- `crawl_tree(root_url, max_depth, max_children, delay)`: Crawl and build tree

### Utility Functions

**I/O:**
- `save_tree_to_json(node, file_path)`: Save tree to JSON
- `load_tree_from_json(file_path)`: Load tree from JSON

**Visualization:**
- `print_tree_compact(node)`: Print compact view
- `print_tree_summary(node)`: Print summary view
- `print_tree_detailed(node, ...)`: Print detailed view
- `print_tree_clustered(node, ...)`: Print clustered view
- `print_tree_with_stats(node)`: Print with statistics
- `print_tree_by_depth(node, max_depth)`: Print organized by depth
- `print_clusters_summary(node)`: Print relationship distribution
- `print_tree_interactive_menu(node)`: Interactive visualization menu


## Advanced Usage

### Batch Processing

```python
from utils.crawler_utils import WebsiteTreeCrawler
from utils.io_utils import save_tree_to_json

urls = [
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
]

crawler = WebsiteTreeCrawler()

for i, url in enumerate(urls):
    print(f"Crawling {url}...")
    root = crawler.crawl_tree(url, max_depth=2, max_children=5)
    save_tree_to_json(root, f"data/tree_{i}.json")
```
