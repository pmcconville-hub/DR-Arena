# Quick Start Guide - Dataset Generation

Generate 100 website trees automatically using LLM-powered search and crawling.

## 1. Install Dependencies

```bash
cd web_tree
pip install -r requirements.txt
```

Required packages:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `anthropic` - Claude LLM API
- `google-search-results` - SerpAPI client

## 2. Set Up API Keys

Get your API keys:
- **Anthropic**: https://console.anthropic.com/
- **SerpAPI**: https://serpapi.com/ (100 free searches/month)

Set environment variables:

```bash
export ANTHROPIC_API_KEY='your-anthropic-key-here'
export SERPAPI_API_KEY='your-serpapi-key-here'
```

To make them permanent, add to your `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
echo 'export SERPAPI_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

## 3. Test Components (Optional but Recommended)

Verify everything is set up correctly:

```bash
python test_components.py
```

This will test:
- ✓ Trends parser
- ✓ LLM agent (uses ~2 API calls)
- ✓ Search API (uses 1 API credit)
- ✓ Crawler
- ✓ Tree validator
- ✓ Dataset manager

## 4. Generate Dataset

Start generating trees:

```bash
python generate_dataset.py --target 100
```

This will:
1. Sample random topics from `data/trends.json`
2. Use Claude to craft search queries
3. Search Google with SerpAPI
4. Use Claude to select best websites
5. Crawl selected websites
6. Validate trees (min depth=3, min width=2)
7. Save valid trees to `data/dataset/`

### Monitor Progress

The script shows detailed progress:

```
######################################################
ATTEMPT 15 | SUCCESS: 10/100 | TOTAL: 10/100
######################################################

[1/6] Crafting search query with LLM...
✓ Search query: 'jazz music history comprehensive guide'

[2/6] Searching Google...
✓ Found 10 results

[3/6] Selecting best website with LLM...
✓ Selected: https://en.wikipedia.org/wiki/Jazz

[4/6] Crawling website...
✓ Crawl completed

[5/6] Validating tree...
✓ Tree is valid

[6/6] Saving tree to dataset...
✓ Tree saved as tree_0011
```

### Resume Interrupted Runs

If interrupted (Ctrl+C), just run the same command again:

```bash
python generate_dataset.py --target 100
```

It automatically resumes from where it left off.

**Automatic Checkpoints**: The script saves progress every 3 successful trees by default. You can adjust this:

```bash
# Save more frequently (every tree)
python generate_dataset.py --target 100 --save-steps 1

# Save less frequently (every 10 trees)
python generate_dataset.py --target 100 --save-steps 10
```

Look for checkpoint messages:
```
💾 Checkpoint: Saved metadata (6 trees total)
📊 Exported summary to data/dataset/summary.json
```

## 5. View Results

Check the dataset:

```bash
ls -lh data/dataset/trees/  # View individual tree files
cat data/dataset/metadata.json  # View metadata
cat data/dataset/summary.json  # View summary
```

View a tree:

```bash
python visualize.py data/dataset/trees/tree_0001.json
```

## Common Options

```bash
# Generate fewer trees for testing
python generate_dataset.py --target 10

# Deeper crawling
python generate_dataset.py --target 100 --max-depth 4 --max-children 15

# Stricter validation (higher quality trees)
python generate_dataset.py --target 100 --min-tree-depth 4 --min-tree-width 3

# Slower crawling (avoid rate limits)
python generate_dataset.py --target 100 --crawl-delay 2.0

# Sequential link selection instead of random (deterministic trees)
python generate_dataset.py --target 100 --no-random-sampling
```

## Link Sampling

By **default**, the crawler **randomly samples** links from each page for maximum diversity:
- Page with 50 links + `max_children=10` → randomly picks 10 links
- Each run produces different trees (more variety in dataset)

To get **deterministic trees** (same page always gives same tree):
```bash
python generate_dataset.py --target 100 --no-random-sampling
```

## Output Structure

```
data/dataset/
├── metadata.json          # All trees metadata
├── summary.json          # Statistics
└── trees/
    ├── tree_0001.json
    ├── tree_0002.json
    └── ...
```

Each tree file contains:
- URL and domain
- Title and description
- Content text
- Children (nested tree structure)
- Link contexts and relationships

## API Failure Protection

The script automatically stops after 3 consecutive API failures to prevent wasting time:

```
✗ Error crafting search query: API quota exceeded
⚠️  LLM failure count: 3/3

❌ Stopping: 3 consecutive LLM API failures.
   Check your ANTHROPIC_API_KEY and API quota.
```

**What it protects against:**
- Invalid API keys
- Exceeded API quotas
- API service outages

**Configure tolerance:**
```bash
# More tolerant (allow 5 failures)
python generate_dataset.py --target 100 --max-api-failures 5

# Less tolerant (stop immediately)
python generate_dataset.py --target 100 --max-api-failures 1
```

## Troubleshooting

### Missing API Keys

```
✗ Error: Anthropic API key not provided
```

Solution: Set the environment variable:
```bash
export ANTHROPIC_API_KEY='your-key-here'
```

### Search Quota Exceeded

```
✗ Error searching: API quota exceeded
```

Solution: SerpAPI free tier has 100 searches/month. Either:
- Wait until next month
- Upgrade to paid plan ($50/mo for 5,000 searches)
- Generate fewer trees: `--target 50`

### Too Many Invalid Trees

If many trees fail validation:
```bash
# Relax validation criteria
python generate_dataset.py --target 100 --min-tree-depth 2 --min-tree-width 1

# OR increase crawling depth
python generate_dataset.py --target 100 --max-depth 4
```

### Rate Limiting

If you see many failed crawls:
```bash
# Increase delay between requests
python generate_dataset.py --target 100 --crawl-delay 2.0
```

## Cost Estimate

### For 100 Trees:

**SerpAPI:**
- ~150 searches (1.5 attempts per successful tree)
- Free tier: 100 searches → need 50 more searches
- Cost: ~$5 (if exceeding free tier)

**Anthropic (Claude):**
- ~300 LLM calls (2 per attempt × 1.5 attempts per tree)
- ~200K tokens total
- Cost: ~$1-3

**Total: ~$6-8 for 100 trees**

### Time:
- 2-5 hours (depends on website response times and crawl delay)

## Next Steps

After generation:

1. **Analyze dataset:**
   ```python
   from utils.dataset_manager import DatasetManager
   manager = DatasetManager("data/dataset")
   manager.print_summary()
   ```

2. **Visualize individual trees:**
   ```bash
   python visualize.py data/dataset/trees/tree_0001.json
   ```

3. **Process for your research:**
   - Load trees using `WebsiteNode.from_dict()`
   - Extract text content
   - Analyze link structures
   - Train models

## Full Documentation

For more details, see:
- `DATASET_GENERATION.md` - Comprehensive guide
- `README.md` - Original crawler documentation
- `--help` flags on any script

## Support

If you encounter issues:
1. Check `test_components.py` passes
2. Review error messages carefully
3. Check API key quotas
4. Try with smaller `--target` first (e.g., 10 trees)

Happy crawling! 🕷️
