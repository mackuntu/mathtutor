"""UI Test configuration and fixtures."""

import datetime
import os
import sys
import tempfile
import time
import warnings
from pathlib import Path
from typing import Generator, Optional

import pypdf
import pytest
from pdf2image import convert_from_path
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Add the project root to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from src.database.models import Subscription
from src.database.repository import DynamoDBRepository

# Filter out specific deprecation warnings from third-party libraries
warnings.filterwarnings(
    "ignore",
    message="datetime.datetime.utcfromtimestamp.*",
    category=DeprecationWarning,
)
warnings.filterwarnings(
    "ignore", message="datetime.datetime.utcnow.*", category=DeprecationWarning
)
warnings.filterwarnings("ignore", message="ARC4 has been moved to.*", category=Warning)

# Configuration
BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8080")
TEST_EMAIL = os.environ.get("TEST_EMAIL", "test-teacher@example.com")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "password")
TEST_BYPASS_KEY = os.environ.get("TEST_BYPASS_KEY", "test-bypass-key-for-selenium")

# Test user information
TEST_USER = {
    "id": "12345",
    "name": "Test Teacher",
    "email": TEST_EMAIL,
    "role": "teacher",
}


@pytest.fixture(scope="session")
def download_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for downloads."""
    # Create a directory for downloads in the project root
    download_path = Path("test-downloads")
    download_path.mkdir(exist_ok=True)
    print(f"Created download directory at: {download_path}")

    # Clear any existing files in the download directory
    for file in download_path.glob("*"):
        try:
            file.unlink()
            print(f"Removed existing file: {file}")
        except Exception as e:
            print(f"Failed to remove file {file}: {e}")

    yield download_path

    # Don't clean up after the session so we can inspect the files if needed


@pytest.fixture(scope="function")
def chrome_driver(request, download_dir):
    """Set up Chrome WebDriver for tests."""
    # Set up Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Enable browser logging
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    # Set download directory to the fixture-provided path
    prefs = {
        "download.default_directory": str(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
        "plugins.always_open_pdf_externally": True,  # Force PDF download instead of opening in browser
    }
    options.add_experimental_option("prefs", prefs)

    print(f"Chrome download directory set to: {download_dir}")

    # Create driver
    driver = webdriver.Chrome(options=options)

    # Set implicit wait time
    driver.implicitly_wait(10)

    # Print capabilities for debugging
    print(f"Chrome capabilities: {driver.capabilities}")

    yield driver

    # Cleanup
    driver.quit()


@pytest.fixture(scope="function")
def firefox_driver(download_dir: Path) -> Generator[webdriver.Firefox, None, None]:
    """Set up Firefox WebDriver with appropriate options."""
    options = FirefoxOptions()

    # Add arguments for headless mode
    options.add_argument("--headless")
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")

    # Set download directory
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.dir", str(download_dir))
    options.set_preference("browser.download.useDownloadDir", True)
    options.set_preference("browser.download.viewableInternally.enabledTypes", "")
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    options.set_preference("pdfjs.disabled", True)

    # Create driver
    driver = webdriver.Firefox(options=options)

    # Set implicit wait time
    driver.implicitly_wait(10)

    yield driver

    # Cleanup
    driver.quit()


@pytest.fixture(scope="function")
def driver(request, chrome_driver):
    """Default WebDriver fixture that uses Chrome."""
    return chrome_driver


@pytest.fixture(scope="function")
def premium_subscription():
    """Create a premium subscription for the test user."""
    # Create repository
    repository = DynamoDBRepository()

    # Check if subscription already exists
    subscription = repository.get_user_subscription(TEST_EMAIL)

    if not subscription:
        # Create a new premium subscription
        subscription = Subscription(
            user_email=TEST_EMAIL,
            plan=Subscription.PLAN_PREMIUM,
            status=Subscription.STATUS_ACTIVE,
            worksheets_limit=Subscription.UNLIMITED_WORKSHEETS,
        )
        repository.create_subscription(subscription)
    else:
        # Update existing subscription to premium
        subscription.plan = Subscription.PLAN_PREMIUM
        subscription.status = Subscription.STATUS_ACTIVE
        subscription.worksheets_limit = Subscription.UNLIMITED_WORKSHEETS
        repository.update_subscription(subscription)

    return subscription


@pytest.fixture(scope="function")
def login(driver, premium_subscription):
    """Standardized authentication for UI testing."""
    # Navigate to base URL
    driver.get(f"{BASE_URL}")

    # Check if already authenticated
    if "dashboard" in driver.current_url or "workspace" in driver.current_url:
        print("Already authenticated")
        return

    # Try the test authentication endpoint first (preferred method)
    try:
        test_auth_url = (
            f"{BASE_URL}/auth/test-auth?user=test-teacher&bypass_key={TEST_BYPASS_KEY}"
        )
        driver.get(test_auth_url)

        # Wait briefly for auth to process
        time.sleep(2)

        # Check if we're authenticated
        if "login" not in driver.current_url:
            print("Successfully authenticated via test endpoint")
            return
    except Exception as e:
        print(f"Test auth endpoint approach failed: {e}")

    # Fallback: Use localStorage and cookie injection
    print("Using fallback authentication method")
    driver.get(f"{BASE_URL}")

    # Set localStorage tokens
    driver.execute_script(
        f"""
        localStorage.setItem('auth_token', 'mock_valid_token');
        localStorage.setItem('user', JSON.stringify({TEST_USER}));
        """
    )

    # Set a session cookie
    driver.add_cookie(
        {"name": "session_token", "value": "test-session-token", "path": "/"}
    )

    # Refresh the page to apply the authentication
    driver.get(f"{BASE_URL}/dashboard")

    # Wait for the page to load
    time.sleep(2)

    # Verify we're authenticated
    if "login" in driver.current_url:
        pytest.fail("Authentication failed")

    print("Successfully authenticated via token injection")


@pytest.fixture(scope="function")
def wait_for_download(download_dir: Path):
    """Fixture to wait for a file to be downloaded."""

    def _wait_for_download(extension: str, timeout: int = 30) -> Optional[Path]:
        """
        Wait for a file with the given extension to be downloaded.

        Args:
            extension: The file extension to wait for (e.g., '.pdf')
            timeout: Maximum time to wait in seconds

        Returns:
            Path to the downloaded file or None if timeout is reached
        """
        print(f"Waiting for download with extension {extension} (timeout: {timeout}s)")
        print(f"Download directory: {download_dir}")

        # Get list of all files before download starts
        existing_files = set(download_dir.glob("*"))
        print(f"Found {len(existing_files)} existing files before download")

        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check every 0.5 seconds
            time.sleep(0.5)

            # Log progress every 5 seconds
            elapsed = time.time() - start_time
            if int(elapsed) % 5 == 0 and elapsed > 0 and elapsed % 5 < 0.5:
                print(f"Still waiting for download... ({int(elapsed)}s elapsed)")

            # Look for any new files
            current_files = set(download_dir.glob("*"))
            new_files = current_files - existing_files

            # Check if any of the new files match our extension
            matching_files = [f for f in new_files if f.name.endswith(extension)]

            if matching_files:
                # Wait a bit to ensure file is completely written
                time.sleep(1)

                # Get the most recently modified file
                newest_file = max(matching_files, key=lambda f: f.stat().st_mtime)

                # Check if file size is stable (not still being written)
                initial_size = newest_file.stat().st_size
                time.sleep(0.5)
                if newest_file.stat().st_size == initial_size and initial_size > 0:
                    print(
                        f"Download detected: {newest_file.name} (size: {newest_file.stat().st_size} bytes)"
                    )
                    return newest_file

        # Timeout reached, log all files in the directory for debugging
        print(
            f"Timeout reached ({timeout}s). No new files with extension {extension} found."
        )
        all_files = list(download_dir.glob("*"))
        if all_files:
            print(f"Files in download directory:")
            for file in all_files:
                print(
                    f"  - {file.name} (size: {file.stat().st_size} bytes, modified: {datetime.datetime.fromtimestamp(file.stat().st_mtime)})"
                )
        else:
            print("Download directory is empty")

        return None

    return _wait_for_download


class PDFAnalyzer:
    """Utility class for analyzing PDF files."""

    @staticmethod
    def extract_text(pdf_path: Path) -> str:
        """Extract text from a PDF file."""
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    @staticmethod
    def convert_to_images(pdf_path: Path) -> list[Image.Image]:
        """Convert PDF pages to images."""
        return convert_from_path(pdf_path)

    @staticmethod
    def analyze_whitespace(image: Image.Image) -> float:
        """Analyze the percentage of whitespace at the top of the image."""
        # Get the top 20% of the image
        width, height = image.size
        top_section = image.crop((0, 0, width, int(height * 0.2)))

        # Convert to grayscale
        gray = top_section.convert("L")

        # Count white pixels (threshold > 240)
        white_pixels = sum(1 for pixel in gray.getdata() if pixel > 240)
        total_pixels = top_section.width * top_section.height

        # Calculate percentage of white pixels
        return (white_pixels / total_pixels) * 100


@pytest.fixture(scope="session")
def pdf_analyzer():
    """Fixture for PDF analysis."""
    return PDFAnalyzer
