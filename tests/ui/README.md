# MathTutor UI Tests

This directory contains UI tests for the MathTutor application using Selenium WebDriver.

## Setup

1. Install the required dependencies:

```bash
pip install -r tests/ui/requirements.txt
```

2. Make sure you have Chrome or Firefox installed on your system.

3. For PDF testing, you'll need Poppler installed:
   - On macOS: `brew install poppler`
   - On Ubuntu/Debian: `apt-get install poppler-utils`
   - On Windows: Download from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)

## Running the Tests

### Run all UI tests:

```bash
pytest tests/ui
```

### Run specific test file:

```bash
pytest tests/ui/test_worksheet_generation.py
```

### Run tests with specific marker:

```bash
pytest tests/ui -m pdf
```

### Run tests in parallel:

```bash
pytest tests/ui -n 2
```

### Run tests with automatic screenshots on failure:

Screenshots are automatically taken when tests fail. This is configured in the pytest.ini file with:
```
--screenshot=on
--screenshot_path=on
```

Screenshots will be saved to the `./screenshot/YYYY-MM-DD/` directory.

## Test Reports

HTML test reports are generated in the `test-reports` directory. Screenshots of failed tests are also saved to the `screenshot` directory and attached to the HTML report.

## Environment Variables

You can configure the tests using the following environment variables:

- `TEST_BASE_URL`: Base URL of the application (default: `http://localhost:5000`)
- `TEST_EMAIL`: Email for login (default: `test@example.com`)
- `TEST_PASSWORD`: Password for login (default: `password`)
- `CI`: Set to `true` to run in headless mode (for CI environments)

## Test Structure

- `conftest.py`: Contains fixtures for UI testing
- `pages/`: Page Object Models for different pages of the application
- `test_*.py`: Test files

## PDF Testing

The tests specifically check for the issue where PDF content starts halfway down the page. They:

1. Generate worksheets and answer keys
2. Download the resulting PDFs
3. Analyze the PDFs to ensure content starts at the top of the page
4. Save screenshots of the PDF pages for visual inspection

## Troubleshooting

- **WebDriver issues**: Make sure you have the latest version of Chrome or Firefox installed
- **PDF conversion issues**: Ensure Poppler is correctly installed and in your PATH
- **Test failures**: Check the HTML report and screenshots for details
- **Screenshot issues**: If screenshots are not being taken on failure, ensure the WebDriver instance is properly set up in the fixture 