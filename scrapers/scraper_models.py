"""
OpenRouter Perfect All Time Periods Scraper
Scrapes all time periods (Top today, Top this week, Top this month, Trending) with perfect data extraction
Handles all edge cases including "new" labels, missing percentages, and trend detection issues
"""

import csv
import json
import time
import re
import os
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client, Client


class OpenRouterPerfectAllPeriodsScraper:
    def __init__(self):
        """Initialize the perfect all periods scraper"""
        self.all_data = {}  # Store data for all time periods
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
    
    def click_time_period_option(self, time_period):
        """Click on a specific time period option"""
        try:
            print(f"INFO: Looking for '{time_period}' option...")
            
            # Wait for the page to load
            time.sleep(5)
            
            # Try different possible selectors for the time period options
            time_period_selectors = [
                f"//button[contains(text(), '{time_period}')]",
                f"//*[contains(text(), '{time_period}')]",
                f"//div[contains(text(), '{time_period}')]",
                f"//span[contains(text(), '{time_period}')]",
                f"//a[contains(text(), '{time_period}')]",
                f"[data-value*='{time_period.lower()}']",
                f"[data-value*='{time_period.lower().replace(' ', '_')}']",
                f"[data-value*='{time_period.lower().replace(' ', '-')}']"
            ]
            
            time_period_element = None
            
            # Try to find the element
            for selector in time_period_selectors:
                try:
                    if selector.startswith("//"):
                        time_period_element = self.driver.find_element(By.XPATH, selector)
                    else:
                        time_period_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if time_period_element and time_period_element.is_displayed():
                        print(f"SUCCESS: Found '{time_period}' option with selector: {selector}")
                        break
                except:
                    continue
            
            # If still not found, try to find any clickable element that might be the time period option
            if not time_period_element:
                print(f"INFO: Trying to find any clickable element that might be '{time_period}'...")
                clickable_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{time_period}')]")
                for element in clickable_elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            time_period_element = element
                            print(f"SUCCESS: Found potential '{time_period}' element with text: '{element.text}'")
                            break
                    except:
                        continue
            
            if time_period_element:
                # Try multiple methods to click the element
                success = False
                
                # Method 1: Regular click
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", time_period_element)
                    time.sleep(2)
                    time_period_element.click()
                    success = True
                    print(f"SUCCESS: Regular click worked for '{time_period}'")
                except Exception as e:
                    print(f"WARNING: Regular click failed for '{time_period}': {e}")
                
                # Method 2: JavaScript click
                if not success:
                    try:
                        self.driver.execute_script("arguments[0].click();", time_period_element)
                        success = True
                        print(f"SUCCESS: JavaScript click worked for '{time_period}'")
                    except Exception as e:
                        print(f"WARNING: JavaScript click failed for '{time_period}': {e}")
                
                # Method 3: ActionChains click
                if not success:
                    try:
                        actions = ActionChains(self.driver)
                        actions.move_to_element(time_period_element).click().perform()
                        success = True
                        print(f"SUCCESS: ActionChains click worked for '{time_period}'")
                    except Exception as e:
                        print(f"WARNING: ActionChains click failed for '{time_period}': {e}")
                
                if success:
                    # Wait for the content to load
                    print(f"INFO: Waiting for '{time_period}' content to load...")
                    time.sleep(10)
                    
                    # Scroll to trigger any lazy loading
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(3)
                    
                    print(f"SUCCESS: '{time_period}' option clicked successfully")
                    return True
                else:
                    print(f"ERROR: All click methods failed for '{time_period}'")
                    return False
            else:
                print(f"WARNING: '{time_period}' option not found")
                return False
                
        except Exception as e:
            print(f"ERROR: Error clicking '{time_period}' option: {e}")
            return False
    
    def click_show_more_button(self):
        """Click the 'Show more' button to reveal all models"""
        try:
            print("INFO: Looking for 'Show more' button...")
            
            # Wait for the page to load completely first
            time.sleep(5)
            
            # Scroll down to make sure the button is visible
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Try different possible selectors for the "Show more" button
            show_more_selectors = [
                "//button[contains(text(), 'Show more')]",
                "//button[contains(text(), 'show more')]",
                "//button[contains(text(), 'Show More')]",
                "//button[contains(text(), 'SHOW MORE')]",
                "//button[contains(@class, 'show-more')]",
                "//button[contains(@class, 'expand')]",
                "//button[contains(@class, 'more')]",
                "//*[contains(text(), 'Show more')]",
                "//*[contains(text(), 'show more')]"
            ]
            
            show_more_button = None
            
            # Try to find the button
            for xpath in show_more_selectors:
                try:
                    show_more_button = self.driver.find_element(By.XPATH, xpath)
                    if show_more_button and show_more_button.is_displayed():
                        print(f"SUCCESS: Found 'Show more' button with XPath: {xpath}")
                        break
                except:
                    continue
            
            if show_more_button:
                # Try multiple methods to click the button
                success = False
                
                # Method 1: Regular click
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_more_button)
                    time.sleep(2)
                    show_more_button.click()
                    success = True
                    print("SUCCESS: Regular click worked")
                except Exception as e:
                    print(f"WARNING: Regular click failed: {e}")
                
                # Method 2: JavaScript click
                if not success:
                    try:
                        self.driver.execute_script("arguments[0].click();", show_more_button)
                        success = True
                        print("SUCCESS: JavaScript click worked")
                    except Exception as e:
                        print(f"WARNING: JavaScript click failed: {e}")
                
                if success:
                    # Wait for the additional models to load
                    print("INFO: Waiting for additional models to load...")
                    time.sleep(15)
                    
                    # Scroll to trigger any lazy loading
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(5)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(5)
                    
                    print("SUCCESS: 'Show more' button clicked successfully")
                    return True
                else:
                    print("ERROR: All click methods failed")
                    return False
            else:
                print("WARNING: 'Show more' button not found - will scrape only visible models")
                return False
                
        except Exception as e:
            print(f"ERROR: Error clicking 'Show more' button: {e}")
            return False
    
    def scrape_time_period(self, time_period, max_models=20):
        """
        Scrape models for a specific time period
        
        Args:
            time_period (str): Time period to scrape (e.g., "Top today", "Top this week")
            max_models (int): Maximum number of models to scrape
            
        Returns:
            list: List of model data dictionaries
        """
        try:
            print(f"INFO: Scraping {time_period}...")
            
            # Click on the time period option
            if not self.click_time_period_option(time_period):
                print(f"WARNING: Could not click '{time_period}' option, trying to scrape current view...")
            
            # Click "Show more" button to reveal all models
            self.click_show_more_button()
            
            # Wait a bit more for all content to load
            time.sleep(10)
            
            # Wait for model rankings to actually appear in the HTML
            print("INFO: Waiting for model rankings to load in HTML...")
            max_wait_time = 30  # Maximum wait time in seconds
            wait_interval = 2   # Check every 2 seconds
            waited_time = 0
            
            while waited_time < max_wait_time:
                page_source = self.driver.page_source
                
                # Check if model rankings are present in the HTML
                if "Anthropic: Claude" in page_source or "Google: Gemini" in page_source or "OpenAI: GPT" in page_source:
                    print(f"SUCCESS: Model rankings found in HTML after {waited_time} seconds")
                    break
                else:
                    print(f"INFO: Model rankings not yet in HTML, waiting... ({waited_time}s)")
                    time.sleep(wait_interval)
                    waited_time += wait_interval
            
            if waited_time >= max_wait_time:
                print("WARNING: Model rankings not found in HTML after maximum wait time")
            
            # Get final page source for trend detection
            page_source = self.driver.page_source
            
            # Extract model URLs from page source
            model_urls_cache = self.extract_model_urls_from_page(page_source)
            
            # Get page text for model data
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Parse the text to extract model data
            models = self.parse_text_data_perfect(page_text, page_source, max_models, time_period, model_urls_cache)
            
            # Add timestamp to each model
            for model in models:
                model['scraped_at'] = datetime.now().isoformat()
            
            print(f"SUCCESS: Successfully scraped {len(models)} models for {time_period}")
            return models
            
        except Exception as e:
            print(f"ERROR: Error scraping {time_period}: {e}")
            return []
    
    def parse_text_data_perfect(self, text, page_source, max_models, time_period, model_urls_cache=None):
        """Parse the text data to extract model information with perfect trend detection"""
        models = []
        lines = text.split('\n')
        
        # Look for the pattern: rank. model_name by author tokens trend%
        i = 0
        while i < len(lines) and len(models) < max_models:
            line = lines[i].strip()
            
            # Check if this line contains a rank number
            if re.match(r'^\d+\.$', line):
                try:
                    rank = int(line[:-1])  # Remove the dot
                    
                    # Get model name from next line
                    if i + 1 < len(lines):
                        model_name = lines[i + 1].strip()
                        
                        # Get author from lines after "by"
                        author = None
                        tokens = None
                        trend_percentage = None
                        trend_direction = None
                        
                        # Look for "by" and extract author
                        for j in range(i + 2, min(i + 10, len(lines))):
                            if lines[j].strip() == 'by' and j + 1 < len(lines):
                                author = lines[j + 1].strip()
                                break
                        
                        # Look for tokens (contains "tokens")
                        for j in range(i + 2, min(i + 10, len(lines))):
                            if 'tokens' in lines[j].lower():
                                tokens = lines[j].strip()
                                break
                        
                        # Look for trend percentage - IMPROVED TO HANDLE "new" and comma-separated numbers
                        for j in range(i + 2, min(i + 10, len(lines))):
                            line_text = lines[j].strip()
                            # Check for percentage pattern (supports commas like 1,000%)
                            if re.match(r'^[\d,]+%$', line_text):
                                trend_percentage = line_text
                                break
                            # Check for "new" pattern
                            elif line_text.lower() == 'new':
                                trend_percentage = 'new'
                                break
                        
                        # Create model data with perfect trend detection
                        if model_name and author:
                            # Perfect trend detection from page source
                            trend_info = self.detect_trend_perfect(model_name, rank, page_source, trend_percentage)
                            
                            model_data = {
                                'rank': rank,
                                'model_name': model_name,
                                'author': author,
                                'tokens': tokens or 'Unknown',
                                'trend_percentage': trend_percentage or 'Unknown',
                                'trend_direction': trend_info['direction'],
                                'trend_icon': trend_info['icon'],
                                'trend_color': trend_info['color'],
                                'time_period': time_period
                            }
                            
                            # Add model URL based on author
                            model_data['model_url'] = self.get_model_url(model_name, author, model_urls_cache)
                            model_data['author_url'] = f"https://openrouter.ai/{author}"
                            
                            # Add logo URL using Google favicon service
                            logo_url = self.get_logo_url(author)
                            model_data['logo_url'] = logo_url
                            
                            models.append(model_data)
                            print(f"INFO: Model {rank}: {model_name} - {trend_info['icon']} {trend_percentage} ({trend_info['direction']}) - Logo: {logo_url[:50]}... - PERFECTLY DETECTED")
                
                except Exception as e:
                    print(f"WARNING: Error parsing rank {line}: {e}")
            
            i += 1
        
        return models
    
    def detect_trend_perfect(self, model_name, rank, page_source, trend_percentage):
        """Perfect trend detection - ONLY SVG PATH DETECTION, NO OTHER PRIORITIES"""
        try:
            # If trend_percentage is "new", it's always an up trend
            if trend_percentage == 'new':
                print(f"DEBUG: Model '{model_name}' is marked as 'new' - defaulting to up trend")
                return {'direction': 'up', 'icon': '^', 'color': 'green'}
            
            # SVG trend paths - THESE ARE THE ONLY PRIORITY
            up_trend_path = 'M11.47 2.47a.75.75 0 0 1 1.06 0l7.5 7.5a.75.75 0 1 1-1.06 1.06l-6.22-6.22V21a.75.75 0 0 1-1.5 0V4.81l-6.22 6.22a.75.75 0 1 1-1.06-1.06l7.5-7.5Z'
            down_trend_path = 'M12 2.25a.75.75 0 0 1 .75.75v16.19l6.22-6.22a.75.75 0 1 1 1.06 1.06l-7.5 7.5a.75.75 0 0 1-1.06 0l-7.5-7.5a.75.75 0 1 1 1.06-1.06l6.22 6.22V3a.75.75 0 0 1 .75-.75Z'
            
            print(f"DEBUG: Looking for trend SVG paths for model '{model_name}' (rank {rank})")
            
            # Find the complete model block by looking for the rank pattern
            rank_pattern = f'<div class="text-muted-foreground col-span-1 text-left">{rank}.</div>'
            rank_matches = list(re.finditer(re.escape(rank_pattern), page_source))
            
            if not rank_matches:
                print(f"DEBUG: Rank {rank} pattern not found, trying alternative pattern")
                # Try alternative rank pattern
                rank_pattern = f'col-span-1 text-left">{rank}.'
                rank_matches = list(re.finditer(re.escape(rank_pattern), page_source))
            
            if rank_matches:
                print(f"DEBUG: Found {len(rank_matches)} rank {rank} patterns")
                
                for i, rank_match in enumerate(rank_matches):
                    # Get the position of this rank
                    rank_start = rank_match.start()
                    
                    # Look for the next rank or end of content to define the model block
                    next_rank_pattern = f'<div class="text-muted-foreground col-span-1 text-left">{rank + 1}.</div>'
                    next_rank_match = re.search(re.escape(next_rank_pattern), page_source[rank_start:])
                    
                    if next_rank_match:
                        # Model block ends at the next rank
                        model_block_end = rank_start + next_rank_match.start()
                    else:
                        # No next rank found, look for the end of the current div structure
                        # Find the closing </div></div> pattern that ends the model block
                        model_block_end = rank_start + 2000  # Fallback: look ahead 2000 characters
                        closing_pattern = '</div></div><div class="grid grid-cols-12 items-center">'
                        closing_match = re.search(re.escape(closing_pattern), page_source[rank_start:rank_start + 2000])
                        if closing_match:
                            model_block_end = rank_start + closing_match.start()
                    
                    # Extract the model block
                    model_block = page_source[rank_start:model_block_end]
                    
                    print(f"DEBUG: Model block {i+1} length: {len(model_block)} characters")
                    
                    # Check if this model block contains the model name
                    if model_name.lower() in model_block.lower():
                        print(f"DEBUG: Found model '{model_name}' in block {i+1}")
                        
                        # Look for SVG paths in this specific model block
                        if down_trend_path in model_block:
                            print(f"DEBUG: Found DOWN trend SVG in model block {i+1} - EXACT MATCH")
                            return {'direction': 'down', 'icon': 'v', 'color': 'red'}
                        
                        if up_trend_path in model_block:
                            print(f"DEBUG: Found UP trend SVG in model block {i+1} - EXACT MATCH")
                            return {'direction': 'up', 'icon': '^', 'color': 'green'}
                        
                        print(f"DEBUG: No trend SVG found in model block {i+1}")
                    else:
                        print(f"DEBUG: Model '{model_name}' not found in block {i+1}")
            else:
                print(f"DEBUG: No rank {rank} pattern found in page source")
            
            # If no trend found in the specific model block, default based on trend_percentage
            if trend_percentage and trend_percentage != 'Unknown':
                try:
                    clean_percentage = trend_percentage.replace(',', '').replace('%', '')
                    if clean_percentage.lstrip('-').isdigit():
                        percentage_value = float(clean_percentage)
                        if percentage_value > 0:
                            print(f"DEBUG: No SVG found, using positive percentage {percentage_value}% - defaulting to up")
                            return {'direction': 'up', 'icon': '^', 'color': 'green'}
                        elif percentage_value < 0:
                            print(f"DEBUG: No SVG found, using negative percentage {percentage_value}% - defaulting to down")
                            return {'direction': 'down', 'icon': 'v', 'color': 'red'}
                except:
                    pass
            
            # Final fallback
            print(f"DEBUG: No trend SVG found for model '{model_name}' - defaulting to stable")
            return {'direction': 'stable', 'icon': '->', 'color': 'gray'}
                
        except Exception as e:
            print(f"ERROR: Error detecting trend for model '{model_name}': {e}")
            # Default to up trend for new models, stable for others
            if trend_percentage == 'new':
                return {'direction': 'up', 'icon': '^', 'color': 'green'}
            else:
                return {'direction': 'stable', 'icon': '->', 'color': 'gray'}
    
    def extract_model_urls_from_page(self, page_source):
        """Extract model URLs from page source by finding href attributes"""
        model_urls = {}
        try:
            # Look for href attributes that point to model pages
            # Pattern: href="/author/model-name" or href="https://openrouter.ai/author/model-name"
            import re
            
            # Find all href attributes that look like model URLs
            # Pattern matches: href="/author/model-name", href="https://openrouter.ai/author/model-name"
            href_pattern = r'href=["\']([^"\']*(?:openrouter\.ai/[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_:\.]+|/[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_:\.]+))["\']'
            matches = re.findall(href_pattern, page_source)
            
            for match in matches:
                # Clean up the URL
                if match.startswith('/'):
                    url = f"https://openrouter.ai{match}"
                elif match.startswith('https://openrouter.ai'):
                    url = match
                else:
                    continue
                
                # Extract author and model from URL path
                # Expected format: https://openrouter.ai/author/model-name
                url_parts = url.split('/')
                if len(url_parts) >= 4:
                    author = url_parts[-2]  # Second to last part
                    model_path = url_parts[-1]  # Last part
                    
                    # Store the URL with author as key for lookup
                    if author not in model_urls:
                        model_urls[author] = {}
                    model_urls[author][model_path] = url
            
            print(f"INFO: Extracted {len(model_urls)} author URLs from page")
            return model_urls
            
        except Exception as e:
            print(f"WARNING: Error extracting model URLs from page: {e}")
            return {}
    
    def get_model_url(self, model_name, author, model_urls_cache=None):
        """Get model URL from extracted URLs or generate fallback URL"""
        try:
            # First try to find the URL from extracted URLs
            if model_urls_cache and author in model_urls_cache:
                # Try to match by model name in the URL paths
                model_name_clean = model_name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace(' ', '-')
                
                for model_path, url in model_urls_cache[author].items():
                    # Improved matching logic to handle colons and other special characters
                    model_path_clean = model_path.lower()
                    
                    # Try multiple matching strategies
                    match_found = False
                    
                    # Strategy 1: Exact match after cleaning
                    if model_name_clean == model_path_clean:
                        match_found = True
                    
                    # Strategy 2: Check if the core model name (before colon) matches
                    elif ':' in model_path:
                        core_model_path = model_path_clean.split(':')[0]
                        if (model_name_clean in core_model_path or 
                            core_model_path in model_name_clean):
                            match_found = True
                    
                    # Strategy 3: Original logic for other cases
                    elif (model_name_clean in model_path_clean or 
                          model_path_clean in model_name_clean):
                        match_found = True
                    
                    if match_found:
                        print(f"INFO: Found exact URL for {model_name}: {url}")
                        return url
            
            # Fallback: generate URL based on standard pattern
            url_name = model_name.lower().replace(' ', '-').replace('(', '').replace(')', '')
            fallback_url = f"https://openrouter.ai/{author}/{url_name}"
            print(f"INFO: Using fallback URL for {model_name}: {fallback_url}")
            return fallback_url
            
        except Exception as e:
            print(f"WARNING: Error getting model URL for {model_name}: {e}")
            # Ultimate fallback
            url_name = model_name.lower().replace(' ', '-').replace('(', '').replace(')', '')
            return f"https://openrouter.ai/{author}/{url_name}"
    
    def get_logo_url(self, author):
        """Generate Google favicon URL for model author"""
        try:
            # Map common authors to their actual domains for better favicon results
            author_domain_map = {
                'OpenAI': 'openai.com',
                'Anthropic': 'anthropic.com',
                'Google': 'google.com',
                'Meta': 'meta.com',
                'Microsoft': 'microsoft.com',
                'Cohere': 'cohere.com',
                'Mistral AI': 'mistral.ai',
                'Hugging Face': 'huggingface.co',
                'Stability AI': 'stability.ai',
                'ElevenLabs': 'elevenlabs.io',
                'Perplexity': 'perplexity.ai',
                'DeepSeek': 'deepseek.com',
                'Qwen': 'qwenlm.com',
                'Claude': 'anthropic.com',
                'GPT': 'openai.com',
                'Gemini': 'google.com',
                'Llama': 'meta.com',
                'PaLM': 'google.com',
                'Vicuna': 'lmsys.org',
                'Alpaca': 'crfm.stanford.edu',
                'WizardLM': 'wizardlm.ai',
                'CodeLlama': 'meta.com',
                'Falcon': 'falconllm.tii.ae',
                'MPT': 'mosaicml.com',
                'RedPajama': 'together.ai',
                'OpenAssistant': 'open-assistant.io',
                'Dolly': 'databricks.com',
                'Cerebras': 'cerebras.net',
                'Baichuan': 'baichuan-ai.com',
                'Zhipu': 'zhipuai.cn',
                'GLM': 'zhipuai.cn',
                'ChatGLM': 'zhipuai.cn',
                'InternLM': 'internlm.org',
                'Qwen': 'qwenlm.com',
                'Yi': '01.ai',
                'DeepSeek': 'deepseek.com',
                'Moonshot': 'moonshot.cn',
                'MiniMax': 'minimax.chat',
                'Abab': 'abab.ai',
                'Baichuan': 'baichuan-ai.com',
                'Zhipu': 'zhipuai.cn',
                'GLM': 'zhipuai.cn',
                'ChatGLM': 'zhipuai.cn',
                'InternLM': 'internlm.org',
                'Qwen': 'qwenlm.com',
                'Yi': '01.ai',
                'DeepSeek': 'deepseek.com',
                'Moonshot': 'moonshot.cn',
                'MiniMax': 'minimax.chat',
                'Abab': 'abab.ai'
            }
            
            # Get the domain for the author
            domain = author_domain_map.get(author, f"{author.lower().replace(' ', '').replace('-', '')}.com")
            
            # Generate Google favicon URL
            # Format: https://t0.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://domain.com&size=256
            encoded_domain = urllib.parse.quote(f"https://{domain}", safe='')
            favicon_url = f"https://t0.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url={encoded_domain}&size=256"
            
            print(f"INFO: Generated favicon URL for {author}: {favicon_url}")
            return favicon_url
            
        except Exception as e:
            print(f"WARNING: Error generating favicon URL for {author}: {e}")
            # Fallback to a generic favicon
            return "https://t0.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://openrouter.ai&size=256"
    
    def scrape_all_time_periods(self, max_models=20):
        """
        Scrape all time periods from the OpenRouter website
        
        Args:
            max_models (int): Maximum number of models to scrape per period (default 20)
            
        Returns:
            dict: Dictionary with time periods as keys and model data as values
        """
        if not self.setup_driver():
            return {}
        
        try:
            print("INFO: Navigating to OpenRouter rankings page...")
            self.driver.get("https://openrouter.ai/rankings")
            
            # Wait for the page to load completely
            print("INFO: Waiting for page to load completely...")
            time.sleep(30)
            
            # Scroll to trigger content loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(5)
            
            # Define time periods to scrape
            time_periods = ["Top today", "Top this week", "Top this month", "Trending"]
            
            # Scrape each time period
            for time_period in time_periods:
                print(f"\n{'='*60}")
                print(f"SCRAPING {time_period.upper()}")
                print(f"{'='*60}")
                
                models = self.scrape_time_period(time_period, max_models)
                self.all_data[time_period] = models
                
                print(f"SUCCESS: Scraped {len(models)} models for {time_period}")
                
                # Wait between periods to avoid overwhelming the server
                time.sleep(5)
            
            print(f"\nSUCCESS: Successfully scraped all time periods!")
            total_models = sum(len(models) for models in self.all_data.values())
            print(f"INFO: Total models scraped across all periods: {total_models}")
            
            return self.all_data
            
        except Exception as e:
            print(f"ERROR: Error scraping all time periods: {e}")
            return {}
        
        finally:
            if self.driver:
                self.driver.quit()
                print("INFO: WebDriver closed")
    
    def save_to_csv(self, filename=None):
        """Save all scraped data to CSV file"""
        if not self.all_data:
            print("ERROR: No data to save")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"openrouter_models_scraper_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['rank', 'model_name', 'author', 'tokens', 'trend_percentage', 
                            'trend_direction', 'trend_icon', 'trend_color', 'model_url', 'author_url', 'logo_url', 'time_period', 'scraped_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for time_period, models in self.all_data.items():
                    for model in models:
                        writer.writerow(model)
            
            print(f"SUCCESS: Perfect all periods data saved to {filename}")
            
        except Exception as e:
            print(f"ERROR: Error saving to CSV: {e}")
    
    def save_to_supabase(self):
        """Save all scraped data to Supabase"""
        if not self.all_data:
            print("ERROR: No data to save")
            return False
        
        if not self.supabase:
            print("ERROR: Supabase client not initialized")
            return False
        
        try:
            print("INFO: Saving data to Supabase...")
            
            # Prepare data for insertion
            all_models = []
            for time_period, models in self.all_data.items():
                for model in models:
                    model['time_period'] = time_period
                    model['scraped_at'] = datetime.now().isoformat()
                    all_models.append(model)
            
            # Debug: Print sample data being sent to Supabase
            if all_models:
                sample_model = all_models[0]
                print(f"DEBUG: Sample model data being sent to Supabase:")
                print(f"DEBUG: - Author: {sample_model.get('author', 'MISSING')}")
                print(f"DEBUG: - Logo URL: {sample_model.get('logo_url', 'MISSING')}")
                print(f"DEBUG: - All keys: {list(sample_model.keys())}")
            
            # Insert data into Supabase
            result = self.supabase.table('openrouter_models').insert(all_models).execute()
            
            print(f"SUCCESS: {len(all_models)} models saved to Supabase")
            return True
            
        except Exception as e:
            print(f"ERROR: Error saving to Supabase: {e}")
            return False
    
    def save_to_json(self, filename=None):
        """Save all scraped data to JSON file (fallback)"""
        if not self.all_data:
            print("ERROR: No data to save")
            return
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"openrouter_perfect_all_periods_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.all_data, jsonfile, indent=2, ensure_ascii=False)
            
            print(f"SUCCESS: Perfect all periods data saved to {filename}")
            
        except Exception as e:
            print(f"ERROR: Error saving to JSON: {e}")
    
    def print_results(self):
        """Print the scraped results for all time periods"""
        if not self.all_data:
            print("ERROR: No data to display")
            return
        
        print("\n" + "="*100)
        print("OPENROUTER PERFECT ALL PERIODS DATA - SCRAPED FROM LIVE WEBSITE")
        print("="*100)
        
        for time_period, models in self.all_data.items():
            print(f"\n{time_period.upper()}:")
            print("-" * 80)
            
            for model in models:
                color_indicator = "[RED]" if model.get('trend_color') == 'red' else "[GREEN]" if model.get('trend_color') == 'green' else "[GRAY]" if model.get('trend_color') == 'gray' else "[UNKNOWN]"
                print(f"{model['rank']:2d}. {model.get('model_name', 'Unknown'):<30} | by {model.get('author', 'Unknown'):<15} | {model.get('tokens', 'Unknown'):<12} | {color_indicator} {model.get('trend_icon', '?')} {model.get('trend_percentage', 'Unknown')} ({model.get('trend_direction', 'unknown')})")
        
        print("="*100)
    
    
    def print_summary(self):
        """Print a summary of scraped data"""
        if not self.all_data:
            print("ERROR: No data to display")
            return
        
        print("\n" + "="*80)
        print("OPENROUTER PERFECT ALL PERIODS SUMMARY")
        print("="*80)
        
        total_models = 0
        for time_period, models in self.all_data.items():
            print(f"{time_period}: {len(models)} models")
            total_models += len(models)
        
        print(f"\nTotal models scraped: {total_models}")
        print("="*80)




def main():
    """Main function to run the perfect all periods scraper"""
    print("Starting OpenRouter Perfect All Time Periods Scraper")
    print("="*60)
    
    try:
        scraper = OpenRouterPerfectAllPeriodsScraper()
        
        # Scrape all time periods
        all_data = scraper.scrape_all_time_periods(max_models=20)
        
        if all_data:
            # Print results
            scraper.print_summary()
            scraper.print_results()
            
            # Save data to Supabase
            if scraper.save_to_supabase():
                print(f"\nSUCCESS: Perfect all periods scraping completed successfully!")
                total_models = sum(len(models) for models in all_data.values())
                print(f"INFO: Total models scraped across all periods: {total_models}")
            else:
                print("WARNING: Failed to save to Supabase, saving to JSON as fallback")
                scraper.save_to_json()
        else:
            print("ERROR: No data was scraped from the live website")
    
    except Exception as e:
        print(f"ERROR: Error in main execution: {e}")


if __name__ == "__main__":
    import sys
    
    # Run the models scraper
    main()
