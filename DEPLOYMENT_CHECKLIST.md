# MathTutor Deployment Checklist

Use this checklist to ensure all steps are completed for a successful deployment.

## Pre-Deployment

- [ ] Code is committed and pushed to GitHub
- [ ] All tests pass locally
- [ ] Required files are present:
  - [ ] `.github/workflows/deploy.yml`
  - [ ] `.github/workflows/tests.yml`
  - [ ] `.ebextensions/python.config`
  - [ ] `Procfile`
  - [ ] `requirements.txt` (with gunicorn)
  - [ ] `scripts/create_dynamodb_tables.py`
  - [ ] `scripts/test_dynamodb_connection.py`

## AWS Setup

- [ ] IAM User created with appropriate permissions
- [ ] S3 Bucket created for deployment artifacts
- [ ] Elastic Beanstalk application created
- [ ] Elastic Beanstalk environment created
- [ ] DynamoDB tables configured with proper indexes

## Payment & Subscription Setup

- [ ] Stripe account created and verified
- [ ] Stripe API keys generated
- [ ] Stripe webhook endpoint configured
- [ ] Stripe products and price plans created:
  - [ ] Free tier
  - [ ] Premium subscription
- [ ] Subscription lifecycle hooks implemented
- [ ] Payment processing tested

## Ad Integration

- [ ] Google AdSense account created
- [ ] Google AdSense site verified
- [ ] Ad units created and configured
- [ ] Facebook Audience Network setup (if applicable)
- [ ] Ad placement tested on all pages
- [ ] Ad blockers handled gracefully

## GitHub Secrets

- [ ] `AWS_ACCESS_KEY_ID` added
- [ ] `AWS_SECRET_ACCESS_KEY` added
- [ ] `AWS_REGION` added
- [ ] `AWS_S3_BUCKET` added
- [ ] `FLASK_SECRET_KEY` added (generated with `scripts/generate_secret_key.py`)
- [ ] OAuth secrets added:
  - [ ] `GOOGLE_CLIENT_ID`
  - [ ] `GOOGLE_CLIENT_SECRET`
  - [ ] `GOOGLE_REDIRECT_URI`
  - [ ] `FACEBOOK_CLIENT_ID`
  - [ ] `FACEBOOK_CLIENT_SECRET`
  - [ ] `FACEBOOK_REDIRECT_URI`
  - [ ] `X_CLIENT_ID`
  - [ ] `X_CLIENT_SECRET`
  - [ ] `X_REDIRECT_URI`
- [ ] Stripe secrets added:
  - [ ] `STRIPE_PUBLISHABLE_KEY`
  - [ ] `STRIPE_SECRET_KEY`
  - [ ] `STRIPE_WEBHOOK_SECRET`
- [ ] Ad integration secrets:
  - [ ] `GOOGLE_ADSENSE_CLIENT_ID`
  - [ ] `FACEBOOK_AD_PLACEMENT_ID` (if applicable)

## Deployment

- [ ] Code pushed to `main` branch or workflow manually triggered
- [ ] GitHub Actions workflow completed successfully
- [ ] Application deployed to Elastic Beanstalk

## Post-Deployment Verification

- [ ] Application is accessible at the Elastic Beanstalk URL
- [ ] Login functionality works
- [ ] DynamoDB tables are created and accessible
- [ ] All application features work as expected
- [ ] Subscription management works:
  - [ ] Users can subscribe to premium plan
  - [ ] Payment processing works
  - [ ] Subscription status updates correctly
- [ ] Worksheet generation limits enforced correctly
- [ ] Ads display properly on relevant pages

## Monitoring Setup

- [ ] CloudWatch alarms configured (optional)
- [ ] Logging configured and verified
- [ ] Stripe webhook monitoring enabled
- [ ] Error reporting configured

## Documentation

- [ ] Deployment documentation updated
- [ ] URL and access information shared with team
- [ ] Any issues or workarounds documented
- [ ] Subscription and payment flow documented
- [ ] Ad placement strategy documented 