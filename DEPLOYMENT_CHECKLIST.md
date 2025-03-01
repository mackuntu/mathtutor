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

## Deployment

- [ ] Code pushed to `main` branch or workflow manually triggered
- [ ] GitHub Actions workflow completed successfully
- [ ] Application deployed to Elastic Beanstalk

## Post-Deployment Verification

- [ ] Application is accessible at the Elastic Beanstalk URL
- [ ] Login functionality works
- [ ] DynamoDB tables are created and accessible
- [ ] All application features work as expected

## Monitoring Setup

- [ ] CloudWatch alarms configured (optional)
- [ ] Logging configured and verified

## Documentation

- [ ] Deployment documentation updated
- [ ] URL and access information shared with team
- [ ] Any issues or workarounds documented 