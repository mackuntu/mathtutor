"""Static page routes for the MathTutor application."""

import logging

from flask import Blueprint, redirect, render_template, request, url_for

from ..blog.manager import BlogManager
from ..database import get_repository
from ..database.models import Subscription
from ..generator import ProblemGenerator
from .common import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Initialize components
repository = get_repository()
generator = ProblemGenerator()
blog_manager = BlogManager()  # Initialize blog manager at module level

# Create blueprint
bp = Blueprint("pages", __name__, url_prefix="")


@bp.route("/")
def index():
    """Render index page."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    # Get user's children
    children = repository.get_children_by_parent(user.email)

    # Get user's subscription
    subscription = repository.get_user_subscription(user.email)
    if not subscription:
        subscription = Subscription(user_email=user.email)
        repository.create_subscription(subscription)

    active_child_id = request.args.get("child_id")
    active_child = None

    if active_child_id:
        active_child = repository.get_child_by_id(active_child_id)
    elif children:
        active_child = children[0]

    return render_template(
        "index.html",
        user=user,
        children=children,
        active_child=active_child,
        ages=list(range(6, 10)),  # Ages 6-9
        default_age=active_child.age if active_child else None,
        default_difficulty=generator.get_school_year_progress(),
        subscription=subscription,
        can_generate=subscription.can_generate_worksheet(),
        remaining_worksheets=subscription.worksheets_limit
        - subscription.worksheets_generated,
        is_premium=subscription.plan == Subscription.PLAN_PREMIUM,
    )


@bp.route("/terms")
def terms():
    """Render Terms of Service page."""
    user = get_current_user()
    return render_template("terms.html", user=user)


@bp.route("/privacy")
def privacy():
    """Render Privacy Policy page."""
    user = get_current_user()
    return render_template("privacy.html", user=user)


@bp.route("/blog")
def blog():
    """Render Blog page with educational math content."""
    user = get_current_user()
    category = request.args.get("category")
    tag = request.args.get("tag")

    logger.info(f"Blog page requested with category={category}, tag={tag}")

    articles = blog_manager.get_articles(category=category, tag=tag)
    categories = blog_manager.get_categories()
    tags = blog_manager.get_tags()

    logger.info(
        f"Found {len(articles)} articles, {len(categories)} categories, {len(tags)} tags"
    )

    return render_template(
        "blog.html",
        user=user,
        articles=articles,
        categories=categories,
        tags=tags,
        active_category=category,
        active_tag=tag,
    )


@bp.route("/blog/article/<article_id>")
def blog_article(article_id):
    """Render individual blog article page."""
    user = get_current_user()

    logger.info(f"Blog article requested: {article_id}")

    article = blog_manager.get_article(article_id)
    if not article:
        logger.warning(f"Article not found: {article_id}")
        return render_template("404.html", user=user), 404

    logger.info(f"Found article: {article_id} - {article.get('title')}")

    related_articles = blog_manager.get_related_articles(article_id)
    categories = blog_manager.get_categories()

    return render_template(
        "blog_article.html",
        user=user,
        article=article,
        related_articles=related_articles,
        categories=categories,
    )
