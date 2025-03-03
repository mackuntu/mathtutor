"""Admin routes for the MathTutor application."""

import logging
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..database import get_repository
from ..database.models import Payment, Subscription, User
from .common import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Initialize components
repository = get_repository()

# Create blueprint
bp = Blueprint("admin", __name__, url_prefix="/admin")

# List of admin emails
ADMIN_EMAILS = [
    "admin@mathtutor.com",
    "mackuntu@gmail.com",
]  # Replace with actual admin emails


def is_admin(user):
    """Check if user is an admin."""
    return user and user.email in ADMIN_EMAILS


@bp.before_request
def check_admin():
    """Check if user is an admin before processing any admin route."""
    user = get_current_user()
    if not is_admin(user):
        flash("Access denied. You must be an administrator to view this page.", "error")
        return redirect(url_for("pages.index"))


@bp.route("/")
def dashboard():
    """Render admin dashboard."""
    user = get_current_user()

    # Get statistics
    users = repository.scan_users()
    subscriptions = repository.scan_subscriptions()

    # Calculate statistics
    total_users = len(users)
    premium_users = sum(
        1
        for s in subscriptions
        if s.plan == Subscription.PLAN_PREMIUM and s.is_active()
    )
    free_users = total_users - premium_users

    # Calculate revenue
    payments = []
    for user_email in [u.email for u in users]:
        payments.extend(repository.get_user_payments(user_email))

    total_revenue = sum(
        p.amount for p in payments if p.status == Payment.STATUS_COMPLETED
    )

    # Get recent payments
    recent_payments = sorted(payments, key=lambda p: p.created_at, reverse=True)[:10]

    return render_template(
        "admin/dashboard.html",
        user=user,
        total_users=total_users,
        premium_users=premium_users,
        free_users=free_users,
        total_revenue=total_revenue,
        recent_payments=recent_payments,
    )


@bp.route("/users")
def users():
    """Render users management page."""
    user = get_current_user()

    # Get all users
    all_users = repository.scan_users()

    # Get subscription status for each user
    user_data = []
    for u in all_users:
        subscription = repository.get_user_subscription(u.email)
        user_data.append(
            {
                "user": u,
                "subscription": subscription,
                "is_admin": u.email in ADMIN_EMAILS,
            }
        )

    return render_template(
        "admin/users.html",
        user=user,
        users=user_data,
    )


@bp.route("/users/<email>")
def user_detail(email):
    """Render user detail page."""
    admin_user = get_current_user()

    # Get user
    user = repository.get_user_by_email(email)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin.users"))

    # Get user's subscription
    subscription = repository.get_user_subscription(email)

    # Get user's payments
    payments = repository.get_user_payments(email)

    # Get user's children
    children = repository.get_children_by_parent(email)

    # Get worksheets for each child
    worksheets_by_child = {}
    for child in children:
        worksheets = repository.get_child_worksheets(child.id)
        worksheets_by_child[child.id] = worksheets

    return render_template(
        "admin/user_detail.html",
        user=admin_user,
        target_user=user,
        subscription=subscription,
        payments=payments,
        children=children,
        worksheets_by_child=worksheets_by_child,
    )


@bp.route("/subscriptions")
def subscriptions():
    """Render subscriptions management page."""
    user = get_current_user()

    # Get all subscriptions
    all_subscriptions = repository.scan_subscriptions()

    # Get user for each subscription
    subscription_data = []
    for s in all_subscriptions:
        u = repository.get_user_by_email(s.user_email)
        subscription_data.append(
            {
                "subscription": s,
                "user": u,
            }
        )

    return render_template(
        "admin/subscriptions.html",
        user=user,
        subscriptions=subscription_data,
    )


@bp.route("/payments")
def payments():
    """Render payments management page."""
    user = get_current_user()

    # Get all payments
    all_payments = []
    users = repository.scan_users()
    for u in users:
        all_payments.extend(repository.get_user_payments(u.email))

    # Sort by date (newest first)
    all_payments.sort(key=lambda p: p.created_at, reverse=True)

    # Get user for each payment
    payment_data = []
    for p in all_payments:
        u = repository.get_user_by_email(p.user_email)
        payment_data.append(
            {
                "payment": p,
                "user": u,
                "date": datetime.fromtimestamp(p.created_at).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )

    return render_template(
        "admin/payments.html",
        user=user,
        payments=payment_data,
    )


@bp.route("/update_subscription", methods=["POST"])
def update_subscription():
    """Update a user's subscription."""
    user = get_current_user()

    user_email = request.form.get("user_email")
    plan = request.form.get("plan")
    status = request.form.get("status")

    if not all([user_email, plan, status]):
        flash("Missing required fields.", "error")
        return redirect(url_for("admin.subscriptions"))

    # Get subscription
    subscription = repository.get_user_subscription(user_email)
    if not subscription:
        subscription = Subscription(user_email=user_email)

    # Update subscription
    subscription.plan = plan
    subscription.status = status
    subscription.updated_at = datetime.now().timestamp()

    # If upgrading to premium, set appropriate limits
    if plan == Subscription.PLAN_PREMIUM:
        subscription.worksheets_limit = Subscription.UNLIMITED_WORKSHEETS  # Unlimited
    else:
        subscription.worksheets_limit = (
            Subscription.FREE_TIER_LIMIT
        )  # Default free tier limit

    repository.update_subscription(subscription)

    flash(f"Subscription updated for {user_email}.", "success")
    return redirect(url_for("admin.subscriptions"))
