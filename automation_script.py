# Complete Automation Script for GitHub Actions
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
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-default-apps")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    
    return driver

# ============================================================================
# YOUR EXISTING FUNCTIONS (Copy from your Colab blocks)
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
        return True

    except Exception as e:
        print(f"Error occurred during login for user '{username}': {e}")
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
        return True
    except TimeoutException:
        print("Error: Could not find the project number input field.")
        return False
    except Exception as e:
        print(f"An error occurred while inputting project number: {str(e)}")
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

        return True

    except TimeoutException:
        print("Timeout: Loading did not finish in the expected time.")
        return False
    except Exception as e:
        print(f"An error occurred while clicking 'View Fibre Analysis' button: {e}")
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
        
        # Get count from record count element
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

# ============================================================================
# SIMPLIFIED MAIN FUNCTION FOR GITHUB ACTIONS
# ============================================================================

def main():
    """Main function that processes one sample per run."""
    print(f"\n{'='*80}")
    print(f"🚀 GITHUB ACTIONS AUTOMATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    # Load state
    state = load_state()
    
    # Load data
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1cK7Agui9UMlPr2p1K2jI3jtZxyJuYtm7jP5hi9g4i4Q/export?format=csv&gid=433984109"
    columns_to_extract = ["Project Number", "Sample No.", "Stereo Binocular Start Time", "Analysis 1"]
    
    df = load_data_from_google_sheets(spreadsheet_url, columns_to_extract)
    if df is None:
        print("❌ Failed to load data")
        return
    
    df["Stereo Binocular Start Time"] = df["Stereo Binocular Start Time"].astype(str).fillna("")
    
    # Get next sample
    project_number, sample_data, sample_index = get_next_sample_to_process(df, state)
    
    if project_number is None:
        print("🏁 All samples completed!")
        return
    
    sample_no = sample_data["Sample No."]
    print(f"📋 Processing Project {project_number}, Sample {sample_no}")
    
    # Setup browser
    driver = setup_chrome_for_github()
    
    try:
        # Login and navigate
        if not login(driver, "ryan", "Crucial12!"):
            print("❌ Login failed")
            return
        
        if not click_lab_button(driver) or not click_lab_project_list_button(driver):
            print("❌ Navigation failed")
            return
        
        # Load project
        wait_for_no_overlay(driver)
        clear_search_criteria(driver)
        
        if not input_project_number(driver, project_number):
            print("❌ Failed to input project")
            return
        
        if not press_enter_or_search_on_project_number(driver, project_number):
            print("❌ Failed to search project")
            return
        
        verify_project_numbers(driver)
        
        if not click_view_fibre_analysis_button(driver):
            print("❌ Failed to open analysis")
            return
        
        # Verify sample counts (first time only)
        if project_number not in state['completed_projects'] and state['current_sample_index'] == 0:
            project_df = df[df["Project Number"] == project_number]
            verification = verify_sample_counts(driver, project_df, project_number)
            
            if not verification['match']:
                print(f"❌ Sample count mismatch: {verification['reason']}")
                state['completed_projects'].append(project_number)
                state['current_sample_index'] = 0
                save_state(state)
                return
        
        # Navigate to sample (simplified for GitHub Actions)
        target_page = (sample_no - 1) // 10
        for _ in range(target_page):
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA_FIBRE_ANALYSIS_UX.V.R1.FOOTER_CONTROLS.Next.ICON"))
                )
                next_button.click()
                time.sleep(2)
            except:
                break
        
        # Click on sample
        row_index = (sample_no - 1) % 10 + 1
        sample_selector = f"#TBI_LAB_PROJEC_162148FIEL_FIBRE_ANAL_BLBA\\.TD\\.R{row_index}\\.SAMPLE_ID"
        
        sample_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, sample_selector))
        )
        sample_element.click()
        
        print(f"✅ Clicked on Sample {sample_no}")
        
        # For GitHub Actions, we'll simulate the 15-minute wait with a shorter delay
        print("⏰ Simulating realistic analysis time...")
        time.sleep(60)  # 1 minute instead of 15 for faster testing
        
        # Update state
        state['current_sample_index'] += 1
        state['total_samples_processed'] += 1
        state['last_run_time'] = datetime.now().isoformat()
        
        print(f"✅ Sample {sample_no} processed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        # Save state and cleanup
        save_state(state)
        driver.quit()

if __name__ == "__main__":
    main()
