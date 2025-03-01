# MathTutor Deployment Guide

This guide provides step-by-step instructions for deploying the MathTutor application to AWS using GitHub Actions, DynamoDB, and Elastic Beanstalk.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Setup](#aws-setup)
3. [GitHub Repository Setup](#github-repository-setup)
4. [GitHub Secrets Configuration](#github-secrets-configuration)
5. [Deployment Process](#deployment-process)
6. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
7. [Updating the Application](#updating-the-application)
8. [Rollback Procedure](#rollback-procedure)

## Prerequisites

Before you begin, ensure you have:

- An AWS account with administrative access
- A GitHub account with access to the repository
- The MathTutor codebase
- AWS CLI installed locally (for testing)

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
   - `Children` (Primary key: `id` - String)
   - `Worksheets` (Primary key: `id` - String)
   - `Sessions` (Primary key: `id` - String)

## GitHub Repository Setup

1. Push your MathTutor code to a GitHub repository
2. Ensure the repository has the following files:
   - `.github/workflows/deploy.yml`
   - `.github/workflows/tests.yml`
   - `.ebextensions/python.config`
   - `Procfile`
   - `requirements.txt` (with gunicorn added)
   - `scripts/create_dynamodb_tables.py`

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

## Rollback Procedure

If you need to rollback to a previous version:

1. Go to the Elastic Beanstalk Console
2. Select your environment
3. Click "Application versions"
4. Select a previous version
5. Click "Deploy"

Alternatively, you can revert commits in GitHub and push to `main` to trigger a new deployment. 