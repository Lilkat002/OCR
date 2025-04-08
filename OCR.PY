import pyautogui
import time
import json
import os
import argparse
from datetime import datetime
import pytesseract
from PIL import Image, ImageGrab
import cv2
import numpy as np
import logging
import sys
import csv
import threading
from pytesseract import Output

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('insurance_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configure PyAutoGUI settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class EpicAutomation:
    def __init__(self):
        self.screen_regions = {
            'patient_search': {'top': 100, 'left': 200, 'width': 400, 'height': 200},
            'insurance_tab': {'top': 150, 'left': 300, 'width': 200, 'height': 50},
            'claim_button': {'top': 300, 'left': 400, 'width': 150, 'height': 50},
            'confirmation': {'top': 250, 'left': 350, 'width': 300, 'height': 100}
        }
        self.results = []
        
    def load_patient_ids(self, file_path):
        """Load patient IDs from a CSV file"""
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header row
                return [row[0] for row in reader]
        except Exception as e:
            logging.error(f"Error loading patient IDs: {str(e)}")
            return []

    def save_results(self, file_path='insurance_claim_results.csv'):
        """Save processing results to CSV"""
        try:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Patient ID', 'Status', 'Timestamp', 'Notes'])
                writer.writerows(self.results)
            logging.info(f"Results saved to {file_path}")
        except Exception as e:
            logging.error(f"Error saving results: {str(e)}")

    def search_patient(self, patient_id):
        """Search for a patient in Epic"""
        try:
            # Click patient search field
            self.click_position(250, 100)  # Adjust coordinates
            time.sleep(0.5)
            
            # Clear existing text
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            
            # Type patient ID
            pyautogui.write(patient_id)
            pyautogui.press('enter')
            time.sleep(2)  # Wait for search results
            
            # Verify patient found
            if self.find_text_in_region("patient_search", patient_id):
                logging.info(f"Patient {patient_id} found")
                return True
            else:
                logging.warning(f"Patient {patient_id} not found")
                return False
        except Exception as e:
            logging.error(f"Error searching patient {patient_id}: {str(e)}")
            return False

    def navigate_to_insurance(self):
        """Navigate to insurance section"""
        try:
            # Look for insurance tab
            if self.find_text_in_region("insurance_tab", "Insurance"):
                self.click_position(350, 175)  # Adjust coordinates
                time.sleep(1)
                return True
            return False
        except Exception as e:
            logging.error(f"Error navigating to insurance: {str(e)}")
            return False

    def process_insurance_claim(self, patient_id):
        """Process insurance claim for a patient"""
        try:
            # Search for patient
            if not self.search_patient(patient_id):
                self.results.append([patient_id, "Failed", datetime.now(), "Patient not found"])
                return False

            # Navigate to insurance section
            if not self.navigate_to_insurance():
                self.results.append([patient_id, "Failed", datetime.now(), "Insurance section not found"])
                return False

            # Look for claim button
            if self.find_text_in_region("claim_button", "Submit Claim"):
                self.click_position(450, 325)  # Adjust coordinates
                time.sleep(1)

                # Verify confirmation
                if self.find_text_in_region("confirmation", "Claim Submitted"):
                    self.results.append([patient_id, "Success", datetime.now(), "Claim submitted"])
                    return True
                else:
                    self.results.append([patient_id, "Failed", datetime.now(), "No confirmation received"])
                    return False
            else:
                self.results.append([patient_id, "Failed", datetime.now(), "Claim button not found"])
                return False

        except Exception as e:
            logging.error(f"Error processing claim for patient {patient_id}: {str(e)}")
            self.results.append([patient_id, "Error", datetime.now(), str(e)])
            return False

    def process_batch(self, patient_ids):
        """Process a batch of patient IDs"""
        total = len(patient_ids)
        successful = 0

        for i, patient_id in enumerate(patient_ids, 1):
            logging.info(f"Processing patient {i}/{total}: {patient_id}")
            
            if self.process_insurance_claim(patient_id):
                successful += 1
            
            # Wait between patients
            time.sleep(2)

        return successful, total

def load_sequence(json_file):
    """Load automation sequence from JSON file"""
    try:
        with open(json_file, 'r') as f:
            sequence = json.load(f)
        return sequence
    except Exception as e:
        print(f"Error loading sequence file: {str(e)}")
        return None

def save_sequence(sequence, json_file):
    """Save automation sequence to JSON file"""
    try:
        with open(json_file, 'w') as f:
            json.dump(sequence, f, indent=2)
        print(f"Sequence saved to {json_file}")
        return True
    except Exception as e:
        print(f"Error saving sequence file: {str(e)}")
        return False

def take_screenshot(filename=None, region=None):
    """Take a screenshot and save it to file if filename is provided"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
    
    try:
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()
        
        screenshot.save(filename)
        print(f"Screenshot saved to {filename}")
        return filename
    except Exception as e:
        print(f"Error taking screenshot: {str(e)}")
        return None

def extract_text_from_screenshot(screenshot_path):
    """Extract text from a screenshot using OCR"""
    try:
        img = Image.open(screenshot_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        return ""

def record_new_sequence():
    """Interactive tool to record a new automation sequence"""
    sequence = {"name": "New Automation Sequence", "steps": []}
    
    print("=== Recording New Automation Sequence ===")
    sequence["name"] = input("Enter a name for this sequence: ")
    
    print("\nInstructions:")
    print("- Enter coordinates or special commands for each step")
    print("- Use 'screenshot' to capture the screen at that moment")
    print("- Use 'region x1 y1 x2 y2' to define a region of interest")
    print("- Use 'wait seconds' to pause execution")
    print("- Use 'ocr_click' to click on text found via OCR")
    print("- Enter 'done' when finished")
    
    step_num = 1
    while True:
        print(f"\nStep {step_num}:")
        command = input("Enter command (x,y/screenshot/region/wait/ocr_click/done): ").strip().lower()
        
        if command == 'done':
            break
            
        elif command.startswith('wait'):
            try:
                parts = command.split()
                wait_time = float(parts[1])
                sequence["steps"].append({
                    "type": "wait",
                    "duration": wait_time
                })
                print(f"Added wait for {wait_time} seconds")
                step_num += 1
            except:
                print("Invalid wait format. Use 'wait seconds'")
                
        elif command == 'screenshot':
            region_input = input("Capture region? (x1,y1,x2,y2 or press Enter for full screen): ").strip()
            
            step = {"type": "screenshot"}
            
            if region_input:
                try:
                    x1, y1, x2, y2 = map(int, region_input.split(','))
                    width = x2 - x1
                    height = y2 - y1
                    step["region"] = [x1, y1, width, height]
                except:
                    print("Invalid region format. Using full screen.")
            
            # Ask if OCR should be performed
            ocr_input = input("Extract text with OCR? (y/n): ").strip().lower()
            if ocr_input == 'y':
                step["ocr"] = True
            
            sequence["steps"].append(step)
            print("Added screenshot step")
            step_num += 1
            
        elif command == 'ocr_click':
            print("Enter the region to search in (x1,y1,x2,y2):")
            region_input = input().strip()
            
            try:
                x1, y1, x2, y2 = map(int, region_input.split(','))
                target_word = input("Enter the text to click on: ").strip()
                fuzzy_match = input("Use fuzzy matching? (y/n): ").strip().lower() == 'y'
                
                step = {
                    "type": "ocr_click",
                    "region": [x1, y1, x2-x1, y2-y1],
                    "target_word": target_word,
                    "fuzzy": fuzzy_match
                }
                sequence["steps"].append(step)
                print(f"Added OCR click step for text '{target_word}'")
                step_num += 1
            except:
                print("Invalid region format. Use 'x1,y1,x2,y2'")
            
        elif command.startswith('region'):
            try:
                parts = command.split()
                x1, y1, x2, y2 = map(int, parts[1:5])
                sequence["steps"].append({
                    "type": "region",
                    "coordinates": [x1, y1, x2, y2]
                })
                print(f"Added region of interest: {x1},{y1} to {x2},{y2}")
                step_num += 1
            except:
                print("Invalid region format. Use 'region x1 y1 x2 y2'")
                
        else:
            try:
                # Try to parse as coordinates
                if ',' in command:
                    x, y = map(int, command.split(','))
                else:
                    x, y = map(int, command.split())
                
                click_type = input("Click type (single, double, right, move): ").strip().lower()
                if click_type not in ['single', 'double', 'right', 'move']:
                    click_type = 'single'  # Default to single click
                
                sequence["steps"].append({
                    "type": "click",
                    "x": x,
                    "y": y,
                    "click_type": click_type
                })
                print(f"Added {click_type} click at {x},{y}")
                step_num += 1
            except:
                print("Invalid format. Use 'x,y' for coordinates")
    
    # Ask where to save the sequence
    filename = input("\nEnter filename to save sequence (or press Enter for default): ").strip()
    if not filename:
        filename = f"sequence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    if not filename.endswith('.json'):
        filename += '.json'
    
    save_sequence(sequence, filename)
    return sequence

def run_sequence(sequence, debug=False, csv_file=None, csv_row=0):
    """Run an automation sequence"""
    if not sequence:
        print("No sequence provided")
        return False
    
    print(f"Running sequence: {sequence.get('name', 'Unnamed Sequence')}")
    
    # Create screenshots directory if needed
    screenshots_dir = "screenshots"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    
    # Create results directory if OCR is used
    results_dir = "ocr_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Load CSV data if provided
    csv_data = None
    if csv_file:
        try:
            with open(csv_file, 'r') as f:
                # Read all lines and strip whitespace
                csv_data = [line.strip() for line in f if line.strip()]
                if csv_row >= len(csv_data):
                    print("CSV row index out of range")
                    return False
        except Exception as e:
            print(f"Error loading CSV file: {str(e)}")
            return False
    
    step_num = 1
    for step in sequence.get("steps", []):
        step_type = step.get("type", "")
        
        if debug:
            print(f"Step {step_num}: {step_type} - {step}")
        
        if step_type == "wait":
            duration = step.get("duration", 1)
            if debug:
                print(f"Waiting for {duration} seconds...")
            time.sleep(duration)
            
        elif step_type == "click":
            x, y = step.get("x", 0), step.get("y", 0)
            click_type = step.get("click_type", "single")
            
            if debug:
                print(f"Moving to {x},{y} for {click_type} click...")
            
            # Move mouse to position
            pyautogui.moveTo(x, y, duration=0.5)
            
            # Perform the click based on type
            if click_type == "single":
                pyautogui.click()
            elif click_type == "double":
                pyautogui.doubleClick()
            elif click_type == "right":
                pyautogui.rightClick()
            
        elif step_type == "ocr_click":
            region = step.get("region")
            target_word = step.get("target_word")
            fuzzy = step.get("fuzzy", False)
            
            if debug:
                print(f"Looking for text '{target_word}' in region {region}")
            
            if not click_on_word(target_word, region, fuzzy):
                print(f"Warning: Could not find text '{target_word}' in specified region")
            
        elif step_type == "screenshot":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
            
            region = None
            if "region" in step:
                region = tuple(step["region"])
            
            screenshot_path = take_screenshot(filename, region)
            
            # If OCR is requested, extract text
            if step.get("ocr", False) and screenshot_path:
                text = extract_text_from_screenshot(screenshot_path)
                
                # Save the extracted text
                text_filename = os.path.join(results_dir, f"ocr_{timestamp}.json")
                with open(text_filename, 'w', encoding='utf-8') as f:
                    json.dump({"extracted_text": text}, f, indent=2)
                
                if debug:
                    print(f"OCR results saved to {text_filename}")
                    print(f"Extracted text: {text[:100]}..." if len(text) > 100 else text)
        
        elif step_type == "csv_input":
            if not csv_data:
                print("Error: CSV file not provided for csv_input step")
                return False
                
            value = csv_data[csv_row]
            if debug:
                print(f"Inputting ID from CSV: {value}")
                
            # Type the value
            pyautogui.write(str(value))
            time.sleep(0.5)  # Small delay after typing
        
        step_num += 1
    
    print("Sequence completed")
    return True

def get_current_mouse_position():
    """Get and display the current mouse position"""
    print("Press Ctrl+C to stop")
    try:
        while True:
            x, y = pyautogui.position()
            position_str = f'Current mouse position: X: {x}, Y: {y}'
            print(position_str, end='\r')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nDone recording mouse position")

def click_on_word(word, region=None, fuzzy=False):
    """Click on a word found via OCR in the specified region"""
    screenshot = ImageGrab.grab(bbox=region) if region else ImageGrab.grab()
    data = pytesseract.image_to_data(screenshot, output_type=Output.DICT)

    for i, text in enumerate(data['text']):
        if not text.strip():
            continue
        match = text.strip().lower()
        if (match == word.lower()) or (fuzzy and word.lower() in match):
            x = data['left'][i] + data['width'][i] // 2
            y = data['top'][i] + data['height'][i] // 2
            screen_x = region[0] + x if region else x
            screen_y = region[1] + y if region else y
            pyautogui.moveTo(screen_x, screen_y, duration=0.3)
            pyautogui.click()
            return True
    return False

# Global variable for mouse position display thread
mouse_position_thread = None
stop_mouse_thread = False

def display_mouse_position():
    """Continuously display mouse position in background"""
    global stop_mouse_thread
    last_pos = None
    while not stop_mouse_thread:
        x, y = pyautogui.position()
        current_pos = (x, y)
        
        # Only update if position changed
        if current_pos != last_pos:
            # Move cursor up one line and to the beginning
            sys.stdout.write('\033[F\033[K')
            sys.stdout.write(f'Mouse position: X: {x}, Y: {y}\n')
            sys.stdout.flush()
            last_pos = current_pos
        
        time.sleep(0.2)

def get_user_input(prompt):
    """Get user input while properly handling mouse position display"""
    # Print an empty line for mouse position
    print()
    # Print the prompt
    sys.stdout.write(prompt)
    sys.stdout.flush()
    # Get input
    return input()

def print_header(title):
    """Print a formatted header"""
    clear_screen()
    print("=" * 60)
    print(f"{title:^60}")
    print("=" * 60)
    print(f"Mouse position: {pyautogui.position()}")
    print("-" * 60)
    # Add an extra line for mouse position updates
    print()

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu(options, show_back=True):
    """Print menu options with consistent formatting"""
    for i, (key, description) in enumerate(options.items(), 1):
        print(f"{i}. {description}")
    if show_back:
        print("b. Go back")
    print("q. Quit")
    print("-" * 60)

def get_menu_choice(options, show_back=True):
    """Get and validate menu choice"""
    while True:
        choice = input("Enter your choice: ").strip().lower()
        if choice == 'q':
            return 'quit'
        if show_back and choice == 'b':
            return 'back'
        try:
            num_choice = int(choice)
            if 1 <= num_choice <= len(options):
                return list(options.keys())[num_choice - 1]
        except ValueError:
            pass
        print("Invalid choice. Please try again.")

def record_sequence_menu():
    """Handle sequence recording menu"""
    sequence = {"name": "New Automation Sequence", "steps": []}
    step_num = 1
    
    while True:
        print_header("Record New Automation Sequence")
        print("Available Commands:")
        print("- x,y          : Click at specific coordinates")
        print("- wait N       : Wait for N seconds")
        print("- screenshot   : Capture screen region")
        print("- ocr_click    : Click on text using OCR")
        print("- type         : Type text")
        print("- csv_input    : Input ID from CSV file")
        print("- region       : Define region of interest")
        print("- done        : Finish recording")
        print("- back        : Go back to main menu")
        print("\nCurrent sequence steps:")
        if sequence["steps"]:
            for i, step in enumerate(sequence["steps"], 1):
                print(f"{i}. {step}")
        else:
            print("(No steps recorded yet)")
        print("\nCurrent mouse position is shown at the top of the screen")
        print("-" * 60)
        
        command = get_user_input("Enter command: ").strip().lower()
        
        if command == 'back':
            if sequence["steps"]:
                confirm = get_user_input("Discard current sequence? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            return
            
        elif command == 'done':
            if not sequence["steps"]:
                print("Cannot save empty sequence!")
                get_user_input("Press Enter to continue...")
                continue
                
            sequence["name"] = get_user_input("Enter a name for this sequence: ").strip()
            if not sequence["name"]:
                sequence["name"] = f"sequence_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
            filename = get_user_input("Enter filename to save sequence (or press Enter for default): ").strip()
            if not filename:
                filename = f"{sequence['name'].lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if not filename.endswith('.json'):
                filename += '.json'
                
            sequences_dir = "sequences"
            if not os.path.exists(sequences_dir):
                os.makedirs(sequences_dir)
            
            filepath = os.path.join(sequences_dir, filename)
            save_sequence(sequence, filepath)
            print("\nSequence saved successfully!")
            get_user_input("Press Enter to continue...")
            return
            
        elif command == 'csv_input':
            sequence["steps"].append({
                "type": "csv_input"
            })
            print("Added CSV input step")
            step_num += 1
            
        elif command.startswith('wait'):
            try:
                parts = command.split()
                wait_time = float(parts[1])
                sequence["steps"].append({
                    "type": "wait",
                    "duration": wait_time
                })
                print(f"Added wait for {wait_time} seconds")
                step_num += 1
            except:
                print("Invalid wait format. Use 'wait seconds'")
                get_user_input("Press Enter to continue...")
                
        elif command == 'screenshot':
            print("\nDefine screenshot region:")
            region_input = get_user_input("Enter region (x1,y1,x2,y2) or press Enter for full screen: ").strip()
            
            step = {"type": "screenshot"}
            
            if region_input:
                try:
                    x1, y1, x2, y2 = map(int, region_input.split(','))
                    width = x2 - x1
                    height = y2 - y1
                    step["region"] = [x1, y1, width, height]
                except:
                    print("Invalid region format. Using full screen.")
                    get_user_input("Press Enter to continue...")
            
            ocr_input = get_user_input("Extract text with OCR? (y/n): ").strip().lower()
            if ocr_input == 'y':
                step["ocr"] = True
            
            sequence["steps"].append(step)
            print("Added screenshot step")
            step_num += 1
            
        elif command == 'ocr_click':
            print("\nDefine OCR click region and target:")
            try:
                print("Enter the region to search in (x1,y1,x2,y2):")
                region_input = get_user_input("").strip()
                x1, y1, x2, y2 = map(int, region_input.split(','))
                
                target_word = get_user_input("Enter the text to click on: ").strip()
                if not target_word:
                    print("Text cannot be empty!")
                    get_user_input("Press Enter to continue...")
                    continue
                    
                fuzzy_match = get_user_input("Use fuzzy matching? (y/n): ").strip().lower() == 'y'
                
                step = {
                    "type": "ocr_click",
                    "region": [x1, y1, x2-x1, y2-y1],
                    "target_word": target_word,
                    "fuzzy": fuzzy_match
                }
                sequence["steps"].append(step)
                print(f"Added OCR click step for text '{target_word}'")
                step_num += 1
            except ValueError:
                print("Invalid region format. Use 'x1,y1,x2,y2'")
                get_user_input("Press Enter to continue...")
                
        elif command == 'type':
            text = get_user_input("Enter text to type: ").strip()
            if text:
                sequence["steps"].append({
                    "type": "type",
                    "text": text
                })
                print(f"Added type step: '{text}'")
                step_num += 1
            else:
                print("Text cannot be empty!")
                get_user_input("Press Enter to continue...")
            
        elif command.startswith('region'):
            try:
                parts = command.split()
                if len(parts) == 5:
                    x1, y1, x2, y2 = map(int, parts[1:5])
                else:
                    print("Enter region coordinates (x1 y1 x2 y2):")
                    coords = get_user_input("").strip()
                    x1, y1, x2, y2 = map(int, coords.split())
                
                sequence["steps"].append({
                    "type": "region",
                    "coordinates": [x1, y1, x2, y2]
                })
                print(f"Added region of interest: {x1},{y1} to {x2},{y2}")
                step_num += 1
            except:
                print("Invalid region format. Use 'region x1 y1 x2 y2'")
                get_user_input("Press Enter to continue...")
                
        else:
            try:
                # Try to parse as coordinates
                if ',' in command:
                    x, y = map(int, command.split(','))
                else:
                    x, y = map(int, command.split())
                
                print("\nClick options:")
                print("1. single - Single click")
                print("2. double - Double click")
                print("3. right  - Right click")
                print("4. move   - Just move mouse")
                click_type = get_user_input("Choose click type (1-4): ").strip()
                
                click_types = {
                    "1": "single",
                    "2": "double",
                    "3": "right",
                    "4": "move"
                }
                
                if click_type in click_types:
                    click_type = click_types[click_type]
                else:
                    click_type = "single"  # Default to single click
                
                sequence["steps"].append({
                    "type": "click",
                    "x": x,
                    "y": y,
                    "click_type": click_type
                })
                print(f"Added {click_type} click at {x},{y}")
                step_num += 1
            except ValueError:
                print("Invalid format. Use 'x,y' for coordinates")
                get_user_input("Press Enter to continue...")

def view_sequences_menu():
    """Handle viewing and editing sequences"""
    while True:
        print_header("View/Edit Sequences")
        sequences_dir = "sequences"
        if not os.path.exists(sequences_dir):
            os.makedirs(sequences_dir)
            
        sequences = [f for f in os.listdir(sequences_dir) if f.endswith('.json')]
        
        if not sequences:
            print("No sequences found.")
            print("\nPress Enter to go back...")
            get_user_input("")
            return
            
        print("Available sequences:")
        sequence_options = {seq: seq for seq in sequences}
        print_menu(sequence_options)
        
        choice = get_menu_choice(sequence_options)
        if choice in ['back', 'quit']:
            return choice
            
        # Show sequence details and edit options
        sequence_file = os.path.join(sequences_dir, choice)
        sequence = load_sequence(sequence_file)
        if sequence:
            while True:
                print_header(f"Sequence: {choice}")
                print("Steps:")
                for i, step in enumerate(sequence.get("steps", []), 1):
                    print(f"{i}. {step}")
                print("\n")
                
                action_options = {
                    "run": "Run sequence",
                    "run_debug": "Run sequence with debug output",
                    "run_csv": "Run sequence with CSV input",
                    "edit": "Edit sequence",
                    "delete": "Delete sequence"
                }
                print_menu(action_options)
                action = get_menu_choice(action_options)
                
                if action == 'back':
                    break
                elif action == 'quit':
                    return 'quit'
                elif action in ['run', 'run_debug', 'run_csv']:
                    print("\nPreparing to run sequence...")
                    countdown = get_user_input("Enter seconds to wait before starting (or press Enter for 5s): ").strip()
                    try:
                        wait_time = int(countdown) if countdown else 5
                    except ValueError:
                        wait_time = 5
                    
                    csv_file = None
                    if action == 'run_csv':
                        csv_file = get_user_input("Enter path to CSV file: ").strip()
                        if not os.path.exists(csv_file):
                            print("CSV file not found!")
                            get_user_input("Press Enter to continue...")
                            continue
                    
                    print(f"\nStarting sequence in {wait_time} seconds...")
                    print("Press Ctrl+C to cancel...")
                    try:
                        for i in range(wait_time, 0, -1):
                            print(f"{i}...", end='\r')
                            time.sleep(1)
                        print("\nRunning sequence...")
                        
                        if action == 'run_csv':
                            # Load CSV to get row count
                            with open(csv_file, 'r') as f:
                                reader = csv.reader(f)
                                csv_data = list(reader)
                                total_rows = len(csv_data)
                            
                            # Run sequence for each row
                            for row in range(total_rows):
                                print(f"\nProcessing row {row + 1}/{total_rows}")
                                run_sequence(sequence, debug=(action == 'run_debug'), csv_file=csv_file, csv_row=row)
                                time.sleep(1)  # Small delay between rows
                        else:
                            run_sequence(sequence, debug=(action == 'run_debug'))
                            
                        print("\nSequence completed successfully!")
                    except KeyboardInterrupt:
                        print("\nSequence cancelled by user")
                    except Exception as e:
                        print(f"\nError running sequence: {str(e)}")
                    
                    get_user_input("\nPress Enter to continue...")
                    
                elif action == 'edit':
                    print("\nStarting sequence editor...")
                    record_sequence_menu()
                    
                elif action == 'delete':
                    confirm = get_user_input("\nAre you sure you want to delete this sequence? (y/n): ").strip().lower()
                    if confirm == 'y':
                        try:
                            os.remove(sequence_file)
                            print("\nSequence deleted successfully!")
                            get_user_input("Press Enter to continue...")
                            break
                        except Exception as e:
                            print(f"\nError deleting sequence: {str(e)}")
                            get_user_input("Press Enter to continue...")

def start_mouse_position_display():
    """Start the mouse position display thread"""
    global mouse_position_thread, stop_mouse_thread
    stop_mouse_thread = False
    mouse_position_thread = threading.Thread(target=display_mouse_position)
    mouse_position_thread.daemon = True
    mouse_position_thread.start()
    # Give the thread a moment to start and print the first position
    time.sleep(0.1)

def stop_mouse_position_display():
    """Stop the mouse position display thread"""
    global stop_mouse_thread, mouse_position_thread
    if mouse_position_thread and mouse_position_thread.is_alive():
        stop_mouse_thread = True
        mouse_position_thread.join(timeout=1)
        # Clear the last mouse position line
        sys.stdout.write('\033[F\033[K')
        sys.stdout.flush()

def main():
    try:
        # Start mouse position display thread
        start_mouse_position_display()
        
        automation = EpicAutomation()
        
        while True:
            print_header("Epic Automation Tool")
            
            main_options = {
                "process": "Process patient IDs from CSV",
                "record": "Record new automation sequence",
                "view": "View/Edit existing sequences",
                "coordinates": "Get mouse coordinates (for setup)",
                "settings": "Settings"
            }
            
            print_menu(main_options, show_back=False)
            choice = get_menu_choice(main_options, show_back=False)
            
            if choice == 'quit':
                print("\nExiting...")
                break
                
            elif choice == "process":
                print_header("Process Patient IDs")
                print("Please provide the path to your CSV file with patient IDs:")
                csv_path = input().strip()
                
                if csv_path.lower() == 'b':
                    continue
                    
                patient_ids = automation.load_patient_ids(csv_path)
                
                if not patient_ids:
                    print("No patient IDs loaded. Please check your CSV file.")
                    input("Press Enter to continue...")
                    continue

                print(f"Found {len(patient_ids)} patients to process.")
                print("Please switch to Epic Hyperspace window within 5 seconds...")
                time.sleep(5)
                
                successful, total = automation.process_batch(patient_ids)
                automation.save_results()
                
                print(f"\nProcessing complete!")
                print(f"Successfully processed: {successful}/{total} patients")
                print("Results have been saved to insurance_claim_results.csv")
                input("Press Enter to continue...")
                
            elif choice == "record":
                record_sequence_menu()
                
            elif choice == "view":
                if view_sequences_menu() == 'quit':
                    break
                    
            elif choice == "coordinates":
                print_header("Mouse Coordinate Tracker")
                print("Move your mouse to get coordinates")
                print("Press Ctrl+C to stop tracking")
                try:
                    get_current_mouse_position()
                except KeyboardInterrupt:
                    pass
                    
            elif choice == "settings":
                print_header("Settings")
                settings_options = {
                    "tesseract": "Configure Tesseract path",
                    "debug": "Toggle debug mode",
                    "delay": "Adjust automation delay"
                }
                print_menu(settings_options)
                settings_choice = get_menu_choice(settings_options)
                if settings_choice == 'quit':
                    break
                
    except KeyboardInterrupt:
        print("\nAutomation stopped by user")
        try:
            automation.save_results()
        except:
            pass
    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
    finally:
        stop_mouse_position_display()

if __name__ == "__main__":
    main() 
