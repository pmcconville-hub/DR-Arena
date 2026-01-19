# main.py
import os
import sys
import glob
import time
from datetime import datetime
script_dir = os.path.dirname(os.path.abspath(__file__))
web_tree_dir = os.path.join(script_dir, 'web_tree')
if not os.path.isdir(web_tree_dir):
    web_tree_dir = os.path.join(os.path.dirname(script_dir), 'web_tree') 
    if not os.path.isdir(web_tree_dir):
        web_tree_dir = os.path.join(script_dir, 'web_tree')
if os.path.isdir(web_tree_dir) and web_tree_dir not in sys.path:
    sys.path.insert(0, web_tree_dir)
try:
    from core.utils import setup_logging
    from core.evolvement_loop import EvolvementLoop
    from utils.io_utils import save_tree_to_json
    from utils.crawler_utils import WebsiteTreeCrawler
    
except ImportError as e:
    print(f"\n[FATAL ERROR] Import failed: {e}")
    print(f"Debug: sys.path[0] is: {sys.path[0]}")
    print("Please ensure the 'web_tree' folder exists and contains 'utils/__init__.py'.\n")
    sys.exit(1)
LOG_DIR = os.path.join(script_dir, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
LOG_FILE = os.path.join(LOG_DIR, f"evolvement_loop_{timestamp}.log")
QUESTIONS_FILE = os.path.join(LOG_DIR, f"evolvement_questions_{timestamp}.jsonl")

if __name__ == "__main__":
    setup_logging(LOG_FILE)
    data_dir = os.path.join(script_dir, 'web_tree', 'data', 'dataset', 'trees')
    if not os.path.exists(data_dir):
         data_dir = os.path.join(script_dir, 'data')
         if not os.path.exists(data_dir):
             os.makedirs(data_dir)
    data_files = glob.glob(os.path.join(data_dir, "*.json"))
    print("\n[1] Start new crawl")
    for i, f in enumerate(data_files):
        print(f"[{i+2}] Load {os.path.basename(f)}")
    try:
        choice_input = input("Select: ").strip()
        if not choice_input:
            raise ValueError("Empty input")
        choice = int(choice_input)
        tree_path = ""
        if choice == 1:
            url = input("Root URL: ").strip()
            if not url.startswith("http"):
                print("Invalid URL. Adding https://...")
                url = "https://" + url
            crawler = WebsiteTreeCrawler(allow_all_domains=True)
            print(f"Crawling {url}...")
            root = crawler.crawl_tree(url, max_depth=2, max_children=4)
            tree_path = os.path.join(data_dir, f"crawl_{int(time.time())}.json")
            save_tree_to_json(root, tree_path)
            print(f"Tree saved to {tree_path}")
        else:
            if choice - 2 < 0 or choice - 2 >= len(data_files):
                raise IndexError("Selection out of range")
            tree_path = data_files[choice-2]
        print(f"Selected Tree: {tree_path}")
        MODEL_A = "" #Choose from AVAILABLE_SEARCH_MODELS
        MODEL_B = "" #Choose from AVAILABLE_SEARCH_MODELS
        print(f"Initializing Arena: {MODEL_A} vs {MODEL_B}...")
        loop = EvolvementLoop(MODEL_A, MODEL_B, tree_path, QUESTIONS_FILE, logger=None)
        loop.start()
    except (ValueError, IndexError) as e:
        print(f"Invalid selection or error: {e}. Exiting.")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")