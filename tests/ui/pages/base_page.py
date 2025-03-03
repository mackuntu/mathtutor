"""Base page object for UI testing."""

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """Base class for all page objects."""

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:8080"):
        """Initialize the page object with a WebDriver instance."""
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 10)

    def open(self, url_path: str = ""):
        """Open a page at the specified URL path."""
        self.driver.get(f"{self.base_url}/{url_path}")
        return self

    def wait_for_element(self, locator, timeout: int = 10) -> WebElement:
        """Wait for an element to be present and return it."""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def wait_for_clickable(self, locator, timeout: int = 10) -> WebElement:
        """Wait for an element to be clickable and return it."""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )

    def wait_for_visibility(self, locator, timeout: int = 10) -> WebElement:
        """Wait for an element to be visible and return it."""
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_for_invisibility(self, locator, timeout: int = 10) -> bool:
        """Wait for an element to be invisible."""
        return WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(locator)
        )

    def wait_for_url_contains(self, text: str, timeout: int = 10) -> bool:
        """Wait for the URL to contain the specified text."""
        return WebDriverWait(self.driver, timeout).until(EC.url_contains(text))

    def wait_for_text_in_element(self, locator, text: str, timeout: int = 10) -> bool:
        """Wait for the specified text to be present in the element."""
        return WebDriverWait(self.driver, timeout).until(
            EC.text_to_be_present_in_element(locator, text)
        )

    def take_screenshot(self, filename: str):
        """Take a screenshot and save it to the specified file."""
        self.driver.save_screenshot(filename)
