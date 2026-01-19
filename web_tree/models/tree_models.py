"""
Data models for website tree structure.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class LinkContext:
    """Context information around a hyperlink"""
    url: str
    anchor_text: str
    surrounding_text: str
    relationship: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> 'LinkContext':
        """Create LinkContext from dictionary"""
        return LinkContext(
            url=data['url'],
            anchor_text=data['anchor_text'],
            surrounding_text=data['surrounding_text'],
            relationship=data.get('relationship')
        )

    def to_dict(self) -> dict:
        """Convert LinkContext to dictionary"""
        return {
            'url': self.url,
            'anchor_text': self.anchor_text,
            'surrounding_text': self.surrounding_text,
            'relationship': self.relationship
        }


@dataclass
class WebsiteNode:
    """Node in the website tree"""
    url: str
    domain: str
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    crawled: bool = False
    depth: int = 0
    children: List['WebsiteNode'] = field(default_factory=list)
    link_contexts: List[LinkContext] = field(default_factory=list)
    error: Optional[str] = None
    relationship_cluster: Optional[str] = None

    @staticmethod
    def from_dict(data: dict) -> 'WebsiteNode':
        """Load WebsiteNode from dictionary"""
        node = WebsiteNode(
            url=data['url'],
            domain=data['domain'],
            title=data.get('title'),
            description=data.get('description'),
            content=data.get('content'),
            crawled=data.get('crawled', False),
            depth=data.get('depth', 0),
            error=data.get('error'),
            relationship_cluster=data.get('relationship_cluster')
        )

        # Load link contexts
        if 'link_contexts' in data:
            node.link_contexts = [LinkContext.from_dict(ctx) for ctx in data['link_contexts']]

        # Load children recursively
        if 'children' in data:
            node.children = [WebsiteNode.from_dict(child) for child in data['children']]

        return node

    def to_dict(self) -> dict:
        """Convert WebsiteNode to dictionary"""
        return {
            'url': self.url,
            'domain': self.domain,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'crawled': self.crawled,
            'depth': self.depth,
            'error': self.error,
            'relationship_cluster': self.relationship_cluster,
            'link_contexts': [ctx.to_dict() for ctx in self.link_contexts],
            'children': [child.to_dict() for child in self.children]
        }
