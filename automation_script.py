# Complete Automation Script with Real UK Timing System
import pandas as pd
import requests
from io import StringIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import time
import random
import json
import os
import sys
from functools import wraps
import pytz

# ============================================================================
# REAL-TIME UK TIMING FUNCTIONS
# ============================================================================

def get_uk_time():
    """Get current UK time (handles BST/GMT automatically)"""
    uk_tz = pytz.timezone('Europe/London')
    return datetime.now(uk_tz)

def calculate_realistic_times():
    """
    Calculate realistic start and end times based on current UK time.
    End time = now (when we save)
    Start time = end time minus 16 minutes (+/- 30 seconds)
    
    Returns:
        tuple: (start_time_str, end_time_str) in format 'dd/mm/yyyy HH:MM:SS'
    """
    # End time is current UK time (when we save)
    end_time = get_uk_time()
    
    # Start time is 16 minutes ago, plus/minus 30 seconds for realism
    random_seconds = random.randint(-30, 30)  # +/- 30 seconds variation
    minutes_ago = 16 * 60 + random_seconds  # 16 minutes in seconds, plus variation
    
    start_time = end_time - timedelta(seconds=minutes_ago)
    
    # Format both times
    start_time_str = start_time.strftime('%d/%m/%Y %H:%M:%S')
    end_time_str = end_time.strftime('%d/%m/%Y %H:%M:%S')
    
    print(f"🕐 Calculated realistic times:")
    print(f"   📅 Start Time: {start_time_str}")
    print(f"   🏁 End Time: {end_time_str}")
    print(f"   ⏱️  Duration: {minutes_ago/60:.1f} minutes")
    
    return start_time_str, end_time_str

# ============================================================================
# GITHUB ACTIONS SPECIFIC SETUP
# ============================================================================

def setup_chrome_for_github():
    """Setup Chrome for GitHub Actions environment"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # INCREASED WINDOW SIZE
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--force-device-scale-factor=1")
    chrome_options.add_argument("--high-dpi-support=1")
    
    # Additional options to help with rendering
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Set window size again after creation
    driver.set_window_size(1920, 1080)
    
    # Execute JavaScript to ensure viewport is correct
    driver.execute_script("window.moveTo(0, 0);")
    driver.execute_script("window.resizeTo(1920, 1080);")
    
    return driver

def capture_screenshot(driver, filename):
    """Captures a screenshot with sanitized filename for GitHub Actions"""
    try:
        # Sanitize filename by removing/replacing invalid characters
        invalid_chars = '<>:"|?*\r\n\\/'
        sanitized_filename = filename
        
        for char in invalid_chars:
            sanitized_filename = sanitized_filename.replace(char, '_')
        
        # Remove multiple underscores and clean up
        while '__' in sanitized_filename:
            sanitized_filename = sanitized_filename.replace('__', '_')
        
        # Ensure it ends with .png
        if not sanitized_filename.endswith('.png'):
            sanitized_filename += '.png'
        
        # Limit filename length to avoid issues
        if len(sanitized_filename) > 100:
            sanitized_filename = sanitized_filename[:96] + '.png'
        
        driver.save_screenshot(sanitized_filename)
        print(f"Screenshot saved: {sanitized_filename}")
    except Exception as e:
        print(f"Could not save screenshot: {e}")

# ============================================================================
# YOUR ORIGINAL FUNCTIONS FROM COLAB BLOCKS
# ============================================================================

def load_data_from_google_sheets(url, columns, row_index=0):
    """Load and process data from a Google Sheets URL."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))

            if 'Project Number' in df.columns:
                df['Project Number'] = df['Project Number'].ffill()
                df['Project Number'] = df['Project Number'].astype(int)
                print("Forward-filled and converted 'Project Number' column to integers.")
            else:
                print("Error: 'Project Number' column not found.")

            print("Data loaded successfully.")
            print("First few rows of the processed data:\n", df.head())
            return df
        else:
            print(f"Error: Failed to fetch Google Sheets data. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while extracting data: {e}")
        return None

def login(driver, username, password):
    """Perform the login process on the specified driver."""
    try:
        driver.get("https://crucial-enviro.alphatracker.online/")

        username_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "LOGIN_UX.V.R1.USERID"))
        )
        password_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "LOGIN_UX.V.R1.PASSWORD"))
        )
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "LOGIN_UX.V.R1.LOGIN_BTN"))
        )

        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)
        submit_button.click()

        WebDriverWait(driver, 10).until(EC.url_contains("TabbedUI_MainMenu"))
        print(f"Login successful for user '{username}'!")
        capture_screenshot(driver, f"screenshot_after_login_{username}.png")
        return True

    except Exception as e:
        print(f"Error occurred during login for user '{username}': {e}")
        capture_screenshot(driver, f"login_error_{username}.png")
        return False

def click_lab_button(driver):
    try:
        lab_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "tb1FRAME_12.A"))
        )
        lab_button.click()
        print("Lab button clicked successfully!")
        return True
    except TimeoutException:
        print("Timeout: Lab button not clickable or not found.")
        return False

def click_lab_project_list_button(driver):
    try:
        lab_project_list_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Lab Project List')]"))
        )
        lab_project_list_button.click()
        print("Lab Project List button clicked successfully!")
        return True
    except TimeoutException:
        print("Timeout: Lab Project List button not clickable or not found.")
        return False

def input_project_number(driver, project_number):
    """Inputs the project number into the appropriate field."""
    try:
        project_number_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "TBI_LAB_PROJEC_162148FIEL.S.PROJECT_NUMBER"))
        )

        project_number_field.clear()
        project_number = str(int(float(project_number)))
        project_number_field.send_keys(project_number)
        print(f"Project number {project_number} input successful!")
        capture_screenshot(driver, "project_number_input.png")
        return True
    except TimeoutException:
        print("Error: Could not find the project number input field.")
        capture_screenshot(driver, "project_number_input_error.png")
        return False
    except Exception as e:
        print(f"An error occurred while inputting project number: {str(e)}")
        capture_screenshot(driver, "project_number_input_error.png")
        return False

