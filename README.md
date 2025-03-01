# MathTutor Application

A web application for generating and managing math worksheets for children.

## Recent Refactoring

The application has been refactored from a monolithic structure to a more modular one:

1. **Route Organization**: Routes are now organized by functional area in the `routes` package.
2. **Blueprint Structure**: Each functional area has its own Flask blueprint.
3. **Common Functionality**: Shared functionality has been extracted to a common module.
4. **Initialization**: The application initialization has been simplified.

## Project Structure

The application follows a modular structure:

```
src/
├── __init__.py           # Application factory
├── auth.py               # Authentication manager
├── config.py             # Configuration settings
├── database.py           # Database connection
├── exceptions.py         # Custom exceptions
├── generator.py          # Math problem generator
├── main.py               # CLI entry point
├── models.py             # Data models
├── renderer.py           # PDF renderer
├── web.py                # Web routes initialization
├── database/             # Database modules
│   ├── __init__.py
│   ├── config.py
│   ├── create_tables.py
│   ├── dynamodb.py
│   ├── models.py
│   └── repository.py
├── document/             # Document generation
│   └── ...
├── routes/               # Web route handlers
│   ├── __init__.py       # Blueprint registration
│   ├── auth.py           # Authentication routes
│   ├── children.py       # Child management routes
│   ├── common.py         # Shared functionality
│   ├── pages.py          # Static page routes
│   └── worksheets.py     # Worksheet routes
├── static/               # Static assets
│   └── ...
├── templates/            # HTML templates
│   └── ...
└── utils/                # Utility functions
    └── ...
```

## Refactoring Changes

The application has been refactored from a monolithic structure to a more modular one:

1. **Route Organization**: Routes are now organized by functional area in the `routes` package.
2. **Blueprint Structure**: Each functional area has its own Flask blueprint.
3. **Common Functionality**: Shared functionality has been extracted to a common module.
4. **Initialization**: The application initialization has been simplified.

## Running the Application

To run the application:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run the application:
   ```
   flask run
   ```

## Development

To set up the development environment:

1. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

3. Run tests:
   ```
   pytest
   ```

### Product Requirements Document: MathTutor System

#### Overview
The MathTutor system simplifies the creation and distribution of personalized math worksheets for families, enabling parents to provide consistent, quality math practice for their children. The system focuses on paper-based learning with efficient parent-guided feedback mechanisms.

---

## Quick Start Guide

### Prerequisites
- Python 3.12
- Java Runtime Environment (JRE) for DynamoDB Local
- OAuth credentials from:
  - Google Cloud Console
  - Facebook Developers
  - X (Twitter) Developer Portal

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:mackuntu/mathtutor.git
   cd mathtutor
   ```

2. **Set Up Python Environment**:
   ```bash
   # Using pyenv (recommended)
   pyenv install 3.12
   pyenv local 3.12
   
   # Create and activate virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Set Up DynamoDB Local**:
   ```bash
   # Download and extract DynamoDB Local
   curl -O https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.tar.gz
   tar xzf dynamodb_local_latest.tar.gz
   
   # Start DynamoDB Local (keep this running in a separate terminal)
   java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
   ```

4. **Configure Environment**:
   ```bash
   # Copy example environment file
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```ini
   # AWS/DynamoDB Configuration
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_DEFAULT_REGION=us-west-2
   DYNAMODB_ENDPOINT=http://localhost:8000
   
   # OAuth Configuration
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   
   FACEBOOK_CLIENT_ID=your_facebook_client_id
   FACEBOOK_CLIENT_SECRET=your_facebook_client_secret
   
   X_CLIENT_ID=your_x_client_id
   X_CLIENT_SECRET=your_x_client_secret
   
   # Application Settings
   FLASK_SECRET_KEY=your_random_secret_key
   OAUTH_REDIRECT_URI=http://localhost:8080/oauth/callback
   ```

### OAuth Setup Guide

#### Google OAuth Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable the Google+ API and OAuth2 API
4. Go to Credentials → Create Credentials → OAuth Client ID
5. Configure the OAuth consent screen:
   - Add authorized domains
   - Add scopes for email and profile
6. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Name: MathTutor
   - Authorized redirect URIs: `http://localhost:8080/oauth/callback`
7. Copy the Client ID and Client Secret to your `.env` file

