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

    # Past worksheets page locators
    PAST_WORKSHEETS_LINK = (By.LINK_TEXT, "Past Worksheets")
    DELETE_BUTTONS = (By.CSS_SELECTOR, "button.btn-danger[onclick*='deleteWorksheet']")
    WORKSHEET_CHECKBOXES = (By.CSS_SELECTOR, ".worksheet-checkbox")
    SELECT_ALL_CHECKBOX = (By.ID, "select-all")
    BULK_DELETE_BUTTON = (By.ID, "bulk-delete")
    WORKSHEET_ROWS = (By.CSS_SELECTOR, "tbody tr")

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:8080"):
        """Initialize the page object with a WebDriver instance."""
        super().__init__(driver, base_url)

    def open_worksheet_page(self):
        """Open the worksheet generator page."""
        self.open("")
        # Wait for redirect to complete if needed
        time.sleep(2)
        return self

    def open_worksheet_page_test_mode(self):
        """Open the worksheet generator page in test mode for PDF testing."""
        self.open("?test_mode=true")
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
        try:
            # Wait for loading overlay to disappear
            self.wait_for_invisibility(self.LOADING_OVERLAY)
            return self
        except Exception as e:
            # Check if there's an alert present
            try:
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                print(f"Alert detected during generation: {alert_text}")
                # Accept the alert
                alert.accept()
                # Re-raise the original exception with more context
                raise Exception(f"Generation failed with alert: {alert_text}") from e
            except Exception as alert_error:
                if "no such alert" not in str(alert_error).lower():
                    # If there was some other error handling the alert, log it
                    print(f"Error handling alert: {alert_error}")
                # Re-raise the original exception
                raise e

    def is_generate_button_enabled(self):
        """Check if the generate button is enabled."""
        return self.wait_for_element(self.GENERATE_BUTTON).is_enabled()

    def get_preview_content(self):
        """Get the content of the preview box."""
        return self.wait_for_element(self.PREVIEW_BOX).text

    def open_past_worksheets_page(self, child_id=None):
        """Open the past worksheets page for a specific child."""
        if child_id:
            print(f"Navigating directly to past worksheets for child ID: {child_id}")
            self.open(f"/worksheets/past/{child_id}")
        else:
            # Try to find the Past Worksheets link and click it
            try:
                print("Trying to find and click the Past Worksheets link")
                past_worksheets_link = self.wait_for_clickable(
                    self.PAST_WORKSHEETS_LINK
                )
                past_worksheets_link.click()
            except Exception as e:
                print(f"Error finding Past Worksheets link: {e}")
                # If link not found, try to navigate directly to the first child's past worksheets
                print("Attempting to navigate to /worksheets/past")
                self.open("/worksheets/past")

        # Wait for the page to load
        time.sleep(2)
        print(f"Current URL after navigation: {self.driver.current_url}")
        return self

    def get_worksheet_count(self):
        """Get the number of worksheets displayed in the table."""
        rows = self.driver.find_elements(*self.WORKSHEET_ROWS)
        return len(rows)

    def delete_first_worksheet(self):
        """Delete the first worksheet in the list."""
        # Get initial count
        initial_count = self.get_worksheet_count()
        print(f"Initial worksheet count before deletion: {initial_count}")

        # Find all delete buttons
        delete_buttons = self.driver.find_elements(*self.DELETE_BUTTONS)
        if not delete_buttons:
            raise Exception("No delete buttons found")

        print(f"Found {len(delete_buttons)} delete buttons")

        # Get the first delete button and ensure it's visible
        delete_button = delete_buttons[0]
        print(f"Delete button class: {delete_button.get_attribute('class')}")
        print(f"Delete button text: {delete_button.text}")
        print(f"Delete button onclick: {delete_button.get_attribute('onclick')}")

        # Set up a confirm handler to automatically accept the confirmation
        self.driver.execute_script("window.confirm = function() { return true; }")

        # Try to click using different methods
        try:
            # Method 1: Direct click
            print("Trying direct click")
            delete_button.click()
        except Exception as e:
            print(f"Direct click failed: {e}")
            try:
                # Method 2: JavaScript click
                print("Trying JavaScript click")
                self.driver.execute_script("arguments[0].click();", delete_button)
            except Exception as e:
                print(f"JavaScript click failed: {e}")
                try:
                    # Method 3: Get the worksheet ID and call the delete API directly
                    print("Trying to extract worksheet ID and call API directly")
                    onclick_attr = delete_button.get_attribute("onclick")
                    if onclick_attr and "deleteWorksheet" in onclick_attr:
                        # Extract the worksheet ID from the onclick attribute
                        # Format is typically: deleteWorksheet('some-id-here')
                        import re

                        match = re.search(r"deleteWorksheet\('([^']+)'\)", onclick_attr)
                        if match:
                            worksheet_id = match.group(1)
                            print(f"Extracted worksheet ID: {worksheet_id}")
                            # Call the delete API directly
                            self.driver.execute_script(
                                f"deleteWorksheet('{worksheet_id}')"
                            )
                        else:
                            print(
                                "Could not extract worksheet ID from onclick attribute"
                            )
                except Exception as e:
                    print(f"API call failed: {e}")

        # Wait for the page to reload
        print("Waiting for page to reload after deletion")
        time.sleep(5)  # Increase wait time to ensure page reloads

        # Get the new count
        new_count = self.get_worksheet_count()
        print(f"New worksheet count after deletion: {new_count}")

        # Return the initial count for verification
        return initial_count

    def bulk_delete_worksheets(self, count=2):
        """Select and delete multiple worksheets."""
        # Get initial count
        initial_count = self.get_worksheet_count()
        print(f"Initial worksheet count before bulk deletion: {initial_count}")

        if initial_count < 1:
            raise Exception(f"No worksheets to delete. Found {initial_count}")

        # Use the select all checkbox instead of individual checkboxes
        print("Clicking the select all checkbox")
        select_all = self.wait_for_clickable(self.SELECT_ALL_CHECKBOX)
        self.driver.execute_script("arguments[0].click();", select_all)

        # Verify checkboxes are selected
        checkboxes = self.driver.find_elements(*self.WORKSHEET_CHECKBOXES)
        print(f"Found {len(checkboxes)} checkboxes")
        for i in range(min(3, len(checkboxes))):
            print(
                f"Checking if checkbox {i + 1} is selected"
            )  # Fixed whitespace around + operator
            is_selected = self.driver.execute_script(
                "return arguments[0].checked;", checkboxes[i]
            )
            print(
                f"Checkbox {i + 1} selected status: {is_selected}"
            )  # Fixed whitespace around + operator

        # Set up a confirm handler to automatically accept the confirmation
        self.driver.execute_script("window.confirm = function() { return true; }")

        # Click the bulk delete button
        print("Clicking the bulk delete button")
        bulk_delete_button = self.wait_for_clickable(self.BULK_DELETE_BUTTON)
        self.driver.execute_script("arguments[0].click();", bulk_delete_button)

        # Wait for the page to reload
        print("Waiting for page to reload after bulk deletion")
        time.sleep(5)  # Increase wait time to ensure page reloads completely

        # Get the new count
        new_count = self.get_worksheet_count()
        print(f"New worksheet count after bulk deletion: {new_count}")

        # Return the initial count for verification
        return initial_count