def press_enter_or_search_on_project_number(driver, project_number):
    """Clicks the Search button or presses Enter on the project number field."""
    max_retries = 3
    delay = 5

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}: Clearing previous search results...")
            clear_search_criteria(driver)

            print("Attempting to click the Search button...")
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "TBI_LAB_PROJEC_162148FIEL.SEARCHBTN"))
            )
            search_button.click()
            print("Search button clicked.")

            WebDriverWait(driver, 10).until(
                EC.text_to_be_present_in_element(
                    (By.ID, "TBI_LAB_PROJEC_162148FIEL.V.R1.PROJECT_NUMBER"), str(project_number)
                )
            )
            print(f"Project number updated successfully: {project_number}")
            return True

        except TimeoutException:
            try:
                project_number_field = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "TBI_LAB_PROJEC_162148FIEL.S.PROJECT_NUMBER"))
                )
                project_number_field.click()
                project_number_field.clear()
                project_number_field.send_keys(str(project_number))
                project_number_field.send_keys(Keys.RETURN)
                print("Pressed Enter on the project number field.")

                WebDriverWait(driver, 10).until(
                    EC.text_to_be_present_in_element(
                        (By.ID, "TBI_LAB_PROJEC_162148FIEL.V.R1.PROJECT_NUMBER"), str(project_number)
                    )
                )
                print(f"Project number updated successfully: {project_number}")
                return True

            except TimeoutException:
                print(f"Attempt {attempt}: Enter key press did not update. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    print("Failed to update the project number after all retries.")
    return False

def verify_project_numbers(driver):
    """Verifies that the project number in the input field matches the one in the span element."""
    try:
        span_project_number = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "TBI_LAB_PROJEC_162148FIEL.V.R1.PROJECT_NUMBER"))
        )
        span_project_number_text = span_project_number.text.strip().split('-')[-1]

        input_project_number = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "TBI_LAB_PROJEC_162148FIEL.S.PROJECT_NUMBER"))
        )
        input_project_number_value = input_project_number.get_attribute("value").strip()

        print(f"Span Project Number Text (cleaned): {span_project_number_text}")
        print(f"Input Project Number Value: {input_project_number_value}")

        if span_project_number_text != input_project_number_value:
            print("Error: The project numbers do not match.")
            raise ValueError(f"Project numbers mismatch: Span '{span_project_number_text}' vs Input '{input_project_number_value}'")

        print("Project numbers match. Continuing execution.")
        screenshot_filename = f"project_numbers_match_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"
        capture_screenshot(driver, screenshot_filename)

    except TimeoutException:
        print("Error: Could not locate one or both project number elements.")
    except ValueError as ve:
        print(f"Verification failed: {ve}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during verification: {str(e)}")

def click_view_fibre_analysis_button(driver):
    """Locates and clicks the 'View Fibre Analysis' button."""
    try:
        fibre_analysis_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "TBI_LAB_PROJEC_162148FIEL.V.R1._UNBOUND_BUTTON_1"))
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", fibre_analysis_button)
        capture_screenshot(driver, "before_click_view_fibre_analysis_button.png")
        fibre_analysis_button.click()
        print("Clicked the 'View Fibre Analysis' button successfully!")

        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), 'Creating Fibre Analysis records')]"))
        )
        print("Loading pop-up detected.")

        WebDriverWait(driver, 30).until_not(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(text(), 'Creating Fibre Analysis records')]"))
        )
        print("Loading pop-up dismissed.")

        capture_screenshot(driver, "after_loading_fibre_analysis.png")
        return True

    except TimeoutException:
        print("Timeout: Loading did not finish in the expected time.")
        capture_screenshot(driver, "timeout_loading_fibre_analysis.png")
        return False
    except Exception as e:
        print(f"An error occurred while clicking 'View Fibre Analysis' button: {e}")
        capture_screenshot(driver, "error_clicking_view_fibre_analysis_button.png")
        return False

def clear_search_criteria(driver):
    try:
        clear_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Clear Search Criteria"))
        )
        clear_button.click()
        print("Cleared previous search criteria.")
        return True
    except TimeoutException:
        print("No 'Clear Search Criteria' button found. Continuing.")
        return False

def wait_for_no_overlay(driver, timeout=10):
    """Waits until overlays disappear."""
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.ID, "AUILockUIPage"))
        )
        print("Overlay removed.")
        return True
    except TimeoutException:
        print("Overlay did not disappear.")
        return False

# ============================================================================
# POPUP HANDLING AND SAMPLE PROCESSING FUNCTIONS
# ============================================================================

def handle_popup_ok_button(driver):
    """Detects and clicks the 'OK' button on a popup if it appears."""
    try:
        ok_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "A5dlg1.BUTTON.ok"))
        )
        ok_button.click()
        print("Popup 'OK' button clicked successfully.")
        return True
    except TimeoutException:
        return False
    except Exception as e:
        print(f"An error occurred while handling popup: {e}")
        return False

def handle_popup(func):
    """Decorator to handle popup after executing a function."""
    @wraps(func)
    def wrapper(driver, *args, **kwargs):
        try:
            result = func(driver, *args, **kwargs)
            
            if handle_popup_ok_button(driver):
                print(f"Popup handled after executing {func.__name__}.")
                # Don't call save button here - just return the original result
                return result
            
            return result
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
            return False
    return wrapper

def normalize_sample_number(sample_no):
    """Convert sample number to integer, handling various input types."""
    try:
        # Handle string, float, or int input
        return int(float(str(sample_no).strip()))
    except (ValueError, TypeError):
        print(f"Warning: Could not convert sample number '{sample_no}' to integer")
        return None

def click_element_safely(driver, element, element_name="element"):
    """
    Tries to click an element safely, using JavaScript if regular click fails.
    """
    try:
        # First try regular click
        element.click()
        return True
    except ElementClickInterceptedException:
        print(f"Regular click intercepted for {element_name}, trying JavaScript click...")
        try:
            # If regular click fails, use JavaScript
            driver.execute_script("arguments[0].click();", element)
            print(f"JavaScript click successful for {element_name}")
            return True
        except Exception as e:
            print(f"JavaScript click also failed for {element_name}: {e}")
            return False
    except Exception as e:
        print(f"Click failed for {element_name}: {e}")
        return False


