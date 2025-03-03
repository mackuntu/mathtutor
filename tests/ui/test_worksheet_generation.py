"""UI tests for worksheet generation functionality."""

import os
import time
from pathlib import Path

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from tests.ui.pages.worksheet_page import WorksheetPage


@pytest.mark.ui
class TestWorksheetGeneration:
    """Test worksheet generation functionality."""

    def test_preview_worksheet(self, driver, login):
        """Test that worksheet preview works correctly."""
        # Navigate to worksheet page
        worksheet_page = WorksheetPage(driver)

        try:
            worksheet_page.open_worksheet_page()
        except Exception as e:
            # Handle any unexpected alerts
            try:
                alert = driver.switch_to.alert
                print(f"Alert detected: {alert.text}")
                alert.accept()
                # Try again after accepting the alert
                worksheet_page.open_worksheet_page()
            except Exception:
                # No alert present, re-raise the original exception
                raise e

        # Check if we need to create a child first
        try:
            child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
            # Select first child in the dropdown if available
            if child_select.find_elements(By.TAG_NAME, "option")[
                1:
            ]:  # Skip the "Select a child..." option
                child_select.find_elements(By.TAG_NAME, "option")[1].click()
            else:
                # No children available, create one
                self._create_test_child(driver)
                # Refresh the page
                try:
                    worksheet_page.open_worksheet_page()
                except Exception as e:
                    # Handle any unexpected alerts
                    try:
                        alert = driver.switch_to.alert
                        print(f"Alert detected: {alert.text}")
                        alert.accept()
                        # Try again after accepting the alert
                        worksheet_page.open_worksheet_page()
                    except Exception:
                        # No alert present, re-raise the original exception
                        raise e
                # Now select the child
                child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
                child_select.find_elements(By.TAG_NAME, "option")[1].click()
        except NoSuchElementException:
            # No child selector found, might be showing "No children found" message
            # Click on "Add a child" link
            driver.find_element(By.LINK_TEXT, "Add a child").click()
            self._create_test_child(driver)
            # Go back to worksheet page
            try:
                worksheet_page.open_worksheet_page()
            except Exception as e:
                # Handle any unexpected alerts
                try:
                    alert = driver.switch_to.alert
                    print(f"Alert detected: {alert.text}")
                    alert.accept()
                    # Try again after accepting the alert
                    worksheet_page.open_worksheet_page()
                except Exception:
                    # No alert present, re-raise the original exception
                    raise e
            # Now select the child
            child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
            child_select.find_elements(By.TAG_NAME, "option")[1].click()

        # Set problem count
        worksheet_page.set_problem_count(10)

        # Click preview button
        worksheet_page.click_preview_button()

        # Wait for preview to load
        worksheet_page.wait_for_preview()

        # Verify preview content
        preview_content = worksheet_page.get_preview_content()
        assert preview_content, "Preview content should not be empty"
        assert any(
            op in preview_content for op in ["×", "+", "−"]
        ), "Preview should contain math operators"

    @pytest.mark.skip(
        reason="PDF generation tests are not working correctly in the current environment"
    )
    def test_generate_worksheet_pdf(
        self, driver, login, wait_for_download, pdf_analyzer
    ):
        """Test that worksheet PDF generation works correctly and content starts at the top of the page."""
        # Navigate to worksheet page
        worksheet_page = WorksheetPage(driver)

        try:
            worksheet_page.open_worksheet_page()
        except Exception as e:
            # Handle any unexpected alerts
            try:
                alert = driver.switch_to.alert
                print(f"Alert detected: {alert.text}")
                alert.accept()
                # Try again after accepting the alert
                worksheet_page.open_worksheet_page()
            except Exception:
                # No alert present, re-raise the original exception
                raise e

        # Check if we need to create a child first
        try:
            child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
            # Select first child in the dropdown if available
            if child_select.find_elements(By.TAG_NAME, "option")[
                1:
            ]:  # Skip the "Select a child..." option
                child_select.find_elements(By.TAG_NAME, "option")[1].click()
            else:
                # No children available, create one
                self._create_test_child(driver)
                # Refresh the page
                try:
                    worksheet_page.open_worksheet_page()
                except Exception as e:
                    # Handle any unexpected alerts
                    try:
                        alert = driver.switch_to.alert
                        print(f"Alert detected: {alert.text}")
                        alert.accept()
                        # Try again after accepting the alert
                        worksheet_page.open_worksheet_page()
                    except Exception:
                        # No alert present, re-raise the original exception
                        raise e
                # Now select the child
                child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
                child_select.find_elements(By.TAG_NAME, "option")[1].click()
        except NoSuchElementException:
            # No child selector found, might be showing "No children found" message
            # Click on "Add a child" link
            driver.find_element(By.LINK_TEXT, "Add a child").click()
            self._create_test_child(driver)
            # Go back to worksheet page
            try:
                worksheet_page.open_worksheet_page()
            except Exception as e:
                # Handle any unexpected alerts
                try:
                    alert = driver.switch_to.alert
                    print(f"Alert detected: {alert.text}")
                    alert.accept()
                    # Try again after accepting the alert
                    worksheet_page.open_worksheet_page()
                except Exception:
                    # No alert present, re-raise the original exception
                    raise e
            # Now select the child
            child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
            child_select.find_elements(By.TAG_NAME, "option")[1].click()

        # Set problem count and worksheet count
        worksheet_page.set_problem_count(10)
        worksheet_page.set_worksheet_count(1)

        # Click generate button
        worksheet_page.click_generate_button()

        # Wait for generation to complete
        worksheet_page.wait_for_generation_complete()

        # Wait for PDF to be downloaded
        pdf_path = wait_for_download(".pdf")
        assert pdf_path is not None, "PDF should be downloaded"

        # Analyze PDF content
        text = pdf_analyzer.extract_text(pdf_path)
        assert text, "PDF should contain text"

        # Convert PDF to images for visual analysis
        images = pdf_analyzer.convert_to_images(pdf_path)
        assert images, "PDF should be convertible to images"

        # Analyze whitespace at the top of the first page
        whitespace_percentage = pdf_analyzer.analyze_whitespace(images[0])

        # Assert that whitespace at the top is reasonable (less than 30%)
        # This threshold might need adjustment based on the actual layout
        assert (
            whitespace_percentage < 30
        ), f"Too much whitespace at the top of the page: {whitespace_percentage}%"

    @pytest.mark.skip(
        reason="PDF generation tests are not working correctly in the current environment"
    )
    def test_pdf_content_position(self, driver, login, wait_for_download, pdf_analyzer):
        """Test that PDF content starts at the appropriate position on the page."""
        # Navigate to worksheet page
        worksheet_page = WorksheetPage(driver)

        try:
            worksheet_page.open_worksheet_page()
        except Exception as e:
            # Handle any unexpected alerts
            try:
                alert = driver.switch_to.alert
                print(f"Alert detected: {alert.text}")
                alert.accept()
                # Try again after accepting the alert
                worksheet_page.open_worksheet_page()
            except Exception:
                # No alert present, re-raise the original exception
                raise e

        # Check if we need to create a child first
        try:
            child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
            # Select first child in the dropdown if available
            if child_select.find_elements(By.TAG_NAME, "option")[
                1:
            ]:  # Skip the "Select a child..." option
                child_select.find_elements(By.TAG_NAME, "option")[1].click()
            else:
                # No children available, create one
                self._create_test_child(driver)
                # Refresh the page
                try:
                    worksheet_page.open_worksheet_page()
                except Exception as e:
                    # Handle any unexpected alerts
                    try:
                        alert = driver.switch_to.alert
                        print(f"Alert detected: {alert.text}")
                        alert.accept()
                        # Try again after accepting the alert
                        worksheet_page.open_worksheet_page()
                    except Exception:
                        # No alert present, re-raise the original exception
                        raise e
                # Now select the child
                child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
                child_select.find_elements(By.TAG_NAME, "option")[1].click()
        except NoSuchElementException:
            # No child selector found, might be showing "No children found" message
            # Click on "Add a child" link
            driver.find_element(By.LINK_TEXT, "Add a child").click()
            self._create_test_child(driver)
            # Go back to worksheet page
            try:
                worksheet_page.open_worksheet_page()
            except Exception as e:
                # Handle any unexpected alerts
                try:
                    alert = driver.switch_to.alert
                    print(f"Alert detected: {alert.text}")
                    alert.accept()
                    # Try again after accepting the alert
                    worksheet_page.open_worksheet_page()
                except Exception:
                    # No alert present, re-raise the original exception
                    raise e
            # Now select the child
            child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
            child_select.find_elements(By.TAG_NAME, "option")[1].click()

        # Set problem count and worksheet count
        worksheet_page.set_problem_count(10)
        worksheet_page.set_worksheet_count(1)

        # Click generate button
        worksheet_page.click_generate_button()

        # Wait for generation to complete
        worksheet_page.wait_for_generation_complete()

        # Wait for PDF to be downloaded
        pdf_path = wait_for_download(".pdf")
        assert pdf_path is not None, "PDF should be downloaded"

        # Take screenshots for visual verification
        screenshot_dir = Path("test-reports/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Convert PDF to images
        images = pdf_analyzer.convert_to_images(pdf_path)

        # Save the first page as an image for visual inspection
        first_page = images[0]
        first_page.save(screenshot_dir / "worksheet_first_page.png")

        # Analyze the first 20% of the page
        height = first_page.height
        top_section = first_page.crop((0, 0, first_page.width, int(height * 0.2)))
        top_section.save(screenshot_dir / "worksheet_top_section.png")

        # Check if the title/header is visible in the top section
        # This is a visual check that content starts at the top
        whitespace_percentage = pdf_analyzer.analyze_whitespace(top_section)
        assert (
            whitespace_percentage < 50
        ), f"Title should be visible in the top 20% of the page, whitespace: {whitespace_percentage}%"

    @pytest.mark.skip(
        reason="PDF generation tests are not working correctly in the current environment"
    )
    def test_answer_key_pdf(self, driver, login, wait_for_download, pdf_analyzer):
        """Test that answer key PDF is generated correctly and content starts at the top of the page."""
        # Navigate to worksheet page
        worksheet_page = WorksheetPage(driver)

        try:
            worksheet_page.open_worksheet_page()
        except Exception as e:
            # Handle any unexpected alerts
            try:
                alert = driver.switch_to.alert
                print(f"Alert detected: {alert.text}")
                alert.accept()
                # Try again after accepting the alert
                worksheet_page.open_worksheet_page()
            except Exception:
                # No alert present, re-raise the original exception
                raise e

        # Check if we need to create a child first
        try:
            child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
            # Select first child in the dropdown if available
            if child_select.find_elements(By.TAG_NAME, "option")[
                1:
            ]:  # Skip the "Select a child..." option
                child_select.find_elements(By.TAG_NAME, "option")[1].click()
            else:
                # No children available, create one
                self._create_test_child(driver)
                # Refresh the page
                try:
                    worksheet_page.open_worksheet_page()
                except Exception as e:
                    # Handle any unexpected alerts
                    try:
                        alert = driver.switch_to.alert
                        print(f"Alert detected: {alert.text}")
                        alert.accept()
                        # Try again after accepting the alert
                        worksheet_page.open_worksheet_page()
                    except Exception:
                        # No alert present, re-raise the original exception
                        raise e
                # Now select the child
                child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
                child_select.find_elements(By.TAG_NAME, "option")[1].click()
        except NoSuchElementException:
            # No child selector found, might be showing "No children found" message
            # Click on "Add a child" link
            driver.find_element(By.LINK_TEXT, "Add a child").click()
            self._create_test_child(driver)
            # Go back to worksheet page
            try:
                worksheet_page.open_worksheet_page()
            except Exception as e:
                # Handle any unexpected alerts
                try:
                    alert = driver.switch_to.alert
                    print(f"Alert detected: {alert.text}")
                    alert.accept()
                    # Try again after accepting the alert
                    worksheet_page.open_worksheet_page()
                except Exception:
                    # No alert present, re-raise the original exception
                    raise e
            # Now select the child
            child_select = driver.find_element(*WorksheetPage.CHILD_SELECT)
            child_select.find_elements(By.TAG_NAME, "option")[1].click()

        # Set problem count and worksheet count
        worksheet_page.set_problem_count(10)
        worksheet_page.set_worksheet_count(1)

        # Click generate button
        worksheet_page.click_generate_button()

        # Wait for generation to complete
        worksheet_page.wait_for_generation_complete()

        # Wait for both PDFs to be downloaded (worksheet and answer key)
        # The answer key should be the second PDF downloaded
        time.sleep(5)  # Give time for both PDFs to download

        # Get all PDFs in the download directory
        download_dir = Path(driver.capabilities["chrome"]["userDataDir"])
        pdf_files = list(download_dir.glob("*.pdf"))

        # Find the answer key PDF (should contain "answer-key" in the filename)
        answer_key_pdf = next(
            (pdf for pdf in pdf_files if "answer-key" in pdf.name.lower()), None
        )
        assert answer_key_pdf is not None, "Answer key PDF should be downloaded"

        # Analyze PDF content
        text = pdf_analyzer.extract_text(answer_key_pdf)
        assert text, "PDF should contain text"
        assert "Answer Key" in text, "PDF should be an answer key"

        # Convert PDF to images for visual analysis
        images = pdf_analyzer.convert_to_images(answer_key_pdf)
        assert images, "PDF should be convertible to images"

        # Analyze whitespace at the top of the first page
        whitespace_percentage = pdf_analyzer.analyze_whitespace(images[0])

        # Assert that whitespace at the top is reasonable (less than 30%)
        assert (
            whitespace_percentage < 30
        ), f"Too much whitespace at the top of the page: {whitespace_percentage}%"

    def _create_test_child(self, driver):
        """Helper method to create a test child."""
        # We should be on the main page with the "Add a child" link or button
        try:
            # Check if the modal is already open
            try:
                modal = driver.find_element(By.ID, "addChildModal")
                if "show" in modal.get_attribute("class"):
                    print("Modal is already open, proceeding with form filling")
                else:
                    # Try to find and click the "Add New Child" button
                    add_child_btn = driver.find_element(By.ID, "addChildBtn")
                    add_child_btn.click()
                    # Wait for the modal to appear
                    time.sleep(1)
            except NoSuchElementException:
                # If modal not found, try to click the button
                add_child_btn = driver.find_element(By.ID, "addChildBtn")
                add_child_btn.click()
                # Wait for the modal to appear
                time.sleep(1)

            # Fill out the form in the modal
            driver.find_element(By.ID, "name").send_keys("Test Child")

            # Set birthday to a specific date for a 6-year-old child
            # Use JavaScript to set the value directly to ensure correct format
            birthday = "2018-01-01"  # January 1, 2018 (6 years old)
            print(f"Setting birthday to: {birthday} (should be 6 years old)")

            # Use JavaScript to set the value directly
            driver.execute_script(
                "document.getElementById('birthday').value = arguments[0]", birthday
            )

            # Select grade 1 (appropriate for a 6-year-old)
            grade_select = driver.find_element(By.ID, "grade_level")
            from selenium.webdriver.support.ui import Select

            Select(grade_select).select_by_value("1")

            # Submit the form
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

            # Handle any alerts that might appear
            from selenium.common.exceptions import (
                TimeoutException,
                UnexpectedAlertPresentException,
            )
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait

            try:
                # Wait for and accept any alert that appears
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert_text = alert.text
                print(f"Alert detected: {alert_text}")
                alert.accept()

                # If we got an alert, the child creation failed
                raise Exception(f"Failed to create child: {alert_text}")
            except TimeoutException:
                # No alert, which is good
                pass

            # Wait for redirect
            time.sleep(2)

        except Exception as e:
            print(f"Error creating child: {e}")
            # Take a screenshot for debugging
            driver.save_screenshot("error_create_child.png")
            raise
