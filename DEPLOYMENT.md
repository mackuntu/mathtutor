# MathTutor Deployment Guide

This document provides instructions for deploying the MathTutor application to AWS using GitHub Actions.

## Prerequisites

1. AWS Account with appropriate permissions
2. GitHub repository with the MathTutor code
3. GitHub Actions enabled on the repository
4. Stripe account for payment processing
5. Google AdSense and/or Facebook Audience Network accounts for ad integration

## AWS Resources Required

1. **DynamoDB**: For storing application data
2. **Elastic Beanstalk**: For hosting the web application
3. **S3 Bucket**: For storing deployment artifacts
4. **IAM User**: With permissions for DynamoDB, Elastic Beanstalk, and S3

## Setting Up AWS Resources

### 1. Create an IAM User

1. Go to the AWS IAM Console
2. Create a new user with programmatic access
3. Attach the following policies:
   - `AmazonDynamoDBFullAccess`
   - `AWSElasticBeanstalkFullAccess`
   - `AmazonS3FullAccess`
4. Save the Access Key ID and Secret Access Key

### 2. Create an S3 Bucket

1. Go to the AWS S3 Console
2. Create a new bucket for deployment artifacts (e.g., `mathtutor-deployments`)
3. Keep the default settings

### 3. Create Elastic Beanstalk Application

1. Go to the AWS Elastic Beanstalk Console
2. Create a new application named `mathtutor`
3. Create a new environment:
   - Web server environment
   - Environment name: `mathtutor-prod`
   - Platform: Python
   - Platform branch: Python 3.10
   - Sample application (we'll deploy our app later)

### 4. Set Up DynamoDB

The DynamoDB tables will be created automatically during deployment, with the following structure:
- `Users`: Stores user information and subscription details
- `Children`: Stores information about children profiles
- `Worksheets`: Stores generated worksheet data
- `Sessions`: Stores user session data

## Setting Up Stripe Integration

### 1. Create a Stripe Account

1. Sign up for a Stripe account at https://stripe.com
2. Complete the verification process

### 2. Configure Stripe Products and Prices

1. In the Stripe Dashboard, go to "Products"
2. Create the following products:
   - **Free Tier**: 
     - Price: $0/month
     - Features: Limited worksheet generation (e.g., 5 per week)
   - **Premium Subscription**:
     - Price: $9.99/month (or your desired price)
     - Features: Unlimited worksheet generation

### 3. Set Up Stripe Webhook

1. In the Stripe Dashboard, go to "Developers" > "Webhooks"
2. Add an endpoint URL: `https://your-app-url.elasticbeanstalk.com/webhook/stripe`
3. Select the following events to listen for:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Save the webhook secret for later use

### 4. Get API Keys

1. In the Stripe Dashboard, go to "Developers" > "API keys"
2. Note down the Publishable Key and Secret Key

## Setting Up Ad Integration

### 1. Google AdSense

1. Sign up for Google AdSense at https://www.google.com/adsense
2. Add your website and verify ownership
3. Create ad units for different placements:
   - Sidebar ads
   - In-content ads
4. Note down your AdSense client ID

### 2. Facebook Audience Network (Optional)

1. Sign up for Facebook Audience Network
2. Create placement IDs for your application
3. Note down the placement IDs

## Setting Up GitHub Secrets

Add the following secrets to your GitHub repository:

1. `AWS_ACCESS_KEY_ID`: IAM user access key
2. `AWS_SECRET_ACCESS_KEY`: IAM user secret key
3. `AWS_REGION`: AWS region (e.g., `us-west-2`)
4. `AWS_S3_BUCKET`: S3 bucket name (e.g., `mathtutor-deployments`)
5. `FLASK_SECRET_KEY`: A secure random string for Flask
6. `GOOGLE_CLIENT_ID`: Google OAuth client ID
7. `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
8. `GOOGLE_REDIRECT_URI`: Google OAuth redirect URI (e.g., `https://your-app-url.elasticbeanstalk.com/oauth/callback`)
9. `FACEBOOK_CLIENT_ID`: Facebook OAuth client ID
10. `FACEBOOK_CLIENT_SECRET`: Facebook OAuth client secret
11. `FACEBOOK_REDIRECT_URI`: Facebook OAuth redirect URI
12. `X_CLIENT_ID`: X (Twitter) OAuth client ID
13. `X_CLIENT_SECRET`: X (Twitter) OAuth client secret
14. `X_REDIRECT_URI`: X (Twitter) OAuth redirect URI
15. `STRIPE_PUBLISHABLE_KEY`: Stripe publishable key
16. `STRIPE_SECRET_KEY`: Stripe secret key
17. `STRIPE_WEBHOOK_SECRET`: Stripe webhook signing secret
18. `GOOGLE_ADSENSE_CLIENT_ID`: Google AdSense client ID
19. `FACEBOOK_AD_PLACEMENT_ID`: Facebook Audience Network placement ID (if applicable)

## Deployment Process

1. Push your code to the `main` branch of your GitHub repository
2. GitHub Actions will automatically:
   - Run tests
   - Create DynamoDB tables if they don't exist
   - Package the application
   - Deploy to Elastic Beanstalk

You can also manually trigger the deployment workflow from the GitHub Actions tab.

## Post-Deployment Configuration

### 1. Verify Stripe Webhook

1. Make a test subscription to verify the webhook is working
2. Check the application logs to ensure events are being received

### 2. Verify Ad Integration

1. Visit different pages of the application to ensure ads are displaying correctly
2. Check for any console errors related to ad loading

## Monitoring and Troubleshooting

1. **Elastic Beanstalk Logs**: Check the Elastic Beanstalk console for application logs
2. **GitHub Actions Logs**: Check the GitHub Actions tab for deployment logs
3. **CloudWatch**: Set up CloudWatch for monitoring application metrics
4. **Stripe Dashboard**: Monitor subscription events and payment status
5. **AdSense Dashboard**: Monitor ad performance and revenue

## Updating the Application

To update the application, simply push changes to the `main` branch. GitHub Actions will automatically deploy the changes.

## Rollback

To rollback to a previous version:

1. Go to the Elastic Beanstalk console
2. Select your environment
3. Go to "Application versions"
4. Select a previous version
5. Click "Deploy" 