def click_sample_row_with_next_button(driver, sample_no, is_new_project=False):
    """
    Navigates to the correct sample using the Next button.
    When the page loads, Sample 1 is automatically selected.
    Each click of Next moves to the next sample (not the next page).
    
    Args:
        driver: Selenium webdriver
        sample_no: Sample number to navigate to (integer)
        is_new_project: If True, first navigate back to sample 1
    """
    try:
        # If this is a new project, first go back to sample 1
        if is_new_project and sample_no != 1:
            if not navigate_to_first_sample(driver):
                print("❌ Failed to navigate to first sample for new project")
                return False
        
        # Calculate how many Next clicks we need
        # Sample 1: 0 clicks (already selected)
        # Sample 2: 1 click
        # Sample 3: 2 clicks, etc.
        clicks_required = sample_no - 1
        
        print(f"📍 Navigating to Sample No. {sample_no}")
        print(f"   Next clicks required: {clicks_required}")

        # If sample 1, it's already selected - no clicks needed
        if clicks_required == 0:
            print(f"✅ Sample 1 is already selected by default")
            capture_screenshot(driver, f"sample_{sample_no}_selected.png")
            
            # Wait a moment and verify
            time.sleep(2)
            return verify_correct_sample_loaded(driver, sample_no)

        # For samples 2+, click Next the required number of times
        for click_num in range(clicks_required):
            print(f"  Clicking 'Next' button ({click_num + 1}/{clicks_required})...")
            try:
                # Wait for any overlays to disappear first
                wait_for_no_overlay(driver)
                
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.FOOTER_CONTROLS.Next.ICON"))
                )
                
                # Scroll into view if needed
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
                time.sleep(1)
                
                # Try to click using our safe click method
                if click_element_safely(driver, next_button, "Next button"):
                    print(f"  ✓ Clicked 'Next' button successfully.")
                else:
                    # If both click methods fail, try one more approach
                    print("  Trying alternative click method...")
                    actions = ActionChains(driver)
                    actions.move_to_element(next_button).click().perform()
                    print(f"  ✓ Clicked 'Next' button using ActionChains.")
                
                # Wait for the form to update
                time.sleep(2)
                
            except TimeoutException:
                print(f"❌ Error: Next button not found or not clickable")
                capture_screenshot(driver, f"next_button_error_sample_{sample_no}.png")
                return False
            except Exception as e:
                print(f"❌ Error clicking Next button: {e}")
                capture_screenshot(driver, f"next_button_exception_sample_{sample_no}.png")
                return False

        print(f"✅ Successfully navigated to Sample {sample_no}")
        capture_screenshot(driver, f"sample_{sample_no}_selected.png")
        
        # Verify the correct sample is loaded
        time.sleep(2)
        return verify_correct_sample_loaded(driver, sample_no)

    except Exception as e:
        print(f"❌ Failed to navigate to Sample No. {sample_no}: {e}")
        capture_screenshot(driver, f"error_sample_{sample_no}.png")
        return False

def verify_correct_sample_loaded(driver, expected_sample_no):
    """
    Verify that the correct sample is loaded in the form.
    Returns True if verified, False otherwise.
    """
    try:
        print(f"🔍 Verifying Sample {expected_sample_no} is loaded...")
        
        # Look for fields that might contain the sample number
        # These are common patterns in the existing IDs
        possible_selectors = [
            # Direct sample ID/number fields
            "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.SAMPLE_ID",
            "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.SAMPLE_NO",
            "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.SAMPLE_NUMBER",
            # Try looking in the form title or header
            "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA.TITLE",
            # Look for any element containing SAMPLE
            "[id*='SAMPLE'][id*='ID']",
            "[id*='SAMPLE'][id*='NO']",
            "[id*='SAMPLE'][id*='NUMBER']"
        ]
        
        sample_found = False
        found_value = None
        
        for selector in possible_selectors:
            try:
                if selector.startswith('['):
                    # CSS selector
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                else:
                    # ID selector
                    elements = driver.find_elements(By.ID, selector)
                
                for element in elements:
                    if element.is_displayed():
                        value = element.text or element.get_attribute('value') or ''
                        if value.strip():
                            # Check if the expected sample number is in the value
                            if str(expected_sample_no) in str(value):
                                print(f"   ✓ Found sample {expected_sample_no} in: {value}")
                                sample_found = True
                                found_value = value
                                break
                            else:
                                # Log what we found for debugging
                                print(f"   - Found value '{value}' but doesn't match expected {expected_sample_no}")
                                
            except Exception as e:
                continue
            
            if sample_found:
                break
        
        if sample_found:
            print(f"✅ Verified: Sample {expected_sample_no} is loaded correctly")
            return True
        else:
            print(f"❌ Could not verify Sample {expected_sample_no} is loaded")
            print(f"   Expected: Sample {expected_sample_no}")
            if found_value:
                print(f"   Found: {found_value}")
            
            # Take a screenshot for debugging
            capture_screenshot(driver, f"sample_verification_failed_{expected_sample_no}.png")
            return False
            
    except Exception as e:
        print(f"❌ Error during sample verification: {e}")
        return False


def wait_for_form_update(driver, timeout=5):
    """
    Wait for the form to finish updating after navigation.
    """
    try:
        # Wait for any loading indicators to disappear
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "loading"))
        )
        
        # Also check for the overlay
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.ID, "AUILockUIPage"))
        )
        
        return True
    except:
        # If no loading indicators found, that's fine
        return True

# ============================================================================
# MODIFIED TIMING FUNCTIONS - USING REAL UK TIME
# ============================================================================

@handle_popup
def input_realistic_stereo_binocular_start_time(driver):
    """
    Calculate and input a realistic Stereo Binocular Start Time based on current UK time.
    This replaces the old function that read from spreadsheet.
    """
    try:
        start_time_str, _ = calculate_realistic_times()
        
        input_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.STEREOBINOCULARSTARTTIME"))
        )

        input_field.clear()
        input_field.send_keys(start_time_str)
        print(f"✅ Stereo Binocular Start Time set to: {start_time_str}")

        return True, start_time_str

    except TimeoutException:
        print("❌ Error: Stereo Binocular Start Time input field not found.")
        return False, None
    except Exception as e:
        print(f"❌ An error occurred while inputting Stereo Binocular Start Time: {e}")
        return False, None

@handle_popup
def set_realistic_plm_end_time(driver):
    """
    Set PLM end time to current UK time (when we're about to save).
    This replaces the old function that calculated from start time.
    """
    try:
        _, end_time_str = calculate_realistic_times()
        
        plm_end_time_field = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.PLMENDTIME"))
        )

        plm_end_time_field.clear()
        plm_end_time_field.send_keys(end_time_str)

        print(f"✅ PLM End Time set to current UK time: {end_time_str}")
        capture_screenshot(driver, "realistic_plm_end_time_set.png")

        return True

    except TimeoutException:
        print("❌ Error: PLM End Time input field not found.")
        return False
    except Exception as e:
        print("❌ An error occurred while setting PLM End Time:", str(e))
        return False

