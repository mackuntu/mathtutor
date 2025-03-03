# MathTutor Deployment Guide

This guide provides step-by-step instructions for deploying the MathTutor application to AWS using GitHub Actions, DynamoDB, and Elastic Beanstalk.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Setup](#aws-setup)
3. [Stripe Integration](#stripe-integration)
4. [Ad Integration](#ad-integration)
5. [GitHub Repository Setup](#github-repository-setup)
6. [GitHub Secrets Configuration](#github-secrets-configuration)
7. [Deployment Process](#deployment-process)
8. [Post-Deployment Configuration](#post-deployment-configuration)
9. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
10. [Updating the Application](#updating-the-application)
11. [Rollback Procedure](#rollback-procedure)

## Prerequisites

Before you begin, ensure you have:

- An AWS account with administrative access
- A GitHub account with access to the repository
- The MathTutor codebase
- AWS CLI installed locally (for testing)
- A Stripe account for payment processing
- Google AdSense and/or Facebook Audience Network accounts for advertising

## AWS Setup

### 1. Create an IAM User for Deployment

1. Go to the AWS IAM Console
2. Click "Users" and then "Add user"
3. Enter a name (e.g., `mathtutor-deployer`)
4. Select "Programmatic access"
5. Click "Next: Permissions"
6. Click "Attach existing policies directly"
7. Search for and select the following policies:
   - `AmazonDynamoDBFullAccess`
   - `AWSElasticBeanstalkFullAccess`
   - `AmazonS3FullAccess`
8. Click "Next: Tags" (optional: add tags)
9. Click "Next: Review" and then "Create user"
10. **Important**: Save the Access Key ID and Secret Access Key securely

### 2. Create an S3 Bucket for Deployment Artifacts

1. Go to the AWS S3 Console
2. Click "Create bucket"
3. Enter a unique bucket name (e.g., `mathtutor-deployments-[unique-id]`)
4. Select your preferred region
5. Keep default settings for other options
6. Click "Create bucket"

### 3. Set Up Elastic Beanstalk

1. Go to the AWS Elastic Beanstalk Console
2. Click "Create application"
3. Enter "mathtutor" as the application name
4. Click "Create"
5. Click "Create environment"
6. Select "Web server environment"
7. Enter "mathtutor-prod" as the environment name
8. Select "Python" as the platform
9. Select "Python 3.10" as the platform branch
10. Choose "Sample application" (we'll deploy our app later)
11. Click "Create environment"

### 4. Set Up DynamoDB Tables

The DynamoDB tables will be created automatically during deployment, but you can also create them manually:

1. Go to the AWS DynamoDB Console
2. Click "Create table"
3. Create the following tables with the specified primary keys:
   - `Users` (Primary key: `id` - String)
     - Add GSI: `email-index` (Primary key: `email` - String)
   - `Children` (Primary key: `id` - String)
     - Add GSI: `user_id-index` (Primary key: `user_id` - String)
   - `Worksheets` (Primary key: `id` - String)
     - Add GSI: `child_id-index` (Primary key: `child_id` - String)
     - Add GSI: `user_id-index` (Primary key: `user_id` - String)
   - `Sessions` (Primary key: `id` - String)
     - Add GSI: `user_id-index` (Primary key: `user_id` - String)
   - `Subscriptions` (Primary key: `id` - String)
     - Add GSI: `user_id-index` (Primary key: `user_id` - String)
     - Add GSI: `stripe_subscription_id-index` (Primary key: `stripe_subscription_id` - String)

## Stripe Integration

### 1. Create and Set Up a Stripe Account

1. Sign up for a Stripe account at https://stripe.com
2. Complete the account verification process
3. Go to the Stripe Dashboard

### 2. Configure Stripe Products and Pricing

1. In the Stripe Dashboard, go to "Products" > "Add Product"
2. Create the following products:

   **Free Tier**:
   - Name: "MathTutor Free"
   - Description: "Limited worksheet generation"
   - Pricing: $0/month (recurring)
   - Features:
     - 5 worksheets per week
     - Basic problem types
     - Standard templates

   **Premium Subscription**:
   - Name: "MathTutor Premium"
   - Description: "Unlimited worksheet generation"
   - Pricing: $9.99/month (recurring)
   - Features:
     - Unlimited worksheets
     - All problem types
     - Premium templates
     - Priority support

3. Note down the Price IDs for each product (you'll need these for your application)

### 3. Set Up Stripe Webhook

1. In the Stripe Dashboard, go to "Developers" > "Webhooks"
2. Click "Add endpoint"
3. Enter your webhook URL: `https://your-app-url.elasticbeanstalk.com/webhook/stripe`
4. Select the following events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `checkout.session.completed`
5. Click "Add endpoint"
6. Reveal and copy the signing secret (you'll need this for webhook verification)

### 4. Get Stripe API Keys

1. In the Stripe Dashboard, go to "Developers" > "API keys"
2. Copy the Publishable key and Secret key
3. Store these securely for later use in GitHub Secrets

## Ad Integration

### 1. Set Up Google AdSense

1. Sign up for Google AdSense at https://www.google.com/adsense
2. Add and verify your website
3. Wait for account approval (this may take a few days)
4. Once approved, create ad units:
   - Go to "Ads" > "By ad unit"
   - Click "Create new ad unit"
   - Create the following ad units:
     - Sidebar Ad (300x250 or 300x600)
     - In-content Ad (responsive)
     - Footer Ad (728x90)
5. Copy your AdSense client ID (format: `ca-pub-XXXXXXXXXXXXXXXX`)

### 2. Set Up Facebook Audience Network (Optional)

1. Sign up for Facebook Audience Network
2. Create an app in the Facebook Developer Portal
3. Set up placements for your application
4. Copy the placement IDs for each ad location

### 3. Implement Ad Components

1. Create reusable ad components in your templates:
   - `components/ads.html` with macros for different ad types
   - Implement ad loading with proper fallbacks
2. Add ad placements to your templates:
   - Sidebar ads on the main dashboard
   - In-content ads between sections
   - Footer ads where appropriate

## GitHub Repository Setup

1. Push your MathTutor code to a GitHub repository
2. Ensure the repository has the following files:
   - `.github/workflows/deploy.yml`
   - `.github/workflows/tests.yml`
   - `.ebextensions/python.config`
   - `Procfile`
   - `requirements.txt` (with gunicorn added)
   - `scripts/create_dynamodb_tables.py`
   - `scripts/test_dynamodb_connection.py`
   - `scripts/test_stripe_connection.py`

## GitHub Secrets Configuration

Add the following secrets to your GitHub repository:

1. Go to your GitHub repository
2. Click "Settings" > "Secrets and variables" > "Actions"
3. Click "New repository secret"
4. Add the following secrets:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | AWS region | `us-west-2` |
| `AWS_S3_BUCKET` | S3 bucket name | `mathtutor-deployments-unique-id` |
| `FLASK_SECRET_KEY` | Secret key for Flask | Random string (e.g., `openssl rand -hex 24`) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | From Google Developer Console |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | From Google Developer Console |
| `GOOGLE_REDIRECT_URI` | Google OAuth redirect URI | `https://your-app-url.elasticbeanstalk.com/oauth/callback` |
| `FACEBOOK_CLIENT_ID` | Facebook OAuth client ID | From Facebook Developer Portal |
| `FACEBOOK_CLIENT_SECRET` | Facebook OAuth client secret | From Facebook Developer Portal |
| `FACEBOOK_REDIRECT_URI` | Facebook OAuth redirect URI | `https://your-app-url.elasticbeanstalk.com/oauth/callback` |
| `X_CLIENT_ID` | X (Twitter) OAuth client ID | From Twitter Developer Portal |
| `X_CLIENT_SECRET` | X (Twitter) OAuth client secret | From Twitter Developer Portal |
| `X_REDIRECT_URI` | X (Twitter) OAuth redirect URI | `https://your-app-url.elasticbeanstalk.com/oauth/callback` |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | `pk_test_...` or `pk_live_...` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_test_...` or `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret | `whsec_...` |
| `STRIPE_PRICE_ID_FREE` | Stripe Price ID for free tier | `price_...` |
| `STRIPE_PRICE_ID_PREMIUM` | Stripe Price ID for premium tier | `price_...` |
| `GOOGLE_ADSENSE_CLIENT_ID` | Google AdSense client ID | `ca-pub-XXXXXXXXXXXXXXXX` |
| `GOOGLE_ADSENSE_SIDEBAR_SLOT` | AdSense sidebar ad slot ID | `XXXXXXXXXX` |
| `GOOGLE_ADSENSE_CONTENT_SLOT` | AdSense in-content ad slot ID | `XXXXXXXXXX` |
| `FACEBOOK_AD_PLACEMENT_ID` | Facebook Audience Network placement ID | `XXXXXXXXXX` (if applicable) |

## Deployment Process

### Automatic Deployment

1. Push your code to the `main` branch
2. GitHub Actions will automatically:
   - Run tests
   - Create DynamoDB tables if they don't exist
   - Package the application
   - Deploy to Elastic Beanstalk

### Manual Deployment

You can also manually trigger the deployment:

1. Go to your GitHub repository
2. Click "Actions"
3. Select the "Deploy MathTutor App" workflow
4. Click "Run workflow"
5. Select the branch to deploy
6. Click "Run workflow"

## Post-Deployment Configuration

### 1. Verify Subscription System

1. Log in to the application
2. Navigate to the subscription management page
3. Test subscribing to the premium plan:
   - Use Stripe test card: `4242 4242 4242 4242`
   - Any future expiration date
   - Any 3-digit CVC
   - Any billing address
4. Verify that the subscription status updates correctly
5. Verify that worksheet generation limits are enforced correctly

### 2. Test Stripe Webhooks

1. In the Stripe Dashboard, go to "Developers" > "Webhooks"
2. Find your webhook endpoint
3. Click "Send test webhook"
4. Select an event type (e.g., `customer.subscription.updated`)
5. Send the test webhook
6. Verify in your application logs that the webhook was received and processed

### 3. Verify Ad Integration

1. Visit different pages of your application
2. Verify that ads are displaying in the correct locations
3. Check browser console for any ad-related errors
4. Test with different devices and screen sizes to ensure responsive behavior

## Monitoring and Troubleshooting

### Monitoring

1. **Elastic Beanstalk Console**:
   - Go to the Elastic Beanstalk Console
   - Select your environment
   - Check the "Health" tab for environment status
   - Check the "Logs" tab for application logs

2. **CloudWatch**:
   - Go to the CloudWatch Console
   - Check "Logs" for application logs
   - Set up alarms for monitoring

3. **Stripe Dashboard**:
   - Monitor subscription events
   - Track payment successes and failures
   - Set up Stripe alerts for important events

4. **AdSense Dashboard**:
   - Monitor ad performance
   - Track revenue and impressions
   - Optimize ad placements based on performance

### Troubleshooting

1. **Deployment Issues**:
   - Check GitHub Actions logs for deployment errors
   - Check Elastic Beanstalk logs for application startup errors

2. **Application Issues**:
   - Check Elastic Beanstalk logs for application errors
   - SSH into the EC2 instance for direct troubleshooting

3. **Database Issues**:
   - Check DynamoDB tables in the AWS Console
   - Run the `test_dynamodb_connection.py` script locally with production credentials

4. **Subscription Issues**:
   - Check Stripe Dashboard for subscription status
   - Verify webhook delivery in Stripe logs
   - Check application logs for webhook processing errors

5. **Ad Issues**:
   - Check browser console for ad-related errors
   - Verify ad units are approved in AdSense
   - Test with ad blockers disabled

## Updating the Application

To update the application:

1. Make changes to your code
2. Push to the `main` branch
3. GitHub Actions will automatically deploy the changes

For major updates:

1. Create a new branch
2. Make changes
3. Create a pull request
4. Review and test
5. Merge to `main` to deploy

### Updating Subscription Plans

To update subscription plans:

1. Create new products/prices in the Stripe Dashboard
2. Update the application code with new price IDs
3. Update the GitHub Secrets with new price IDs
4. Deploy the changes
5. Test the new subscription plans

### Updating Ad Placements

To update ad placements:

1. Create new ad units in AdSense/Facebook Audience Network
2. Update the ad component templates
3. Update the GitHub Secrets with new ad unit IDs
4. Deploy the changes
5. Test the new ad placements

## Rollback Procedure

If you need to rollback to a previous version:

1. Go to the Elastic Beanstalk Console
2. Select your environment
3. Click "Application versions"
4. Select a previous version
5. Click "Deploy"

Alternatively, you can revert commits in GitHub and push to `main` to trigger a new deployment.

### Subscription Rollback Considerations

When rolling back changes that affect subscriptions:

1. Ensure compatibility between the application version and Stripe product/price configuration
2. Consider the impact on existing subscribers
3. Test subscription functionality after rollback

### Ad Integration Rollback Considerations

When rolling back changes that affect ad integration:

1. Ensure ad components are compatible with the rolled-back version
2. Verify ad display after rollback
3. Monitor ad performance after rollback 