"""
Web crawler utilities for building website trees.
"""

import csv
import random
import re
import sys
import time
from urllib.parse import urljoin, urlparse
from typing import List, Set, Optional, Tuple

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages not installed.")
    print("Please install them using: pip install requests beautifulsoup4")
    sys.exit(1)

from models.tree_models import LinkContext, WebsiteNode


class WebsiteTreeCrawler:
    """Crawls websites and builds a tree structure"""

    def __init__(self, moz_csv_path='data/moz_websites.csv', top_n=100,
                 filter_meaningful=True, allow_all_domains=True, random_sampling=True):
        """
        Initialize the crawler.

        Args:
            moz_csv_path: Path to MOZ top domains CSV file
            top_n: Number of top domains to allow (if not allow_all_domains)
            filter_meaningful: Whether to filter out navigational links
            allow_all_domains: Whether to allow crawling any domain
            random_sampling: Whether to randomly sample links (default: True)
        """
        self.allow_all_domains = allow_all_domains
        self.top_domains = self._load_top_domains(moz_csv_path, top_n) if not allow_all_domains else set()
        self.visited_urls: Set[str] = set()
        self.filter_meaningful = filter_meaningful
        self.random_sampling = random_sampling
        self.session = requests.Session()
        # Complete browser-like headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def _load_top_domains(self, csv_path: str, top_n: int) -> Set[str]:
        """Load top N domains from moz_websites.csv"""
        domains = set()
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= top_n:
                        break
                    domain = row['Root Domain'].strip()
                    domain = domain.replace('www.', '')
                    domains.add(domain)
            print(f"Loaded {len(domains)} top domains from {csv_path}")
        except Exception as e:
            print(f"Error loading domains: {e}")
            sys.exit(1)
        return domains

    def _is_allowed_domain(self, url: str) -> bool:
        """Check if URL's domain is in the allowed top domains"""
        if self.allow_all_domains:
            return True
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            domain = domain.replace('www.', '')
            domain = domain.split(':')[0]
            return domain in self.top_domains
        except:
            return False

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragment (anchor) portion"""
        try:
            parsed = urlparse(url)
            normalized = parsed._replace(fragment='').geturl()
            return normalized
        except:
            return url

    def _get_context_around_link(self, link_tag, context_chars=100) -> str:
        """Extract text context around a link"""
        try:
            parent = link_tag.parent
            if parent:
                text = parent.get_text(strip=True)
                link_text = link_tag.get_text(strip=True)
                idx = text.find(link_text)
                if idx != -1:
                    start = max(0, idx - context_chars)
                    end = min(len(text), idx + len(link_text) + context_chars)
                    return text[start:end]
                return text[:context_chars * 2]
            return ""
        except:
            return ""

    def _infer_relationship(self, anchor_text: str, context: str, 
                           parent_title: Optional[str] = None) -> str:
        """Infer the semantic relationship type based on anchor text and context"""
        anchor_lower = anchor_text.lower()
        context_lower = context.lower()
        combined = f"{anchor_lower} {context_lower}"

        # Define relationship indicators
        relationships = {
            "origins/locations": [
                'country', 'region', 'origin', 'from', 'grown in', 'produced in',
                'colombian', 'brazilian', 'ethiopian', 'kenyan', 'yunnan', 'sumatra',
                'africa', 'asia', 'america', 'continent', 'colombia', 'brazil', 
                'ethiopia', 'kenya', 'yemen', 'vietnam', 'indonesia', 'java'
            ],
            "types/varieties": [
                'type', 'variety', 'species', 'kind', 'form', 'class', 'category',
                'arabica', 'robusta', 'liberica', 'typica', 'bourbon',
                'different', 'various', 'several'
            ],
            "processes/methods": [
                'process', 'method', 'technique', 'how to', 'way', 'procedure',
                'roasting', 'brewing', 'grinding', 'ferment', 'dry', 'wet',
                'preparation', 'making', 'processing', 'production'
            ],
            "products/drinks": [
                'drink', 'beverage', 'product', 'serve', 'espresso', 'cappuccino',
                'latte', 'americano', 'macchiato', 'mocha', 'frappe'
            ],
            "components/ingredients": [
                'contains', 'ingredient', 'chemical', 'compound', 'element',
                'caffeine', 'acid', 'oil', 'antioxidant', 'flavor', 'aroma',
                'composition', 'molecule'
            ],
            "history/timeline": [
                'history', 'origin', 'ancient', 'traditional', 'first', 'discover',
                'century', 'year', 'era', 'period', 'historical', 'originally',
                'began', 'started'
            ],
            "people/organizations": [
                'company', 'brand', 'founder', 'person', 'grower', 'farmer',
                'organization', 'association', 'expert', 'barista'
            ],
            "health/effects": [
                'health', 'benefit', 'effect', 'impact', 'risk', 'study',
                'research', 'disease', 'medical', 'nutrition'
            ],
            "culture/economics": [
                'culture', 'social', 'ritual', 'ceremony', 'tradition',
                'economy', 'trade', 'market', 'price', 'industry', 'business'
            ],
            "equipment/tools": [
                'machine', 'equipment', 'tool', 'grinder', 'maker', 'pot',
                'filter', 'press', 'device'
            ]
        }

        # Check each relationship category
        for relationship, indicators in relationships.items():
            if any(ind in combined for ind in indicators):
                return relationship

        return "related topics"

    def _crawl_page(self, url: str, timeout=10) -> Tuple[Optional[BeautifulSoup], Optional[str]]:
        """Crawl a single page and return BeautifulSoup object"""
        try:
            response = self.session.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type.lower():
                return None, "Non-HTML content"

            soup = BeautifulSoup(response.content, 'html.parser')
            return soup, None
        except requests.Timeout:
            return None, "Timeout"
        except requests.RequestException as e:
            return None, f"Request error: {str(e)[:100]}"
        except Exception as e:
            return None, f"Parse error: {str(e)[:100]}"

    def _extract_metadata(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """Extract title and description from page"""
        title = None
        description = None

        try:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)

            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                description = desc_tag.get('content', '').strip()
            elif soup.find('meta', attrs={'property': 'og:description'}):
                description = soup.find('meta', attrs={'property': 'og:description'}).get('content', '').strip()
        except:
            pass

        return title, description

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract and clean main text content from the page"""
        try:
            soup_copy = BeautifulSoup(str(soup), 'html.parser')

            # Remove unwanted elements
            unwanted_tags = [
                'script', 'style', 'noscript', 'iframe', 'embed',
                'nav', 'header', 'footer', 'aside', 'form',
                'button', 'input', 'select', 'textarea'
            ]

            for tag in unwanted_tags:
                for element in soup_copy.find_all(tag):
                    element.decompose()

            # Remove elements by class/id patterns
            unwanted_patterns = [
                'nav', 'menu', 'sidebar', 'footer', 'header',
                'advertisement', 'ad-', 'social', 'share',
                'comment', 'related', 'recommended',
                'cookie', 'banner', 'popup', 'modal'
            ]

            for pattern in unwanted_patterns:
                for element in soup_copy.find_all(class_=lambda x: x and pattern in x.lower()):
                    element.decompose()
                for element in soup_copy.find_all(id=lambda x: x and pattern in x.lower()):
                    element.decompose()

            # Try to find main content area
            main_content = None
            main_patterns = [
                ('main', {}),
                ('article', {}),
                ('div', {'class': lambda x: x and any(term in x.lower() for term in ['content', 'main', 'article', 'body', 'post'])}),
                ('div', {'id': lambda x: x and any(term in x.lower() for term in ['content', 'main', 'article', 'body', 'post'])})
            ]

            for tag, attrs in main_patterns:
                element = soup_copy.find(tag, attrs)
                if element:
                    main_content = element
                    break

            if not main_content:
                main_content = soup_copy.find('body')

            if not main_content:
                main_content = soup_copy

            text = main_content.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)

            if len(text) < 50:
                return None

            return text

        except Exception as e:
            print(f"Error extracting content: {e}")
            return None

    def _is_meaningful_link(self, link_ctx: LinkContext, parent_title: Optional[str] = None) -> bool:
        """Determine if a link is meaningful (filters out navigational/boilerplate links)"""
        anchor = link_ctx.anchor_text.lower()
        context = link_ctx.surrounding_text.lower()
        url = link_ctx.url.lower()

        if not anchor or len(anchor) < 2:
            return False

        # Navigational terms to skip
        navigational_terms = {
            'home', 'homepage', 'main page', 'back', 'top', 'menu', 'navigation',
            'login', 'log in', 'sign in', 'sign up', 'register', 'subscribe',
            'share', 'tweet', 'facebook', 'email', 'print', 'download',
            'click here', 'read more', 'more', 'see more', 'learn more',
            'here', 'this', 'next', 'previous', 'prev', 'continue',
            'help', 'about', 'about us', 'contact', 'privacy', 'terms',
            'comments', 'discussion', 'talk', 'forum',
            'pdf', 'xml', 'rss', 'atom', 'feed'
        }

        if anchor in navigational_terms:
            return False

        if anchor.isdigit() or len(anchor) == 1:
            return False

        if anchor.startswith('[') and anchor.endswith(']'):
            return False

        # Skip URL patterns
        skip_url_patterns = [
            'login', 'signin', 'signup', 'register', 'subscribe',
            'special:', 'talk:', 'user:', 'action=edit', 'action=history'
        ]

        for pattern in skip_url_patterns:
            if pattern in url:
                return False

        # Check for meaningful context
        if context:
            context_without_anchor = context.replace(anchor, '').strip()
            if len(context_without_anchor) < 20:
                return False

        # Anchor text quality
        word_count = len(anchor.split())
        if word_count == 1 and len(anchor) <= 4:
            return False
        if word_count > 8:
            return False

        if link_ctx.anchor_text and link_ctx.anchor_text[0].isupper():
            return True

        return True

    def _extract_links(self, soup: BeautifulSoup, base_url: str, 
                      parent_title: Optional[str] = None) -> List[LinkContext]:
        """Extract meaningful links from page with context"""
        links = []
        normalized_base = self._normalize_url(base_url)

        try:
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                absolute_url = urljoin(base_url, href)

                if not absolute_url.startswith(('http://', 'https://')):
                    continue

                normalized_url = self._normalize_url(absolute_url)

                if normalized_url == normalized_base:
                    continue

                if not self._is_allowed_domain(normalized_url):
                    continue

                anchor_text = link_tag.get_text(strip=True)
                context = self._get_context_around_link(link_tag)
                relationship = self._infer_relationship(anchor_text, context, parent_title)

                link_ctx = LinkContext(
                    url=normalized_url,
                    anchor_text=anchor_text,
                    surrounding_text=context,
                    relationship=relationship
                )

                if not self.filter_meaningful or self._is_meaningful_link(link_ctx, parent_title):
                    links.append(link_ctx)

        except Exception as e:
            print(f"Error extracting links: {e}")

        return links

    def crawl_tree(self, root_url: str, max_depth: int = 2, max_children: int = 10,
                   delay: float = 1.0) -> WebsiteNode:
        """
        Crawl websites starting from root_url and build a tree.

        Args:
            root_url: Starting URL
            max_depth: Maximum depth to crawl (0 = only root)
            max_children: Maximum number of child nodes per parent
            delay: Delay between requests in seconds

        Returns:
            Root WebsiteNode with children populated
        """
        normalized_root_url = self._normalize_url(root_url)

        root_node = WebsiteNode(
            url=normalized_root_url,
            domain=self._extract_domain(normalized_root_url),
            depth=0
        )

        self._crawl_node(root_node, max_depth, max_children, delay)
        return root_node

    def _crawl_node(self, node: WebsiteNode, max_depth: int, max_children: int, delay: float):
        """Recursively crawl a node and its children"""
        if node.url in self.visited_urls:
            node.error = "Already visited"
            node.crawled = False
            print(f"{'  ' * node.depth}Skipping already visited: {node.url}")
            return

        self.visited_urls.add(node.url)
        print(f"{'  ' * node.depth}Crawling [{node.depth}]: {node.url}")

        soup, error = self._crawl_page(node.url)

        if error or soup is None:
            node.error = error or "Unknown error"
            node.crawled = False
            print(f"{'  ' * node.depth}  Error: {node.error}")
            return

        node.title, node.description = self._extract_metadata(soup)
        node.crawled = True
        node.content = self._extract_content(soup)

        print(f"{'  ' * node.depth}  Title: {node.title}")
        if node.content:
            content_preview = node.content[:100] + "..." if len(node.content) > 100 else node.content
            print(f"{'  ' * node.depth}  Content: {len(node.content)} chars - {content_preview}")

        if node.depth >= max_depth:
            print(f"{'  ' * node.depth}  Max depth reached")
            return

        link_contexts = self._extract_links(soup, node.url, node.title)
        node.link_contexts = link_contexts

        print(f"{'  ' * node.depth}  Found {len(link_contexts)} meaningful links")

        # Create child nodes - filter out already visited URLs first
        available_links = [
            link_ctx for link_ctx in link_contexts
            if link_ctx.url not in self.visited_urls
        ]

        # Sample links randomly or take in order
        if self.random_sampling and len(available_links) > max_children:
            selected_links = random.sample(available_links, max_children)
            print(f"{'  ' * node.depth}  Randomly sampled {len(selected_links)} from {len(available_links)} links")
        else:
            selected_links = available_links[:max_children]
            if self.random_sampling:
                print(f"{'  ' * node.depth}  Using all {len(selected_links)} available links")
            else:
                print(f"{'  ' * node.depth}  Taking first {len(selected_links)} links in order")

        print(f"{'  ' * node.depth}  Creating {len(selected_links)} child nodes")

        # Crawl children
        for i, link_ctx in enumerate(selected_links):
            if i > 0:
                time.sleep(delay)

            child_node = WebsiteNode(
                url=link_ctx.url,
                domain=self._extract_domain(link_ctx.url),
                depth=node.depth + 1,
                relationship_cluster=link_ctx.relationship
            )
            node.children.append(child_node)
            self._crawl_node(child_node, max_depth, max_children, delay)