# ============================================================================
# OTHER SAMPLE PROCESSING FUNCTIONS (UNCHANGED)
# ============================================================================

@handle_popup
def copy_value_to_dropdown(driver):
    try:
        text_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.SURVEYORS_ASSESSMENT"))
        )

        value = text_input.get_attribute("value")

        dropdown = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.ANALYST_ASSESSMENT"))
        )

        dropdown_option = WebDriverWait(dropdown, 10).until(
            EC.visibility_of_element_located((By.XPATH, f"//option[text()='{value}']"))
        )
        dropdown_option.click()

        dropdown.send_keys(Keys.ENTER)

        print("Value copied to dropdown and Enter key pressed successfully!")
        return True

    except TimeoutException:
        print("Error: Element not found.")
        return False
    except Exception as e:
        print("An error occurred:", str(e))
        return False

@handle_popup
def set_sample_size_value(driver):
    try:
        sample_size_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.SAMPLE_SIZE"))
        )

        sample_size_field.clear()
        time.sleep(1)

        sample_size_field.send_keys("sufficient")
        sample_size_field.send_keys(Keys.ENTER)

        time.sleep(2)

        entered_value = sample_size_field.get_attribute("value")
        if entered_value.lower() != "sufficient":
            print(f"⚠️ Warning: Expected 'sufficient', but found '{entered_value}'. Retrying...")
            sample_size_field.clear()
            sample_size_field.send_keys("sufficient")
            sample_size_field.send_keys(Keys.ENTER)

        print("✅ Sample size set to 'sufficient' successfully!")
        capture_screenshot(driver, "sample_size_set.png")

        return True

    except TimeoutException:
        print("❌ Error: Sample size field not found within the timeout.")
        return False
    except Exception as e:
        print(f"❌ An error occurred while setting sample size: {str(e)}")
        return False

@handle_popup
def click_analysis_tab(driver):
    """Clicks on the 'Analysis' tab in the Fibre Analysis pop-up."""
    try:
        print("Attempting to locate 'Analysis' tab...")
        analysis_tab_id = "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.MAIN_TAB.1.TAB"

        analysis_tab = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, analysis_tab_id))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", analysis_tab)
        driver.execute_script("arguments[0].click();", analysis_tab)
        print("Clicked on the 'Analysis' tab using ID successfully.")

        time.sleep(2)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='Analysis 1']"))
        )
        print("Analysis tab content loaded successfully.")
        return True

    except TimeoutException:
        print("Timeout: 'Analysis' tab content not found or not clickable.")
        capture_screenshot(driver, "analysis_tab_not_found.png")
        return False
    except Exception as e:
        print(f"An error occurred while clicking the 'Analysis' tab: {e}")
        capture_screenshot(driver, "analysis_tab_error.png")
        return False

@handle_popup
def handle_analysis_1_result(driver, df, row_index):
    """Handles the analysis result for a specific sample in the 'Analysis' tab."""
    try:
        analysis_1_result = df.loc[row_index, 'Analysis 1']
        sample_no = df.loc[row_index, 'Sample No.']

        if pd.isna(analysis_1_result):
            print(f"Analysis result is empty or NaN for Sample No. {sample_no}. Skipping.")
            return False

        print(f"Processing Analysis 1 result for Sample No. {sample_no} (DataFrame row {row_index}): {analysis_1_result}")

        if "NAD" in analysis_1_result:
            print("Handling NAD result...")
            click_NAD_result_elements(driver, NAD_result_elements)
            capture_screenshot(driver, "NAD_result.png")

        elif "Chrysotile" in analysis_1_result:
            print("Handling Chrysotile result...")
            click_Chrysotile_result_elements(driver, Chrysotile_result_elements)
            capture_screenshot(driver, "Chrysotile_result.png")

        elif "Amosite" in analysis_1_result:
            print("Handling Amosite result...")
            click_amosite_result_elements(driver, amosite_result_elements)
            capture_screenshot(driver, "Amosite_result.png")

        elif "Crocidolite" in analysis_1_result:
            print("Handling Crocidolite result...")
            click_crocidolite_result_elements(driver, crocidolite_result_elements)
            capture_screenshot(driver, "Crocidolite_result.png")

        else:
            print(f"Unknown analysis result for Sample No. {sample_no}: {analysis_1_result}")
            capture_screenshot(driver, "unknown_analysis_result.png")
            return False

        print(f"Analysis result handled successfully for Sample No. {sample_no}")
        capture_screenshot(driver, "analysis_result_handling_success.png")
        return True

    except KeyError as e:
        print(f"KeyError: Missing column in DataFrame - {e}")
        capture_screenshot(driver, "analysis_result_keyerror.png")
        return False
    except TimeoutException:
        print("Error: Element not found within the specified time.")
        capture_screenshot(driver, "analysis_result_timeout.png")
        return False
    except Exception as e:
        print(f"An error occurred while handling analysis 1 result: {str(e)}")
        capture_screenshot(driver, "analysis_result_error.png")
        return False

# Analysis element lists (your original data)
NAD_result_elements = [
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.MAIN_TAB.1.TAB",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_LIST\.CONTROL\.0 > table > tbody > tr > td:nth-child(1)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.0 > table",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.2 > table",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.2 > table",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.0 td:nth-child(2)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.FIBRE_ANALYSIS_OPTIONS_LIST.CONTROL.2",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.1",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.2 td:nth-child(2)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.FIBRE_ANALYSIS_OPTIONS_LIST.CONTROL.4",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.5 > table",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX_analysis_tab_2",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_LIST\.CONTROL\.0 > table > tbody > tr > td:nth-child(3)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.0 td:nth-child(2)",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.0 > table",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.2",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.2 td:nth-child(2)",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.0 td:nth-child(2)",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.2 > table",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.1 > table",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.2 td:nth-child(2)",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.4 > table",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.5 td:nth-child(2)",
]

Chrysotile_result_elements = [
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.MAIN_TAB.1.TAB",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_LIST\.CONTROL\.0 > table > tbody > tr > td:nth-child(1)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.0 td:nth-child(2)",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.0 td:nth-child(2)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.2",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.0 td:nth-child(2)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.2",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.4",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.2 td:nth-child(2)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.1",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.3",
]

