"""
OpenRouter Top Apps Scraper - Simplified Version
Scrapes Top Apps data dynamically from the live website
"""

import csv
import json
import time
import re
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client, Client


class OpenRouterAppsScraper:
    def __init__(self):
        """Initialize the apps scraper"""
        self.driver = None
        self.supabase = self.init_supabase()
    
    def init_supabase(self):
        """Initialize Supabase client"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                print("ERROR: Supabase credentials not found in environment variables")
                return None
            
            supabase: Client = create_client(supabase_url, supabase_key)
            print("SUCCESS: Supabase client initialized")
            return supabase
        except Exception as e:
            print(f"ERROR: Failed to initialize Supabase client: {e}")
            return None
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            print("INFO: Setting up Chrome WebDriver...")
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Use webdriver-manager to automatically handle ChromeDriver
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e:
                print(f"WARNING: ChromeDriver service failed: {e}")
                print("INFO: Trying without service...")
                # Fallback: try without service
                self.driver = webdriver.Chrome(options=chrome_options)
            
            print("SUCCESS: Chrome WebDriver setup completed")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to setup Chrome WebDriver: {e}")
            return False
    
    def scrape_top_apps(self, max_apps=20, time_period="Today"):
        """
        Scrape Top Apps data from OpenRouter for a specific time period
        
        Args:
            max_apps (int): Maximum number of apps to scrape
            time_period (str): Time period to scrape ("Today", "This Week", "This Month")
            
        Returns:
            list: List of app data dictionaries
        """
        if not self.setup_driver():
            return []
        
        try:
            print("INFO: Scraping Top Apps...")
            
            # Navigate to the rankings page
            print("INFO: Navigating to OpenRouter rankings page...")
            self.driver.get("https://openrouter.ai/rankings")
            
            # Wait for the page to load completely
            print("INFO: Waiting for page to load completely...")
            time.sleep(30)
            
            # Wait for dynamic content to load
            print("INFO: Waiting for dynamic content to load...")
            try:
                # Wait for specific elements to appear
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Top Apps')]"))
                )
                print("SUCCESS: Top Apps section found")
            except TimeoutException:
                print("WARNING: Top Apps section not found within timeout")
            
            # Additional wait for content to fully render
            time.sleep(15)
            
            # Scroll to trigger content loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(5)
            
            # Look for Top Apps section
            if not self.find_top_apps_section():
                print("WARNING: Could not find Top Apps section")
                return []
            
            # Select the time period
            if not self.select_time_period(time_period):
                print(f"WARNING: Could not select time period '{time_period}', using default")
            
            # Wait for the page content to update after time period selection
            print(f"INFO: Waiting for page content to update after selecting '{time_period}'...")
            time.sleep(8)  # Wait for content to update
            
            # Scroll to refresh content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Verify that the content actually changed by checking for time period indicators
            self.verify_content_changed(time_period)
            
            # Get the page source
            page_source = self.driver.page_source
            
            # Skip saving page source to avoid creating temporary files
            print(f"INFO: Page source obtained for {time_period} (not saved to avoid temp files)")
            
            # Parse the app data from the page
            apps = self.parse_top_apps_data(page_source, max_apps, time_period)
            
            print(f"SUCCESS: Successfully scraped {len(apps)} top apps")
            return apps
            
        except Exception as e:
            print(f"ERROR: Error scraping top apps: {e}")
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                print("INFO: WebDriver closed")
    
    def find_top_apps_section(self):
        """
        Find the Top Apps section on the page
        
        Returns:
            bool: True if found, False otherwise
        """
        try:
            print("INFO: Looking for Top Apps section...")
            
            # Look for various indicators of Top Apps section
            selectors = [
                "//button[contains(text(), 'Apps')]",
                "//a[contains(text(), 'Apps')]", 
                "//div[contains(text(), 'Apps')]",
                "//span[contains(text(), 'Apps')]",
                "//h2[contains(text(), 'Apps')]",
                "//h3[contains(text(), 'Apps')]"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            # Click on the Apps section
                            self.driver.execute_script("arguments[0].click();", element)
                            print("SUCCESS: Found and clicked Top Apps section")
                            time.sleep(5)
                            return True
                except:
                    continue
            
            print("WARNING: Top Apps section not found with standard selectors")
            return False
            
        except Exception as e:
            print(f"WARNING: Error looking for Top Apps section: {e}")
            return False
    
    def select_time_period(self, time_period="Today"):
        """
        Select the time period using the same robust method as openrouter_scraper(final).py
        
        Args:
            time_period (str): Time period to select ("Today", "This Week", "This Month")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"INFO: Looking for '{time_period}' option...")
            
            # Wait for the page to load
            time.sleep(5)
            
            # Use the exact menu item text (not the dropdown button text)
            # The menu items have text: "Today", "This Week", "This Month"
            actual_text = time_period
            print(f"INFO: Looking for '{actual_text}' option...")
            
            # Try different possible selectors for the time period options (same as working scraper)
            time_period_selectors = [
                f"//button[contains(text(), '{actual_text}')]",
                f"//*[contains(text(), '{actual_text}')]",
                f"//div[contains(text(), '{actual_text}')]",
                f"//span[contains(text(), '{actual_text}')]",
                f"//a[contains(text(), '{actual_text}')]",
                f"[data-value*='{actual_text.lower()}']",
                f"[data-value*='{actual_text.lower().replace(' ', '_')}']",
                f"[data-value*='{actual_text.lower().replace(' ', '-')}']"
            ]
            
            time_period_element = None
            
            # Try to find the element (same logic as working scraper)
            for selector in time_period_selectors:
                try:
                    if selector.startswith("//"):
                        time_period_element = self.driver.find_element(By.XPATH, selector)
                    else:
                        time_period_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if time_period_element and time_period_element.is_displayed():
                        print(f"SUCCESS: Found '{actual_text}' option with selector: {selector}")
                        break
                except:
                    continue
            
            # If still not found, try to find any clickable element that might be the time period option
            if not time_period_element:
                print(f"INFO: Trying to find any clickable element that might be '{actual_text}'...")
                clickable_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{actual_text}')]")
                for element in clickable_elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            time_period_element = element
                            print(f"SUCCESS: Found potential '{actual_text}' element with text: '{element.text}'")
                            break
                    except:
                        continue
            
            if time_period_element:
                # Try multiple methods to click the element (same as working scraper)
                success = False
                
                # Method 1: Regular click
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", time_period_element)
                    time.sleep(2)
                    time_period_element.click()
                    success = True
                    print(f"SUCCESS: Regular click worked for '{actual_text}'")
                except Exception as e:
                    print(f"WARNING: Regular click failed for '{actual_text}': {e}")
                
                # Method 2: JavaScript click
                if not success:
                    try:
                        self.driver.execute_script("arguments[0].click();", time_period_element)
                        success = True
                        print(f"SUCCESS: JavaScript click worked for '{actual_text}'")
                    except Exception as e:
                        print(f"WARNING: JavaScript click failed for '{actual_text}': {e}")
                
                # Method 3: ActionChains click
                if not success:
                    try:
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(self.driver)
                        actions.move_to_element(time_period_element).click().perform()
                        success = True
                        print(f"SUCCESS: ActionChains click worked for '{actual_text}'")
                    except Exception as e:
                        print(f"WARNING: ActionChains click failed for '{actual_text}': {e}")
                
                if success:
                    # Wait for the content to load (same as working scraper)
                    print(f"INFO: Waiting for '{actual_text}' content to load...")
                    time.sleep(10)
                    
                    # Scroll to trigger any lazy loading
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(3)
                    
                    print(f"SUCCESS: '{actual_text}' option clicked successfully")
                    return True
                else:
                    print(f"ERROR: All click methods failed for '{actual_text}'")
                    return False
            else:
                print(f"WARNING: '{actual_text}' option not found")
                return False
                
        except Exception as e:
            print(f"ERROR: Error clicking '{actual_text}' option: {e}")
            return False
    
    def verify_content_changed(self, time_period):
        """
        Verify that the page content actually changed after selecting a time period
        """
        try:
            print(f"INFO: Verifying content changed for '{time_period}'...")
            
            # Get the current page text
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Check if we can find time period indicators in the content
            time_indicators = {
                "Today": ["Today"],
                "This Week": ["This Week"],
                "This Month": ["This Month"]
            }
            
            expected_indicators = time_indicators.get(time_period, [time_period.lower()])
            found_indicators = []
            
            for indicator in expected_indicators:
                if indicator in page_text.lower():
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"SUCCESS: Found time period indicators: {found_indicators}")
            else:
                print(f"WARNING: No time period indicators found for '{time_period}'")
            
            # Also check the dropdown button text to see if it changed
            try:
                dropdown_button = self.driver.find_element(By.ID, "options-menu")
                button_text = dropdown_button.text
                print(f"INFO: Current dropdown button text: '{button_text}'")
                
                # Check if the button text indicates the correct selection
                if time_period.lower() in button_text.lower():
                    print(f"SUCCESS: Dropdown button shows correct selection: '{button_text}'")
                else:
                    print(f"WARNING: Dropdown button text '{button_text}' doesn't match expected '{time_period}'")
                    
            except Exception as e:
                print(f"WARNING: Could not check dropdown button text: {e}")
                
        except Exception as e:
            print(f"WARNING: Error verifying content change: {e}")
    
    def parse_top_apps_data(self, page_source, max_apps=20, time_period="Today"):
        """
        Parse top apps data from page source using HTML href extraction
        
        Args:
            page_source (str): HTML page source
            max_apps (int): Maximum number of apps to parse
            time_period (str): Time period for the data
            
        Returns:
            list: List of app data dictionaries
        """
        apps = []
        
        try:
            print("INFO: Parsing top apps data from page source...")
            
            # First try to extract URLs and image URLs from HTML using href attributes
            app_urls, image_urls = self.extract_app_urls_from_html(page_source, max_apps)
            
            # Then extract app data from text content
            apps = self.extract_apps_from_text(page_source, max_apps, app_urls, image_urls, time_period)
            
            if apps:
                print(f"INFO: Successfully extracted {len(apps)} apps combining HTML URLs with text data")
                return apps
            
            # Fallback to text-based parsing only
            print("INFO: Combined extraction failed, trying text-based parsing only...")
            
            # Get the page text content
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Save page text for debugging
            with open("top_apps_page_text.txt", "w", encoding="utf-8") as file:
                file.write(page_text)
            print("INFO: Page text saved to top_apps_page_text.txt")
            
            # Look for app data in the text
            lines = page_text.split('\n')
            in_top_apps_section = False
            current_rank = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Check if we're in the Top Apps section
                if 'Top Apps' in line:
                    in_top_apps_section = True
                    print("INFO: Found Top Apps section in text")
                    continue
                
                if in_top_apps_section:
                    # Look for rank numbers
                    if re.match(r'^\d+\.$', line):
                        current_rank = int(line[:-1])
                        if current_rank > max_apps:
                            break
                        
                        # Look ahead for app data
                        app_data = self.extract_app_data_from_lines(lines, i + 1, current_rank, time_period)
                        if app_data:
                            apps.append(app_data)
                            print(f"INFO: Found app {current_rank}: {app_data['app_name']} - {app_data['tokens']}")
            
            # If no apps found with the above method, try a different approach
            if not apps:
                print("INFO: No apps found with standard method, trying alternative approach...")
                apps = self.parse_apps_alternative(page_text, max_apps, time_period)
            
            return apps
            
        except Exception as e:
            print(f"ERROR: Error parsing top apps data: {e}")
            return []
    
    def extract_app_urls_from_html(self, page_source, max_apps=20):
        """
        Extract app URLs and image URLs from HTML using href attributes and favicon sources
        
        Args:
            page_source (str): HTML page source
            max_apps (int): Maximum number of URLs to extract
            
        Returns:
            tuple: (list of decoded URLs, list of image URLs)
        """
        urls = []
        image_urls = []
        
        try:
            print("INFO: Extracting app URLs and image URLs from HTML...")
            
            # Look for the pattern: href="/apps?url=https%3A%2F%2Fwww.hammerai.com%2F"
            href_pattern = r'href="(/apps\?url=([^"]+))"'
            matches = re.findall(href_pattern, page_source)
            
            if not matches:
                print("INFO: No href patterns found, trying alternative patterns...")
                # Try alternative pattern without the /apps prefix
                href_pattern = r'href="([^"]*url=([^"]+))"'
                matches = re.findall(href_pattern, page_source)
            
            if matches:
                print(f"INFO: Found {len(matches)} href matches")
                
                for i, (full_href, encoded_url) in enumerate(matches[:max_apps]):
                    try:
                        # Decode the URL
                        import urllib.parse
                        decoded_url = urllib.parse.unquote(encoded_url)
                        urls.append(decoded_url)
                        
                        # Extract image URL from the same HTML block
                        image_url = self.extract_image_url_from_href_block(page_source, full_href, decoded_url)
                        image_urls.append(image_url)
                        
                        print(f"INFO: Extracted URL {i+1}: {decoded_url}")
                        if image_url:
                            print(f"INFO: Extracted Image {i+1}: {image_url}")
                    
                    except Exception as e:
                        print(f"WARNING: Error processing href match {i+1}: {e}")
                        continue
            
            return urls, image_urls
            
        except Exception as e:
            print(f"ERROR: Error extracting URLs from HTML: {e}")
            return [], []
    
    def extract_image_url_from_href_block(self, page_source, href, decoded_url):
        """
        Extract image URL from the HTML block containing the href
        
        Args:
            page_source (str): Full HTML page source
            href (str): The href attribute value
            decoded_url (str): The decoded URL
            
        Returns:
            str: Image URL or empty string if not found
        """
        try:
            # Find the position of this href in the page source
            href_pos = page_source.find(href)
            if href_pos == -1:
                return ""
            
            # Extract a block of HTML around this href (1000 characters before and after)
            start_pos = max(0, href_pos - 1000)
            end_pos = min(len(page_source), href_pos + 1000)
            html_block = page_source[start_pos:end_pos]
            
            # Look for favicon image URLs in the same block
            # Pattern: src="https://t0.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.hammerai.com/&size=256"
            favicon_pattern = r'src="(https://t0\.gstatic\.com/faviconV2[^"]+)"'
            favicon_match = re.search(favicon_pattern, html_block)
            
            if favicon_match:
                # Decode HTML entities like &amp; to &
                import html
                decoded_url = html.unescape(favicon_match.group(1))
                return decoded_url
            
            # Try alternative pattern for other image sources
            img_pattern = r'src="([^"]*favicon[^"]*)"'
            img_match = re.search(img_pattern, html_block)
            
            if img_match:
                # Decode HTML entities like &amp; to &
                import html
                decoded_url = html.unescape(img_match.group(1))
                return decoded_url
            
            # If no favicon found, try to generate one using the decoded URL
            if decoded_url:
                # Generate a favicon URL using Google's favicon service
                import urllib.parse
                encoded_domain = urllib.parse.quote(decoded_url, safe='')
                generated_favicon = f"https://t0.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url={encoded_domain}&size=256"
                return generated_favicon
            
            return ""
            
        except Exception as e:
            print(f"WARNING: Error extracting image URL from href block: {e}")
            return ""
    
    def extract_apps_from_text(self, page_source, max_apps=20, app_urls=None, image_urls=None, time_period="Today"):
        """
        Extract apps from text content and combine with URLs and image URLs
        
        Args:
            page_source (str): HTML page source
            max_apps (int): Maximum number of apps to extract
            app_urls (list): List of app URLs from HTML extraction
            image_urls (list): List of image URLs from HTML extraction
            time_period (str): Time period for the data
            
        Returns:
            list: List of app data dictionaries
        """
        apps = []
        
        try:
            print("INFO: Extracting apps from text content...")
            
            # Get the page text content
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Look for the Top Apps section in the text
            lines = page_text.split('\n')
            in_top_apps_section = False
            current_rank = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Check if we're in the Top Apps section
                if 'Top Apps' in line:
                    in_top_apps_section = True
                    print("INFO: Found Top Apps section in text")
                    continue
                
                if in_top_apps_section:
                    # Look for rank numbers
                    if re.match(r'^\d+\.$', line):
                        current_rank = int(line[:-1])
                        if current_rank > max_apps:
                            break
                        
                        # Look ahead for app data
                        app_data = self.extract_app_data_from_lines(lines, i + 1, current_rank, time_period)
                        if app_data:
                            # Use the corresponding URL if available
                            if app_urls and current_rank <= len(app_urls):
                                app_data['app_url'] = app_urls[current_rank - 1]
                                app_data['domain'] = self.extract_domain_from_url(app_urls[current_rank - 1])
                            
                            # Use the corresponding image URL if available
                            if image_urls and current_rank <= len(image_urls):
                                app_data['image_url'] = image_urls[current_rank - 1]
                            else:
                                app_data['image_url'] = ""
                            
                            apps.append(app_data)
                            print(f"INFO: Found app {current_rank}: {app_data['app_name']} - {app_data['tokens']} - URL: {app_data.get('app_url', 'Generated')} - Image: {app_data.get('image_url', 'None')[:50]}...")
            
            return apps
            
        except Exception as e:
            print(f"ERROR: Error extracting apps from text: {e}")
            return []
    
    def extract_apps_from_html(self, page_source, max_apps=20):
        """
        Extract apps from HTML using href attributes and proper parsing
        
        Args:
            page_source (str): HTML page source
            max_apps (int): Maximum number of apps to extract
            
        Returns:
            list: List of app data dictionaries
        """
        apps = []
        
        try:
            print("INFO: Extracting apps from HTML using href attributes...")
            
            # Look for the pattern: href="/apps?url=https%3A%2F%2Fwww.hammerai.com%2F"
            # This pattern matches the href attributes in the HTML
            href_pattern = r'href="(/apps\?url=([^"]+))"'
            matches = re.findall(href_pattern, page_source)
            
            if not matches:
                print("INFO: No href patterns found, trying alternative patterns...")
                # Try alternative pattern without the /apps prefix
                href_pattern = r'href="([^"]*url=([^"]+))"'
                matches = re.findall(href_pattern, page_source)
            
            if matches:
                print(f"INFO: Found {len(matches)} href matches")
                
                # For each href match, extract the surrounding HTML to get app data
                for i, (full_href, encoded_url) in enumerate(matches[:max_apps]):
                    try:
                        # Decode the URL
                        import urllib.parse
                        decoded_url = urllib.parse.unquote(encoded_url)
                        
                        # Extract app data from the HTML block containing this href
                        app_data = self.extract_app_data_from_href_block(page_source, full_href, decoded_url, i + 1)
                        
                        if app_data:
                            apps.append(app_data)
                            print(f"INFO: Extracted app {app_data['rank']}: {app_data['app_name']} - {app_data['tokens']} - URL: {app_data['app_url']}")
                    
                    except Exception as e:
                        print(f"WARNING: Error processing href match {i+1}: {e}")
                        continue
            
            return apps
            
        except Exception as e:
            print(f"ERROR: Error extracting apps from HTML: {e}")
            return []
    
    def extract_app_data_from_href_block(self, page_source, href, decoded_url, rank):
        """
        Extract app data from the HTML block containing the href
        
        Args:
            page_source (str): Full HTML page source
            href (str): The href attribute value
            decoded_url (str): The decoded URL
            rank (int): App rank
            
        Returns:
            dict: App data dictionary or None
        """
        try:
            # Find the position of this href in the page source
            href_pos = page_source.find(href)
            if href_pos == -1:
                return None
            
            # Extract a block of HTML around this href (500 characters before and after)
            start_pos = max(0, href_pos - 500)
            end_pos = min(len(page_source), href_pos + 500)
            html_block = page_source[start_pos:end_pos]
            
            # Look for the app name in the same block
            # Pattern: <a ... href="...">AppName</a>
            app_name_pattern = rf'<a[^>]*href="{re.escape(href)}"[^>]*>([^<]+)</a>'
            app_name_match = re.search(app_name_pattern, html_block)
            
            if not app_name_match:
                # Try alternative pattern
                app_name_pattern = rf'href="{re.escape(href)}"[^>]*>([^<]+)</a>'
                app_name_match = re.search(app_name_pattern, html_block)
            
            app_name = app_name_match.group(1).strip() if app_name_match else f"App {rank}"
            
            # Look for description in the same block
            # Pattern: <div class="truncate text-xs text-slate-9">Description</div>
            desc_pattern = r'<div[^>]*class="[^"]*truncate[^"]*text-xs[^"]*"[^>]*>([^<]+)</div>'
            desc_match = re.search(desc_pattern, html_block)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Look for tokens in the same block
            # Pattern: <span class="text-sm font-medium text-muted-foreground">3.54B</span><span class="text-xs text-slate-9 ml-1">tokens</span>
            tokens_pattern = r'<span[^>]*class="[^"]*text-sm[^"]*font-medium[^"]*"[^>]*>([^<]+)</span><span[^>]*class="[^"]*text-xs[^"]*"[^>]*>tokens</span>'
            tokens_match = re.search(tokens_pattern, html_block)
            
            if tokens_match:
                tokens_value = tokens_match.group(1).strip()
                tokens = f"{tokens_value}tokens"
            else:
                # Try alternative pattern
                tokens_pattern = r'(\d+\.?\d*[BMK]?)tokens'
                tokens_match = re.search(tokens_pattern, html_block)
                tokens = tokens_match.group(0) if tokens_match else "Unknown tokens"
            
            # Check for "new" label
            is_new = 'new' in html_block.lower()
            
            # Use the decoded URL as the app URL
            app_url = decoded_url
            
            return {
                'rank': rank,
                'app_name': app_name,
                'description': description,
                'tokens': tokens,
                'is_new': is_new,
                'app_url': app_url,
                'domain': self.extract_domain_from_url(decoded_url)
            }
            
        except Exception as e:
            print(f"WARNING: Error extracting app data from href block: {e}")
            return None
    
    def extract_domain_from_url(self, url):
        """
        Extract domain from URL
        
        Args:
            url (str): Full URL
            
        Returns:
            str: Domain name
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""
    
    def extract_app_data_from_lines(self, lines, start_index, rank, time_period="Today"):
        """
        Extract app data from lines starting at start_index
        """
        try:
            app_name = ""
            description = ""
            tokens = ""
            is_new = False
            domain = ""
            
            # Look ahead up to 10 lines for app data
            for j in range(start_index, min(start_index + 10, len(lines))):
                line = lines[j].strip()
                
                if not line:
                    continue
                
                # Look for favicon line to get domain
                if 'Favicon for https://' in line:
                    domain_match = re.search(r'Favicon for https://([^/]+)/', line)
                    if domain_match:
                        domain = domain_match.group(1)
                
                # Look for app name (first non-empty line that's not favicon, tokens, or "new")
                elif not app_name and line and not line.startswith('Favicon') and not line.endswith('tokens') and line.lower() != 'new':
                    app_name = line
                
                # Look for description (second non-empty line)
                elif app_name and not description and line and not line.startswith('Favicon') and not line.endswith('tokens') and line.lower() != 'new':
                    description = line
                
                # Look for tokens
                elif 'tokens' in line.lower():
                    tokens = line
                    break
                
                # Look for "new" label
                elif line.lower() == 'new':
                    is_new = True
            
            if app_name and tokens:
                # Generate app URL
                if domain:
                    app_url = f"https://{domain}"
                else:
                    app_url = f"https://openrouter.ai/apps/{app_name.lower().replace(' ', '-').replace(':', '').replace('.', '')}"
                
                return {
                    'rank': rank,
                    'app_name': app_name,
                    'description': description,
                    'tokens': tokens,
                    'is_new': is_new,
                    'app_url': app_url,
                    'domain': domain,
                    'image_url': "",
                    'time_period': time_period
                }
            
            return None
            
        except Exception as e:
            print(f"WARNING: Error extracting app data for rank {rank}: {e}")
            return None
    
    def parse_apps_alternative(self, page_text, max_apps=20, time_period="Today"):
        """
        Alternative method to parse apps using regex patterns
        """
        apps = []
        try:
            print("INFO: Using alternative parsing method...")
            
            # Look for patterns like "1. Kilo Code AI coding agent for VS Code 99.2Btokens"
            pattern = r'(\d+)\.\s*([^<\n]+?)\s*([^<\n]+?)\s*([\d.]+[BMK]?tokens)'
            matches = re.findall(pattern, page_text, re.MULTILINE | re.DOTALL)
            
            for i, match in enumerate(matches[:max_apps]):
                try:
                    rank = int(match[0])
                    app_name = match[1].strip()
                    description = match[2].strip()
                    tokens = match[3].strip()
                    
                    # Check for "new" label
                    is_new = 'new' in description.lower() or 'new' in app_name.lower()
                    
                    # Generate app URL
                    app_url = f"https://openrouter.ai/apps/{app_name.lower().replace(' ', '-').replace(':', '').replace('.', '')}"
                    
                    app_data = {
                        'rank': rank,
                        'app_name': app_name,
                        'description': description,
                        'tokens': tokens,
                        'is_new': is_new,
                        'app_url': app_url,
                        'domain': '',
                        'image_url': '',
                        'time_period': time_period
                    }
                    
                    apps.append(app_data)
                    print(f"INFO: Found app {rank}: {app_name} - {tokens}")
                    
                except Exception as e:
                    print(f"WARNING: Error processing match {match}: {e}")
                    continue
            
            return apps
            
        except Exception as e:
            print(f"ERROR: Error in alternative parsing: {e}")
            return []
    
    def save_to_csv(self, apps_data, filename=None):
        """Save apps data to CSV file"""
        if not apps_data:
            print("ERROR: No apps data to save")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"openrouter_top_apps_{timestamp}.csv"
        
        try:
            print(f"INFO: Saving apps data to {filename}...")
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['rank', 'app_name', 'description', 'tokens', 'is_new', 'app_url', 'domain', 'image_url', 'time_period']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for app in apps_data:
                    writer.writerow(app)
            
            print(f"SUCCESS: Apps data saved to {filename}")
            
        except Exception as e:
            print(f"ERROR: Error saving apps data to CSV: {e}")
    
    def save_to_json(self, apps_data, filename=None):
        """Save apps data to JSON file"""
        if not apps_data:
            print("ERROR: No apps data to save")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"openrouter_top_apps_{timestamp}.json"
        
        try:
            print(f"INFO: Saving apps data to {filename}...")
            
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(apps_data, jsonfile, indent=2, ensure_ascii=False)
            
            print(f"SUCCESS: Apps data saved to {filename}")
            
        except Exception as e:
            print(f"ERROR: Error saving apps data to JSON: {e}")

    def save_to_supabase(self, apps_data, time_period="Today"):
        """Save apps data to Supabase"""
        if not apps_data:
            print("ERROR: No apps data to save")
            return False
        
        if not self.supabase:
            print("ERROR: Supabase client not initialized")
            return False
        
        try:
            print(f"INFO: Saving {len(apps_data)} apps to Supabase...")
            
            # Prepare data for insertion
            for app in apps_data:
                app['time_period'] = time_period
                app['scraped_at'] = datetime.now().isoformat()
            
            # Insert data into Supabase
            result = self.supabase.table('openrouter_apps').insert(apps_data).execute()
            
            print(f"SUCCESS: {len(apps_data)} apps saved to Supabase")
            return True
            
        except Exception as e:
            print(f"ERROR: Error saving to Supabase: {e}")
            return False
    
    def save_to_structured_json(self, time_period_data, filename=None):
        """Save apps data to JSON file organized by time periods (fallback)"""
        if not time_period_data:
            print("ERROR: No time period data to save")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"openrouter_top_apps_structured_{timestamp}.json"
        
        try:
            print(f"INFO: Saving structured apps data to {filename}...")
            
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(time_period_data, jsonfile, indent=2, ensure_ascii=False)
            
            print(f"SUCCESS: Structured apps data saved to {filename}")
            
        except Exception as e:
            print(f"ERROR: Error saving structured apps data to JSON: {e}")

    
    def print_results(self, apps_data, time_period="Today"):
        """Print formatted apps results"""
        if not apps_data:
            print("ERROR: No apps data to display")
            return
        
        print("\n" + "="*100)
        print(f"OPENROUTER TOP APPS - {time_period.upper()} - DYNAMICALLY SCRAPED")
        print("="*100)
        
        for app in apps_data:
            new_indicator = " [NEW]" if app.get('is_new', False) else ""
            print(f"{app['rank']:2d}. {app.get('app_name', 'Unknown'):<30} | {app.get('description', 'Unknown'):<40} | {app.get('tokens', 'Unknown'):<12}{new_indicator}")
        
        print("="*100)


def main():
    """Main function to run the apps scraper"""
    print("Starting OpenRouter Top Apps Scraper")
    print("="*60)
    
    try:
        scraper = OpenRouterAppsScraper()
        
        # Scrape Top Apps for Today (default)
        apps_data = scraper.scrape_top_apps(max_apps=20, time_period="Today")
        
        if apps_data:
            # Print results
            scraper.print_results(apps_data, "Today")
            
            # Save data to Supabase
            if scraper.save_to_supabase(apps_data, "Today"):
                print(f"\nSUCCESS: Top Apps scraping completed successfully!")
                print(f"INFO: Total apps scraped: {len(apps_data)}")
            else:
                print("WARNING: Failed to save to Supabase, saving to files as fallback")
                scraper.save_to_csv(apps_data)
                scraper.save_to_json(apps_data)
        else:
            print("ERROR: No apps data was scraped from the live website")
    
    except Exception as e:
        print(f"ERROR: Error in main execution: {e}")


def main_all_periods():
    """Main function to run the apps scraper for all time periods"""
    print("Starting OpenRouter Top Apps Scraper - All Time Periods")
    print("="*60)
    
    try:
        scraper = OpenRouterAppsScraper()
        
        # Define time periods to scrape
        time_periods = ["Today", "This Week", "This Month"]
        all_apps_data = []
        structured_data = {}
        
        for time_period in time_periods:
            print(f"\n" + "="*80)
            print(f"SCRAPING TOP APPS - {time_period.upper()}")
            print("="*80)
            
            apps_data = scraper.scrape_top_apps(max_apps=20, time_period=time_period)
            
            if apps_data:
                # Print results for this time period
                scraper.print_results(apps_data, time_period)
                
                # Add to combined data
                all_apps_data.extend(apps_data)
                
                # Add to structured data organized by time period
                structured_data[time_period] = apps_data
                
                print(f"\nSUCCESS: {time_period} scraping completed successfully!")
                print(f"INFO: Total apps scraped for {time_period}: {len(apps_data)}")
            else:
                print(f"ERROR: No apps data was scraped for {time_period}")
                # Add empty list for failed time period
                structured_data[time_period] = []
        
        # Save data to Supabase
        if all_apps_data:
            print(f"\n" + "="*80)
            print("SAVING DATA")
            print("="*80)
            
            # Save each time period to Supabase
            success_count = 0
            for time_period, apps_data in structured_data.items():
                if apps_data:
                    if scraper.save_to_supabase(apps_data, time_period):
                        success_count += 1
                        print(f"SUCCESS: {time_period} data saved to Supabase")
                    else:
                        print(f"WARNING: Failed to save {time_period} data to Supabase")
            
            if success_count > 0:
                print(f"\nSUCCESS: All time periods scraping completed successfully!")
                print(f"INFO: Total apps scraped across all periods: {len(all_apps_data)}")
                print(f"INFO: {success_count}/{len(structured_data)} time periods saved to Supabase")
            else:
                print("WARNING: Failed to save any data to Supabase, saving to JSON as fallback")
                scraper.save_to_structured_json(structured_data, "openrouter_top_apps_structured")
        else:
            print("ERROR: No apps data was scraped from any time period")
    
    except Exception as e:
        print(f"ERROR: Error in main execution: {e}")

if __name__ == "__main__":
    # Run the scraper for all time periods
    main_all_periods()

