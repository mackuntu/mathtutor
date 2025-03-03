#!/usr/bin/env python
"""Test script for the BlogManager."""

import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the BlogManager
from src.blog.manager import BlogManager


def main():
    """Test the BlogManager."""
    print("Testing BlogManager...")

    # Create a BlogManager instance
    blog_manager = BlogManager()

    # Get all articles
    articles = blog_manager.get_articles()
    print(f"Found {len(articles)} articles:")

    # Print article details
    for article in articles:
        print(f"- {article['id']}: {article['title']} ({article['published_date']})")
        print(f"  Category: {article['category']}")
        print(f"  Tags: {', '.join(article['tags'])}")
        print(f"  Excerpt: {article['excerpt'][:50]}...")
        print()

    # Get categories
    categories = blog_manager.get_categories()
    print(f"Found {len(categories)} categories: {', '.join(categories)}")

    # Get tags
    tags = blog_manager.get_tags()
    print(f"Found {len(tags)} tags: {', '.join(tags)}")

    # Test getting a specific article
    if articles:
        article_id = articles[0]["id"]
        article = blog_manager.get_article(article_id)
        print(f"\nGetting article {article_id}:")
        print(f"- Title: {article['title']}")
        print(f"- Content length: {len(article['content'])} characters")

        # Test related articles
        related = blog_manager.get_related_articles(article_id)
        print(f"- Related articles: {len(related)}")
        for rel in related:
            print(f"  - {rel['title']}")


if __name__ == "__main__":
    main()