#### Facebook OAuth Setup
1. Go to [Facebook Developers](https://developers.facebook.com)
2. Create a new app or select an existing one
3. Add Facebook Login product to your app
4. Go to Facebook Login → Settings:
   - Add `http://localhost:8080/oauth/callback` to Valid OAuth Redirect URIs
5. Go to Basic Settings:
   - Copy App ID to `FACEBOOK_CLIENT_ID`
   - Copy App Secret to `FACEBOOK_CLIENT_SECRET`
6. Configure app permissions:
   - Add email and public_profile permissions

#### X (Twitter) OAuth Setup
1. Go to [X Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new project and app
3. Enable OAuth 2.0
4. In project settings:
   - Set Type to Web App
   - Add `http://localhost:8080/oauth/callback` to Callback URLs
   - Enable OAuth 2.0 scopes:
     - `tweet.read`
     - `users.read`
     - `offline.access`
5. Copy API Key to `X_CLIENT_ID`
6. Copy API Secret Key to `X_CLIENT_SECRET`

### Security Notes
- Never commit `.env` file to version control
- Keep OAuth credentials secure
- Regularly rotate secrets in production
- Use different credentials for development and production

5. **Initialize Database**:
   ```bash
   # Create DynamoDB tables
   python src/database/create_tables.py
   ```

6. **Run the Application**:
   ```bash
   # Start the Flask application
   python -m src.web
   ```

   The application will be available at http://localhost:8080

### Running in Development

1. **Start DynamoDB Local** (in a separate terminal):
   ```bash
   java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb
   ```

2. **Start the Flask Application** (in another terminal):
   ```bash
   python -m src.web
   ```

3. **Access the Application**:
   - Open http://localhost:8080 in your browser
   - Log in using any of the configured OAuth providers
   - Start managing children and generating worksheets

### Troubleshooting

1. **DynamoDB Connection Issues**:
   - Ensure DynamoDB Local is running (port 8000)
   - Check AWS credentials in `.env`
   - Verify DYNAMODB_ENDPOINT is set correctly

2. **OAuth Login Problems**:
   - Verify OAuth credentials in `.env`
   - Ensure redirect URIs are configured in provider consoles
   - Check that OAUTH_REDIRECT_URI matches the configured callbacks

3. **Application Errors**:
   - Check application logs for detailed error messages
   - Verify all required environment variables are set
   - Ensure Python virtual environment is activated

---

## Features

### Authentication
- Multi-provider social login support:
  - Google OAuth2
  - Facebook OAuth2
  - X (Twitter) OAuth2
- Secure session management
- User profile management

### Child Management
- Add, edit, and remove children profiles
- Customize per child:
  - Grade level
  - Birthday tracking
  - Color preferences
- Multi-child support for families

### Worksheet Generation
- Grade-appropriate content
- Customizable difficulty levels
- Print-ready formatting
- Answer overlays for grading

### Progress Tracking
- Worksheet history
- Completion tracking
- Performance insights

---

## Technical Stack

### Backend
- Python 3.12
- Flask web framework
- DynamoDB for data storage
- OAuth2 for authentication

### Frontend
- HTML5/CSS3
- Bootstrap for responsive design
- JavaScript for interactive features

### Database Schema

#### Users
- Primary Key: email (String)
- Attributes:
  - name (String)
  - picture (String, optional)
  - created_at (Number)
  - updated_at (Number)

#### Children
- Primary Key: id (String)
- GSI: ParentEmailIndex
- Attributes:
  - parent_email (String)
  - name (String)
  - birthday (String)
  - grade_level (Number)
  - preferred_color (String)
  - created_at (Number)
  - updated_at (Number)

#### Sessions
- Primary Key: token (String)
- GSI: UserEmailIndex
- Attributes:
  - user_email (String)
  - expires_at (Number)
  - created_at (Number)

#### Worksheets
- Primary Key: id (String)
- GSI: ChildIdIndex
- Attributes:
  - child_id (String)
  - problems (List)
  - answers (List)
  - completed (Boolean)
  - created_at (Number)
  - updated_at (Number)

---

## Development

### Testing
```bash
python -m pytest tests/
```

### Code Style
- Black for Python formatting
- Flake8 for linting
- MyPy for type checking

---

## Recent Updates

- Implemented multi-provider social login (Google, Facebook, X)
- Enhanced child profile management with birthday tracking
- Added color preferences for worksheet customization
- Improved error handling and validation
- Set up local DynamoDB for development
- Updated authentication flow with proper token handling
- Enhanced UI with modern design elements

---

## License

MIT License

