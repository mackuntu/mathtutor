"""Blog content manager for MathTutor."""

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import frontmatter as python_frontmatter
import markdown
from flask import current_app, has_app_context

logger = logging.getLogger(__name__)


class BlogManager:
    """Manages blog content for the MathTutor application."""

    def __init__(self, content_dir: str = None):
        """Initialize the blog manager.

        Args:
            content_dir: Directory containing blog content files.
                         If None, uses the default content directory.
        """
        self.content_dir = content_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "content",
            "blog",
        )
        self._articles_cache = None
        self._last_cache_update = None
        self._cache_ttl = datetime.timedelta(minutes=5)  # Cache for 5 minutes

    def _should_refresh_cache(self) -> bool:
        """Check if the cache should be refreshed."""
        if self._articles_cache is None or self._last_cache_update is None:
            return True

        return (datetime.datetime.now() - self._last_cache_update) > self._cache_ttl

    def _load_articles(self) -> Dict[str, Dict[str, Any]]:
        """Load all articles from the content directory."""
        if not self._should_refresh_cache():
            return self._articles_cache

        articles = {}
        content_path = Path(self.content_dir)

        logger.info(f"Loading articles from {content_path}")

        if not content_path.exists():
            logger.warning(f"Blog content directory does not exist: {self.content_dir}")
            return articles

        for file_path in content_path.glob("*.md"):
            try:
                article_id = file_path.stem
                logger.info(f"Processing article: {article_id} from {file_path}")

                # Parse frontmatter and content
                with open(file_path, "r", encoding="utf-8") as f:
                    post = python_frontmatter.load(f)

                # Convert publish_date string to datetime if it exists
                if "publish_date" in post.metadata:
                    try:
                        publish_date_str = post.metadata["publish_date"]
                        if isinstance(publish_date_str, str):
                            publish_date = datetime.datetime.fromisoformat(
                                publish_date_str
                            )
                            # Only include if publish date is in the past
                            if publish_date > datetime.datetime.now():
                                debug_mode = False
                                if has_app_context():
                                    try:
                                        debug_mode = current_app.config.get(
                                            "DEBUG", False
                                        )
                                    except RuntimeError:
                                        pass

                                if debug_mode:
                                    logger.info(
                                        f"Skipping future article: {article_id} (publishes on {publish_date})"
                                    )
                                else:
                                    logger.info(
                                        f"Skipping future article: {article_id} (publishes on {publish_date})"
                                    )
                                continue
                        else:
                            logger.warning(
                                f"Invalid publish_date format in {file_path}: not a string"
                            )
                    except ValueError as e:
                        logger.warning(
                            f"Invalid publish_date format in {file_path}: {str(e)}"
                        )

                # Convert markdown content to HTML
                html_content = markdown.markdown(
                    post.content,
                    extensions=[
                        "markdown.extensions.extra",
                        "markdown.extensions.codehilite",
                        "markdown.extensions.smarty",
                    ],
                )

                # Create article object
                article = {
                    "id": article_id,
                    "title": post.metadata.get("title", "Untitled"),
                    "published_date": post.metadata.get(
                        "published_date", "Unknown date"
                    ),
                    "category": post.metadata.get("category", "Uncategorized"),
                    "image_url": post.metadata.get(
                        "image_url", "https://placehold.co/800x400"
                    ),
                    "image_alt": post.metadata.get("image_alt", "Article image"),
                    "meta_description": post.metadata.get("meta_description", ""),
                    "meta_keywords": post.metadata.get("meta_keywords", ""),
                    "tags": post.metadata.get("tags", []),
                    "content": html_content,
                    "excerpt": post.metadata.get("excerpt", ""),
                    "author": post.metadata.get("author", "MathTutor Team"),
                    "publish_date": post.metadata.get("publish_date", None),
                }

                articles[article_id] = article
                logger.info(f"Added article: {article_id}")

            except Exception as e:
                logger.error(f"Error loading article {file_path}: {str(e)}")

        logger.info(f"Loaded {len(articles)} articles")
        self._articles_cache = articles
        self._last_cache_update = datetime.datetime.now()

        return articles

    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific article by ID.

        Args:
            article_id: The ID of the article to retrieve.

        Returns:
            The article data or None if not found.
        """
        articles = self._load_articles()
        return articles.get(article_id)

    def get_articles(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        limit: Optional[int] = None,
        sort_by: str = "publish_date",
        sort_order: str = "desc",
    ) -> List[Dict[str, Any]]:
        """Get a list of articles, optionally filtered by category or tag.

        Args:
            category: Filter articles by category.
            tag: Filter articles by tag.
            limit: Maximum number of articles to return.
            sort_by: Field to sort by.
            sort_order: Sort order ('asc' or 'desc').

        Returns:
            List of article data.
        """
        articles = self._load_articles()

        # Filter by category if specified
        if category:
            articles = {
                k: v
                for k, v in articles.items()
                if v.get("category", "").lower() == category.lower()
            }

        # Filter by tag if specified
        if tag:
            articles = {
                k: v
                for k, v in articles.items()
                if tag.lower() in [t.lower() for t in v.get("tags", [])]
            }

        # Convert to list for sorting
        article_list = list(articles.values())

        # Sort articles
        reverse = sort_order.lower() == "desc"
        article_list.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)

        # Apply limit if specified
        if limit and limit > 0:
            article_list = article_list[:limit]

        return article_list

    def get_categories(self) -> List[str]:
        """Get a list of all categories used in articles.

        Returns:
            List of category names.
        """
        articles = self._load_articles()
        categories = set(
            article.get("category", "Uncategorized") for article in articles.values()
        )
        return sorted(list(categories))

    def get_tags(self) -> List[str]:
        """Get a list of all tags used in articles.

        Returns:
            List of tag names.
        """
        articles = self._load_articles()
        tags = set()
        for article in articles.values():
            for tag in article.get("tags", []):
                tags.add(tag)
        return sorted(list(tags))

    def get_related_articles(
        self, article_id: str, limit: int = 2
    ) -> List[Dict[str, Any]]:
        """Get articles related to the specified article.

        Args:
            article_id: The ID of the reference article.
            limit: Maximum number of related articles to return.

        Returns:
            List of related article data.
        """
        articles = self._load_articles()
        article = articles.get(article_id)

        if not article:
            return []

        # Get articles in the same category
        same_category = [
            a
            for aid, a in articles.items()
            if aid != article_id and a.get("category") == article.get("category")
        ]

        # Get articles with common tags
        article_tags = set(article.get("tags", []))
        related_by_tag = []

        for aid, a in articles.items():
            if aid != article_id and aid not in [sc["id"] for sc in same_category]:
                common_tags = article_tags.intersection(set(a.get("tags", [])))
                if common_tags:
                    a["common_tag_count"] = len(common_tags)
                    related_by_tag.append(a)

        # Sort related by tag by number of common tags
        related_by_tag.sort(key=lambda x: x.get("common_tag_count", 0), reverse=True)

        # Combine and limit results
        related = same_category + related_by_tag
        return related[:limit]