amosite_result_elements = [
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.MAIN_TAB.1.TAB",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_LIST\.CONTROL\.0 > table > tbody > tr > td:nth-child(1)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.3",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.2 td:nth-child(2)",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.2 td:nth-child(2)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.2",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.1 td:nth-child(2)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.1",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.3 td:nth-child(2)",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.1 td:nth-child(2)",
]

crocidolite_result_elements = [
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.MAIN_TAB.1.TAB",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX_analysis_tab_1",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_LIST.DISPLAY_NAME.I.0",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.4",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.1",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.3 > table",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.2",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.0 td:nth-child(2)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.0",
    "css=#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX\.V\.R1\.FIBRE_ANALYSIS_OPTIONS_LIST\.CONTROL\.0 td:nth-child(2)",
    "id=TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.FIBRE_ANALYSIS_OPTIONS_LIST.VALUE.I.4",
]

@handle_popup
def click_NAD_result_elements(driver, NAD_result_elements):
    """Iterates over the list of NAD result elements and performs actions."""
    try:
        for action in NAD_result_elements:
            try:
                element_type, element_selector = action.split("=")
                if element_type == "id":
                    locator = (By.ID, element_selector)
                elif element_type == "css":
                    locator = (By.CSS_SELECTOR, element_selector)
                else:
                    print(f"Unknown locator type '{element_type}'. Skipping this element.")
                    continue

                print(f"Attempting to click element: {element_selector}")
                for attempt in range(3):
                    try:
                        element = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable(locator)
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        element.click()
                        print(f"Clicked on {element_selector} successfully!")
                        capture_screenshot(driver, f"clicked_{element_selector.replace('#', '').replace('.', '')}.png")
                        break
                    except StaleElementReferenceException:
                        print(f"Stale element reference encountered for {element_selector}. Retrying...")
                        continue
                    except TimeoutException:
                        print(f"Timeout waiting for {element_selector}. Retrying...")
                        continue
                else:
                    print(f"Failed to click on {element_selector} after 3 retries.")

            except ValueError:
                print(f"Malformed action: {action}. Expected format 'type=value'. Skipping.")
                continue

    except Exception as e:
        print(f"An error occurred while performing actions on NAD result elements: {str(e)}")
        capture_screenshot(driver, "nad_result_error.png")

@handle_popup
def click_Chrysotile_result_elements(driver, Chrysotile_result_elements):
    """Iterates over the list of Chrysotile result elements and performs actions."""
    try:
        for action in Chrysotile_result_elements:
            try:
                element_type, element_selector = action.split("=")
                if element_type == "id":
                    locator = (By.ID, element_selector)
                elif element_type == "css":
                    locator = (By.CSS_SELECTOR, element_selector)
                else:
                    print(f"Unknown locator type '{element_type}'. Skipping this element.")
                    continue

                print(f"Attempting to click element: {element_selector}")
                for attempt in range(3):
                    try:
                        element = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable(locator)
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        element.click()
                        print(f"Clicked on {element_selector} successfully!")
                        capture_screenshot(driver, f"clicked_{element_selector.replace('#', '').replace('.', '')}.png")
                        break
                    except StaleElementReferenceException:
                        print(f"Stale element reference encountered for {element_selector}. Retrying...")
                        continue
                    except TimeoutException:
                        print(f"Timeout waiting for {element_selector}. Retrying...")
                        continue
                else:
                    print(f"Failed to click on {element_selector} after 3 retries.")

            except ValueError:
                print(f"Malformed action: {action}. Expected format 'type=value'. Skipping.")
                continue

    except Exception as e:
        print(f"An error occurred while performing actions on Chrysotile result elements: {str(e)}")
        capture_screenshot(driver, "chrysotile_result_error.png")

@handle_popup
def click_amosite_result_elements(driver, amosite_result_elements):
    """Iterates over the list of Amosite result elements and performs actions."""
    try:
        for action in amosite_result_elements:
            try:
                element_type, element_selector = action.split("=")
                if element_type == "id":
                    locator = (By.ID, element_selector)
                elif element_type == "css":
                    locator = (By.CSS_SELECTOR, element_selector)
                else:
                    print(f"Unknown locator type '{element_type}'. Skipping this element.")
                    continue

                print(f"Attempting to click element: {element_selector}")
                for attempt in range(3):
                    try:
                        element = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable(locator)
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        element.click()
                        print(f"Clicked on {element_selector} successfully!")
                        capture_screenshot(driver, f"clicked_{element_selector.replace('#', '').replace('.', '')}.png")
                        break
                    except StaleElementReferenceException:
                        print(f"Stale element reference encountered for {element_selector}. Retrying...")
                        continue
                    except TimeoutException:
                        print(f"Timeout waiting for {element_selector}. Retrying...")
                        continue
                else:
                    print(f"Failed to click on {element_selector} after 3 retries.")

            except ValueError:
                print(f"Malformed action: {action}. Expected format 'type=value'. Skipping.")
                continue

    except Exception as e:
        print(f"An error occurred while performing actions on Amosite result elements: {str(e)}")
        capture_screenshot(driver, "amosite_result_error.png")

def click_crocidolite_result_elements(driver, crocidolite_result_elements):
    """Iterates over the list of Crocidolite result elements and performs actions."""
    try:
        for action in crocidolite_result_elements:
            try:
                element_type, element_selector = action.split("=")
                if element_type == "id":
                    locator = (By.ID, element_selector)
                elif element_type == "css":
                    locator = (By.CSS_SELECTOR, element_selector)
                else:
                    print(f"Unknown locator type '{element_type}'. Skipping this element.")
                    continue

                print(f"Attempting to click element: {element_selector}")
                for attempt in range(3):
                    try:
                        element = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable(locator)
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        element.click()
                        print(f"Clicked on {element_selector} successfully!")
                        capture_screenshot(driver, f"clicked_{element_selector.replace('#', '').replace('.', '')}.png")
                        break
                    except StaleElementReferenceException:
                        print(f"Stale element reference encountered for {element_selector}. Retrying...")
                        continue
                    except TimeoutException:
                        print(f"Timeout waiting for {element_selector}. Retrying...")
                        continue
                else:
                    print(f"Failed to click on {element_selector} after 3 retries.")

            except ValueError:
                print(f"Malformed action: {action}. Expected format 'type=value'. Skipping.")
                continue

    except Exception as e:
        print(f"An error occurred while performing actions on Crocidolite result elements: {str(e)}")
        capture_screenshot(driver, "crocidolite_result_error.png")

