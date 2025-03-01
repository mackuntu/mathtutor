# MathTutor Deployment Guide

This document provides instructions for deploying the MathTutor application to AWS using GitHub Actions.

## Prerequisites

1. AWS Account with appropriate permissions
2. GitHub repository with the MathTutor code
3. GitHub Actions enabled on the repository

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

The DynamoDB tables will be created automatically during deployment.

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

## Deployment Process

1. Push your code to the `main` branch of your GitHub repository
2. GitHub Actions will automatically:
   - Run tests
   - Create DynamoDB tables if they don't exist
   - Package the application
   - Deploy to Elastic Beanstalk

You can also manually trigger the deployment workflow from the GitHub Actions tab.

## Monitoring and Troubleshooting

1. **Elastic Beanstalk Logs**: Check the Elastic Beanstalk console for application logs
2. **GitHub Actions Logs**: Check the GitHub Actions tab for deployment logs
3. **CloudWatch**: Set up CloudWatch for monitoring application metrics

## Updating the Application

To update the application, simply push changes to the `main` branch. GitHub Actions will automatically deploy the changes.

## Rollback

To rollback to a previous version:

1. Go to the Elastic Beanstalk console
2. Select your environment
3. Go to "Application versions"
4. Select a previous version
5. Click "Deploy" 