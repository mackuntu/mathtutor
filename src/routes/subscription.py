"""Subscription management routes for the MathTutor application."""

import logging
import os
from datetime import datetime, timedelta

import stripe
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from ..database import get_repository
from ..database.models import Payment, Subscription
from .common import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Initialize components
repository = get_repository()

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_your_test_key")
stripe_public_key = os.getenv("STRIPE_PUBLIC_KEY", "pk_test_your_test_key")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_your_webhook_secret")

# Create blueprint
bp = Blueprint("subscription", __name__, url_prefix="/subscription")


@bp.route("/")
def subscription_page():
    """Render subscription management page."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    # Get user's current subscription
    subscription = repository.get_user_subscription(user.email)

    # If no subscription exists, create a free tier subscription
    if not subscription:
        subscription = Subscription(user_email=user.email)
        repository.create_subscription(subscription)

    # Get payment history
    payments = repository.get_user_payments(user.email)

    return render_template(
        "subscription.html",
        user=user,
        subscription=subscription,
        payments=payments,
        stripe_public_key=stripe_public_key,
    )


@bp.route("/upgrade", methods=["POST"])
def upgrade_subscription():
    """Upgrade to premium subscription."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    try:
        # Create a Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "MathTutor Premium Subscription",
                            "description": "Unlimited worksheet generation and advanced analytics",
                        },
                        "unit_amount": 499,  # $4.99 in cents
                        "recurring": {
                            "interval": "month",
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=request.host_url + url_for("subscription.success"),
            cancel_url=request.host_url + url_for("subscription.subscription_page"),
            client_reference_id=user.email,
        )

        return jsonify({"id": checkout_session.id})
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/success")
def success():
    """Handle successful subscription."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    flash("Your subscription has been activated successfully!", "success")
    return redirect(url_for("subscription.subscription_page"))


@bp.route("/cancel", methods=["POST"])
def cancel_subscription():
    """Cancel premium subscription."""
    user = get_current_user()
    if not user:
        return redirect(url_for("auth.login"))

    subscription = repository.get_user_subscription(user.email)
    if not subscription:
        flash("No active subscription found.", "error")
        return redirect(url_for("subscription.subscription_page"))

    try:
        # If there's a Stripe subscription, cancel it
        if subscription.stripe_subscription_id:
            stripe.Subscription.delete(subscription.stripe_subscription_id)

        # Update subscription status
        subscription.status = Subscription.STATUS_CANCELED
        subscription.end_date = (
            datetime.now() + timedelta(days=30)
        ).timestamp()  # End at the end of current billing period
        repository.update_subscription(subscription)

        flash(
            "Your subscription has been canceled. You will have access until the end of your current billing period.",
            "success",
        )
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        flash(f"Error canceling subscription: {str(e)}", "error")

    return redirect(url_for("subscription.subscription_page"))


@bp.route("/webhook", methods=["POST"])
def webhook():
    """Handle Stripe webhook events."""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid payload: {str(e)}")
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid signature: {str(e)}")
        return "Invalid signature", 400

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        handle_checkout_session(session)
    elif event["type"] == "invoice.paid":
        invoice = event["data"]["object"]
        handle_invoice_paid(invoice)
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        handle_subscription_deleted(subscription)

    return "Success", 200


def handle_checkout_session(session):
    """Handle checkout session completed event."""
    user_email = session.get("client_reference_id")
    if not user_email:
        logger.error("No client_reference_id in checkout session")
        return

    # Get or create subscription
    subscription = repository.get_user_subscription(user_email)
    if not subscription:
        subscription = Subscription(user_email=user_email)

    # Update subscription
    subscription.plan = Subscription.PLAN_PREMIUM
    subscription.status = Subscription.STATUS_ACTIVE
    subscription.start_date = datetime.now().timestamp()
    subscription.stripe_subscription_id = session.get("subscription")
    repository.update_subscription(subscription)

    # Create payment record
    payment = Payment(
        user_email=user_email,
        amount=4.99,
        status=Payment.STATUS_COMPLETED,
        payment_id=session.get("payment_intent"),
        description="Premium subscription activation",
    )
    repository.create_payment(payment)


def handle_invoice_paid(invoice):
    """Handle invoice paid event."""
    subscription_id = invoice.get("subscription")
    customer_id = invoice.get("customer")

    if not subscription_id or not customer_id:
        logger.error("Missing subscription_id or customer_id in invoice")
        return

    # Get customer email from Stripe
    try:
        customer = stripe.Customer.retrieve(customer_id)
        user_email = customer.get("email")

        if not user_email:
            logger.error("No email found for customer")
            return

        # Get subscription
        subscription = repository.get_user_subscription(user_email)
        if not subscription:
            logger.error(f"No subscription found for user {user_email}")
            return

        # Update subscription
        subscription.status = Subscription.STATUS_ACTIVE
        subscription.updated_at = datetime.now().timestamp()
        repository.update_subscription(subscription)

        # Create payment record
        payment = Payment(
            user_email=user_email,
            amount=4.99,
            status=Payment.STATUS_COMPLETED,
            payment_id=invoice.get("payment_intent"),
            description="Premium subscription renewal",
        )
        repository.create_payment(payment)
    except Exception as e:
        logger.error(f"Error handling invoice paid: {str(e)}")


def handle_subscription_deleted(subscription_data):
    """Handle subscription deleted event."""
    subscription_id = subscription_data.get("id")
    customer_id = subscription_data.get("customer")

    if not subscription_id or not customer_id:
        logger.error("Missing subscription_id or customer_id in subscription data")
        return

    # Get customer email from Stripe
    try:
        customer = stripe.Customer.retrieve(customer_id)
        user_email = customer.get("email")

        if not user_email:
            logger.error("No email found for customer")
            return

        # Get subscription
        subscription = repository.get_user_subscription(user_email)
        if not subscription:
            logger.error(f"No subscription found for user {user_email}")
            return

        # Update subscription
        subscription.status = Subscription.STATUS_EXPIRED
        subscription.plan = Subscription.PLAN_FREE
        subscription.updated_at = datetime.now().timestamp()
        repository.update_subscription(subscription)
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {str(e)}")