@handle_popup
def click_save_button(driver):
    """Clicks the save button on the Fibre Analysis page."""
    try:
        print("Attempting to click the save button...")

        save_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.FOOTER_CONTROLS.PreSaveChecks.ICON"))
        )

        driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
        save_button.click()
        print("Save button clicked successfully!")

        WebDriverWait(driver, 15).until_not(
            EC.presence_of_element_located((By.ID, "loading_indicator_id"))
        )
        print("Save action completed.")
        capture_screenshot(driver, "Save_screenshot.png")

        return True

    except TimeoutException:
        print("Error: Save button not clickable or not found.")
        capture_screenshot(driver, "save_button_error.png")
        return False
    except Exception as e:
        print(f"An error occurred while clicking the save button: {e}")
        capture_screenshot(driver, "save_button_exception.png")
        return False

@handle_popup
def close_fiber_analysis(driver):
    """Closes the Fibre Analysis dialog by clicking on the close button."""
    try:
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "A5dlg2.TITLE.TOOLS."))
        )

        close_button.click()

        print("Fibre Analysis dialog closed successfully.")
        return True
    except TimeoutException:
        print("Timeout: Close button not clickable or not found.")
    except NoSuchElementException:
        print("Error: Close button not found.")
    except Exception as e:
        print(f"An error occurred while closing the Fibre Analysis dialog: {str(e)}")
    return False

# ============================================================================
# STATE MANAGEMENT FOR GITHUB ACTIONS
# ============================================================================

def load_state():
    """Load automation state from file."""
    try:
        if os.path.exists('automation_state.json'):
            with open('automation_state.json', 'r') as f:
                state = json.load(f)
            print(f"📂 State loaded: {state}")
            return state
    except Exception as e:
        print(f"⚠️ Could not load state: {e}")
    
    default_state = {
        'current_project': None,
        'current_sample_index': 0,
        'processed_samples': [],
        'failed_samples': [],
        'completed_projects': [],
        'last_run_time': None,
        'total_samples_processed': 0
    }
    print(f"🆕 Using default state")
    return default_state

def save_state(state):
    """Save automation state to file."""
    try:
        with open('automation_state.json', 'w') as f:
            json.dump(state, f, indent=2, default=str)
        print(f"💾 State saved: {state}")
    except Exception as e:
        print(f"❌ Error saving state: {e}")

def count_samples_on_website(driver):
    """Count samples on website using record count element."""
    try:
        print("Counting samples on website...")
        
        try:
            record_count_element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA.RECORDCOUNT.TOP"))
            )
            
            record_count_text = record_count_element.text.strip()
            
            if record_count_text.isdigit():
                total_samples = int(record_count_text)
                print(f"✅ Found total samples: {total_samples}")
                return total_samples
            else:
                print(f"⚠️ Record count not a number: '{record_count_text}'")
                
        except TimeoutException:
            print("⚠️ Record count element not found")
        
        return -1
        
    except Exception as e:
        print(f"❌ Error counting samples: {e}")
        return -1

def verify_sample_counts(driver, project_df, project_number):
    """Compare sample counts between spreadsheet and website."""
    try:
        spreadsheet_count = len(project_df)
        website_count = count_samples_on_website(driver)
        
        result = {
            'project_number': int(project_number),
            'spreadsheet_count': spreadsheet_count,
            'website_count': website_count,
            'match': website_count == spreadsheet_count,
            'reason': ''
        }
        
        if website_count == -1:
            result['match'] = False
            result['reason'] = 'Error counting samples on website'
        elif website_count == spreadsheet_count:
            result['reason'] = 'Counts match'
        else:
            result['reason'] = f'Count mismatch: Spreadsheet has {spreadsheet_count}, website has {website_count}'
            
        return result
        
    except Exception as e:
        return {
            'project_number': int(project_number),
            'spreadsheet_count': len(project_df) if project_df is not None else 0,
            'website_count': -1,
            'match': False,
            'reason': f'Error during verification: {str(e)}'
        }

def get_next_sample_to_process(df, state):
    """Determine the next sample to process."""
    try:
        projects = df["Project Number"].unique()
        
        if state['current_project'] is None:
            if len(projects) > 0:
                state['current_project'] = int(projects[0])
                state['current_sample_index'] = 0
            else:
                return None, None, None
        
        current_project_df = df[df["Project Number"] == state['current_project']].reset_index(drop=True)
        
        if state['current_sample_index'] >= len(current_project_df):
            state['completed_projects'].append(state['current_project'])
            
            remaining_projects = [p for p in projects if int(p) not in state['completed_projects']]
            
            if remaining_projects:
                state['current_project'] = int(remaining_projects[0])
                state['current_sample_index'] = 0
                current_project_df = df[df["Project Number"] == state['current_project']].reset_index(drop=True)
            else:
                print("🏁 All projects completed!")
                return None, None, None
        
        if state['current_sample_index'] < len(current_project_df):
            sample_data = current_project_df.iloc[state['current_sample_index']]
            return state['current_project'], sample_data, state['current_sample_index']
        
        return None, None, None
        
    except Exception as e:
        print(f"❌ Error getting next sample: {e}")
        return None, None, None

# Realistic Variable Timing System
import random
from datetime import datetime, timedelta
import pytz

# ============================================================================
# REALISTIC TIMING PATTERNS
# ============================================================================

