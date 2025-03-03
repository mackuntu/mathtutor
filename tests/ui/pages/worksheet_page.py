"""Worksheet generator page object for UI testing."""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from tests.ui.pages.base_page import BasePage


class WorksheetPage(BasePage):
    """Page object for the worksheet generator page."""

    # Locators
    CHILD_SELECT = (By.ID, "childSelect")
    COUNT_INPUT = (By.ID, "count")
    NUM_WORKSHEETS_INPUT = (By.ID, "num_worksheets")
    DIFFICULTY_SLIDER = (By.ID, "difficulty")
    GENERATE_BUTTON = (By.ID, "generateBtn")
    PREVIEW_BUTTON = (By.ID, "previewBtn")
    PREVIEW_BOX = (By.ID, "previewBox")
    LOADING_OVERLAY = (By.ID, "loading")

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:8080"):
        """Initialize the page object with a WebDriver instance."""
        super().__init__(driver, base_url)

    def open_worksheet_page(self):
        """Open the worksheet generator page."""
        self.open("")
        # Wait for redirect to complete if needed
        time.sleep(2)
        return self

    def select_child(self, child_name: str):
        """Select a child from the dropdown."""
        select = Select(self.wait_for_element(self.CHILD_SELECT))
        select.select_by_visible_text(child_name)
        # Wait for page to update based on child selection
        time.sleep(1)
        return self

    def set_problem_count(self, count: int):
        """Set the number of problems."""
        count_input = self.wait_for_element(self.COUNT_INPUT)
        count_input.clear()
        count_input.send_keys(str(count))
        return self

    def set_worksheet_count(self, count: int):
        """Set the number of worksheets."""
        worksheets_input = self.wait_for_element(self.NUM_WORKSHEETS_INPUT)
        worksheets_input.clear()
        worksheets_input.send_keys(str(count))
        return self

    def set_difficulty(self, difficulty: float):
        """Set the difficulty level (0.0 to 1.0)."""
        # JavaScript is needed to set the value of a range input
        self.driver.execute_script(
            f"document.getElementById('difficulty').value = {difficulty};"
        )
        return self

    def click_generate_button(self):
        """Click the generate button."""
        # Use JavaScript to click the button to avoid ElementClickInterceptedException
        generate_button = self.wait_for_clickable(self.GENERATE_BUTTON)
        self.driver.execute_script("arguments[0].click();", generate_button)
        return self

    def click_preview_button(self):
        """Click the preview button."""
        # Use JavaScript to click the button to avoid ElementClickInterceptedException
        preview_button = self.wait_for_clickable(self.PREVIEW_BUTTON)
        self.driver.execute_script("arguments[0].click();", preview_button)
        return self

    def wait_for_preview(self):
        """Wait for the preview to load."""
        # Wait for loading overlay to appear
        # self.wait_for_visibility(self.LOADING_OVERLAY)
        # Wait for loading overlay to disappear
        # self.wait_for_invisibility(self.LOADING_OVERLAY)
        # Wait for preview box to be visible
        self.wait_for_visibility(self.PREVIEW_BOX)
        return self

    def wait_for_generation_complete(self):
        """Wait for worksheet generation to complete."""
        # Wait for loading overlay to appear
        # self.wait_for_visibility(self.LOADING_OVERLAY)
        # Wait for loading overlay to disappear
        self.wait_for_invisibility(self.LOADING_OVERLAY)
        return self

    def is_generate_button_enabled(self):
        """Check if the generate button is enabled."""
        return self.wait_for_element(self.GENERATE_BUTTON).is_enabled()

    def get_preview_content(self):
        """Get the content of the preview box."""
        return self.wait_for_element(self.PREVIEW_BOX).text