def should_process_sample_now(state):
    """
    Rolling timing: Run 17-19 minutes after the last sample was SUCCESSFULLY processed.
    This creates a natural rolling schedule that shifts throughout the day.
    """
    uk_time = get_uk_time()
    
    print(f"🕐 Current time: {uk_time.strftime('%H:%M')}")
    
    last_sample_time = state.get('last_sample_time', None)
    
    # If no previous sample, start immediately
    if not last_sample_time:
        print(f"🚀 No previous sample found - starting first sample!")
        # Don't update last_sample_time here - only after successful processing
        updated_state = state.copy()
        updated_state['last_timing_check'] = uk_time.isoformat()
        return True, updated_state
    
    # Calculate time since last sample
    try:
        last_time = datetime.fromisoformat(last_sample_time.replace('Z', '+00:00'))
        time_since_last = (uk_time.replace(tzinfo=None) - last_time.replace(tzinfo=None)).total_seconds()
        minutes_since_last = time_since_last / 60
        
        print(f"📊 Last successful sample: {last_time.strftime('%H:%M')}")
        print(f"⏱️  Time since last successful sample: {minutes_since_last:.1f} minutes")
        
        # Random interval between 17-19 minutes
        # Use a consistent random interval per sample (stored in state)
        current_interval = state.get('current_interval')
        if current_interval is None:
            current_interval = random.randint(17, 19)  # 17, 18, or 19 minutes
        
        print(f"🎯 Target interval: {current_interval} minutes")
        
        # Check if enough time has passed (allow ±1 minute flexibility)
        if minutes_since_last >= (current_interval - 1):
            print(f"✅ {minutes_since_last:.1f} minutes ≥ {current_interval-1} minutes - Time for next sample!")
            
            # Set new random interval for next time
            next_interval = random.randint(17, 19)
            
            updated_state = state.copy()
            # Don't update last_sample_time here - only after successful processing
            updated_state['current_interval'] = next_interval
            updated_state['last_timing_check'] = uk_time.isoformat()
            
            print(f"🔄 Next interval will be: {next_interval} minutes")
            return True, updated_state
        else:
            # Not time yet
            minutes_remaining = current_interval - minutes_since_last
            next_time = uk_time + timedelta(minutes=minutes_remaining)
            
            print(f"⏰ Not time yet - need {minutes_remaining:.1f} more minutes")
            print(f"⏰ Next sample at approximately: {next_time.strftime('%H:%M')}")
            
            updated_state = state.copy()
            updated_state['current_interval'] = current_interval
            updated_state['last_timing_check'] = uk_time.isoformat()
            return False, updated_state
            
    except Exception as e:
        print(f"⚠️  Error parsing last sample time: {e}")
        # If we can't parse, start a new sample
        updated_state = state.copy()
        # Don't update last_sample_time here - only after successful processing
        updated_state['current_interval'] = random.randint(17, 19)
        updated_state['last_timing_check'] = uk_time.isoformat()
        return True, updated_state

def navigate_to_first_sample(driver):
    """
    Navigate back to the first sample when starting a new project.
    The 'First' button takes you back to sample 1.
    """
    try:
        print("📍 Navigating back to Sample 1 for new project...")
        
        # Wait for any overlays to disappear
        wait_for_no_overlay(driver)
        
        first_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.FOOTER_CONTROLS.First.ICON"))
        )
        
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", first_button)
        time.sleep(1)
        
        if click_element_safely(driver, first_button, "First button"):
            print("✅ Clicked 'First' button - back at Sample 1")
        else:
            # Try ActionChains as fallback
            actions = ActionChains(driver)
            actions.move_to_element(first_button).click().perform()
            print("✅ Clicked 'First' button using ActionChains - back at Sample 1")
        
        time.sleep(2)
        return True
        
    except Exception as e:
        print(f"❌ Error navigating to first sample: {e}")
        capture_screenshot(driver, "first_button_error.png")
        return False

# ============================================================================
# MODIFIED MAIN FUNCTION WITH VARIABLE TIMING
# ============================================================================

def main():
    """Main function with realistic variable timing."""
    print(f"\n{'='*80}")
    print(f"🚀 REALISTIC VARIABLE TIMING AUTOMATION - {get_uk_time().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"{'='*80}")
    
    # Load state
    state = load_state()
    
    # Check if we should process a sample right now
    should_process, updated_state = should_process_sample_now(state)
    
    if not should_process:
        print(f"⏸️  Not time to process a sample yet. Exiting until next check.")
        # Save the updated state (pattern info) even if we're not processing
        save_state(updated_state)
        return
    
    print(f"🎯 Time to process a sample! Starting automation...")
    print(f"⚠️  Note: If processing fails, the system can retry immediately since timing is only updated after successful saves.")
    
    # Load data
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1cK7Agui9UMlPr2p1K2jI3jtZxyJuYtm7jP5hi9g4i4Q/export?format=csv&gid=433984109"
    columns_to_extract = ["Project Number", "Sample No.", "Stereo Binocular Start Time", "Analysis 1"]
    
    df = load_data_from_google_sheets(spreadsheet_url, columns_to_extract)
    if df is None:
        print("❌ Failed to load data")
        save_state(updated_state)
        return
    
    # Note: We still need the spreadsheet for Analysis 1 column, but ignore the start time
    df["Stereo Binocular Start Time"] = df["Stereo Binocular Start Time"].astype(str).fillna("")
    
    # Get next sample
    project_number, sample_data, sample_index = get_next_sample_to_process(df, updated_state)
    
    if project_number is None:
        print("🏁 All samples completed!")
        save_state(updated_state)
        return
    
        # In main(), after getting sample_data:
    sample_no = normalize_sample_number(sample_data["Sample No."])
    if sample_no is None:
        print(f"❌ Invalid sample number in spreadsheet")
        updated_state['current_sample_index'] += 1
        save_state(updated_state)
        return
    
    print(f"📋 Processing Project {project_number}, Sample {sample_no}")
    print(f"🕐 Using real UK time with variable timing pattern")
    
    # Setup browser
    driver = setup_chrome_for_github()
    
    try:
    # Login and navigate
        if not login(driver, "ryan", os.environ.get('LOGIN_PASSWORD', '')):
            print("❌ Login failed")
            print("🔄 Timing not updated - can retry immediately")
            save_state(updated_state)
            return
        
        if not click_lab_button(driver) or not click_lab_project_list_button(driver):
            print("❌ Navigation failed")
            save_state(updated_state)
            return
        
        # Load project
        wait_for_no_overlay(driver)
        clear_search_criteria(driver)
        
        if not input_project_number(driver, project_number):
            print("❌ Failed to input project")
            save_state(updated_state)
            return
        
        if not press_enter_or_search_on_project_number(driver, project_number):
            print("❌ Failed to search project")
            save_state(updated_state)
            return
        
        verify_project_numbers(driver)
        
        if not click_view_fibre_analysis_button(driver):
            print("❌ Failed to open analysis")
            save_state(updated_state)
            return
        
        # Verify sample counts (first time only)
        if project_number not in updated_state['completed_projects'] and updated_state['current_sample_index'] == 0:
            project_df = df[df["Project Number"] == project_number]
            verification = verify_sample_counts(driver, project_df, project_number)
            
            if not verification['match']:
                print(f"❌ Sample count mismatch: {verification['reason']}")
                updated_state['completed_projects'].append(project_number)
                updated_state['current_sample_index'] = 0
                save_state(updated_state)
                return
        
        # Track if this is the first sample of a new project
        is_new_project = (updated_state['current_sample_index'] == 0)
        
        # Navigate to sample using the corrected navigation logic
        clicked = click_sample_row_with_next_button(driver, sample_no, is_new_project)
        if not clicked:
            print(f"❌ Failed to navigate to Sample {sample_no}")
            
            # Log this as a failed sample
            updated_state['failed_samples'].append({
                'project': project_number,
                'sample': sample_no,
                'reason': 'Failed to navigate to sample',
                'timestamp': get_uk_time().isoformat()
            })
            updated_state['current_sample_index'] += 1
            save_state(updated_state)
            return
        
        print(f"✅ Successfully navigated to and verified Sample {sample_no}")
        
        # Wait for form to be ready
        wait_for_form_update(driver)
        
        # Process sample with real timing
        project_df = df[df["Project Number"] == project_number].reset_index(drop=True)
        
        print(f"📝 Starting sample processing with realistic timing...")
        
        # Step 1: Set sample size
        if not set_sample_size_value(driver):
            print(f"❌ Failed to set sample size")
            updated_state['failed_samples'].append({
                'project': project_number,
                'sample': sample_no,
                'reason': 'Failed to set sample size',
                'timestamp': get_uk_time().isoformat()
            })
            updated_state['current_sample_index'] += 1
            save_state(updated_state)
            return
        
        # Step 2: Input realistic start time (calculated from current UK time)
        success, start_time_str = input_realistic_stereo_binocular_start_time(driver)
        if not success:
            print(f"❌ Failed to input start time")
            updated_state['failed_samples'].append({
                'project': project_number,
                'sample': sample_no,
                'reason': 'Failed to input start time',
                'timestamp': get_uk_time().isoformat()
            })
            updated_state['current_sample_index'] += 1
            save_state(updated_state)
            return
        
        # Step 3: Set realistic end time (current UK time)
        if not set_realistic_plm_end_time(driver):
            print(f"❌ Failed to set PLM end time")
            updated_state['failed_samples'].append({
                'project': project_number,
                'sample': sample_no,
                'reason': 'Failed to set PLM end time',
                'timestamp': get_uk_time().isoformat()
            })
            updated_state['current_sample_index'] += 1
            save_state(updated_state)
            return
        
        # Step 4: Copy value to dropdown
        if not copy_value_to_dropdown(driver):
            print(f"❌ Failed to copy value to dropdown")
            updated_state['failed_samples'].append({
                'project': project_number,
                'sample': sample_no,
                'reason': 'Failed to copy value to dropdown',
                'timestamp': get_uk_time().isoformat()
            })
            updated_state['current_sample_index'] += 1
            save_state(updated_state)
            return
        
        # Step 5: Click analysis tab
        if not click_analysis_tab(driver):
            print(f"❌ Failed to click analysis tab")
            updated_state['failed_samples'].append({
                'project': project_number,
                'sample': sample_no,
                'reason': 'Failed to click analysis tab',
                'timestamp': get_uk_time().isoformat()
            })
            updated_state['current_sample_index'] += 1
            save_state(updated_state)
            return
        
        # Step 6: Handle analysis result
        if not handle_analysis_1_result(driver=driver, df=project_df, row_index=sample_index):
            print(f"❌ Failed to handle analysis result")
            updated_state['failed_samples'].append({
                'project': project_number,
                'sample': sample_no,
                'reason': 'Failed to handle analysis result',
                'timestamp': get_uk_time().isoformat()
            })
            updated_state['current_sample_index'] += 1
            save_state(updated_state)
            return
        
        # Step 7: Save immediately (end time will match save time)
        print(f"💾 Saving Sample {sample_no} at current UK time...")
        if not click_save_button(driver):
            print(f"❌ Failed to save Sample {sample_no}")
            updated_state['failed_samples'].append({
                'project': project_number,
                'sample': sample_no,
                'reason': 'Save failed',
                'timestamp': get_uk_time().isoformat()
            })
        else:
            print(f"✅ Successfully completed and saved Sample {sample_no}")
            success_time = get_uk_time()
            
            # Update last_sample_time ONLY after successful save
            updated_state['last_sample_time'] = success_time.isoformat()
            
            updated_state['processed_samples'].append({
                'project': project_number,
                'sample': sample_no,
                'timestamp': success_time.isoformat(),
                'save_time': success_time.strftime('%d/%m/%Y %H:%M:%S'),
                'pattern_used': updated_state.get('current_pattern', 'unknown')
            })
            updated_state['total_samples_processed'] += 1
            
            print(f"🕐 Next sample can be processed after: {(success_time + timedelta(minutes=updated_state.get('current_interval', 18))).strftime('%H:%M')}")
        
        print(f"📊 Progress Update:")
        print(f"   ✅ Samples Processed: {updated_state['total_samples_processed']}")
        print(f"   ❌ Samples Failed: {len(updated_state['failed_samples'])}")
        print(f"   🏷️  Current Project: {updated_state['current_project']}")
        print(f"   📍 Next Sample Index: {updated_state['current_sample_index']}")
        print(f"   🎯 Current Pattern: {updated_state.get('current_pattern', 'unknown')}")
        
        # Show timing status
        if 'last_sample_time' in updated_state:
            last_time = datetime.fromisoformat(updated_state['last_sample_time'].replace('Z', '+00:00'))
            next_possible = last_time + timedelta(minutes=updated_state.get('current_interval', 18))
            print(f"   🕐 Last successful sample: {last_time.strftime('%H:%M')}")
            print(f"   ⏰ Next sample possible at: {next_possible.strftime('%H:%M')}")
        else:
            print(f"   🕐 No timing restriction - can process immediately")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
        updated_state['failed_samples'].append({
            'project': project_number,
            'sample': sample_no,
            'reason': f'Processing error: {str(e)}',
            'timestamp': get_uk_time().isoformat()
        })
        updated_state['current_sample_index'] += 1
        print("🔄 Timing not updated due to error - can retry immediately")
        
    finally:
        # Save state and cleanup
        save_state(updated_state)
        if 'driver' in locals() and driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()
