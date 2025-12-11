"""
Content Extractor Module
Handles extracting content from various sources (blogs, YouTube, raw text)
"""

import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json
from urllib.parse import urlparse, parse_qs
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('content_extractor.log')  # File output
    ]
)

logger = logging.getLogger(__name__)


class ContentExtractor:

    # ---------------------------------------------------------------
    # YOUTUBE
    # ---------------------------------------------------------------
    @staticmethod
    def extract_youtube_id(url):
        """Extract video ID from YouTube URL"""
        logger.info(f"Extracting YouTube ID from URL: {url}")
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
            logger.info(f"Extracted video ID (youtu.be format): {video_id}")
            return video_id
        elif "youtube.com/watch" in url:
            parsed = urlparse(url)
            video_id = parse_qs(parsed.query).get("v", [None])[0]
            logger.info(f"Extracted video ID (youtube.com format): {video_id}")
            return video_id
        logger.warning(f"Could not extract video ID from URL: {url}")
        return None

    @staticmethod
    def get_youtube_transcript(url):
        """Extract transcript from YouTube video"""
        logger.info(f"Starting YouTube transcript extraction for: {url}")
        try:
            video_id = ContentExtractor.extract_youtube_id(url)
            if not video_id:
                logger.error("Invalid YouTube URL - no video ID found")
                return None, "Invalid YouTube URL"

            logger.info(f"Fetching transcript for video ID: {video_id}")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            logger.info(f"Successfully fetched transcript with {len(transcript_list)} segments")

            # Combine transcript text
            full_transcript = " ".join([item["text"] for item in transcript_list])
            full_transcript = re.sub(r"\s+", " ", full_transcript)

            logger.info(f"Transcript extracted successfully. Length: {len(full_transcript)} characters")
            return full_transcript.strip(), None

        except Exception as e:
            logger.error(f"Error extracting YouTube transcript: {str(e)}", exc_info=True)
            return None, f"Error extracting YouTube transcript: {str(e)}"

    # ---------------------------------------------------------------
    # BLOG SCRAPER (Uber, Medium, Substack, Generic)
    # ---------------------------------------------------------------
    @staticmethod
    def scrape_blog_post(url):
        """Scrape content from any blog URL. Handles Uber, Medium, WP, Substack, etc."""
        logger.info(f"Starting blog scraping for URL: {url}")
        try:
            headers = {
                "User-Agent": (
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                 "AppleWebKit/537.36 (KHTML, like Gecko) "
                 "Chrome/123.0.0.0 Safari/537.36"
                 ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Referer": "https://www.google.com/",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
            }

            logger.info("Sending HTTP request...")
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            logger.info(f"Request successful. Status code: {resp.status_code}")
            
            soup = BeautifulSoup(resp.text, "html.parser")
            logger.info("HTML parsed successfully with BeautifulSoup")
            
            # Save HTML for debugging
            try:
                with open('last_scraped.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                logger.info("Saved HTML to last_scraped.html for debugging")
            except Exception as e:
                logger.warning(f"Could not save HTML file: {e}")

            # ---- 1. UBER BLOG HANDLER (JSON-LD CONTAINS FULL ARTICLE) ----
            logger.info("Checking for JSON-LD articleBody...")
            json_ld_tags = soup.find_all("script", type="application/ld+json")
            logger.info(f"Found {len(json_ld_tags)} JSON-LD script tags")
            
            for idx, json_ld_tag in enumerate(json_ld_tags):
                logger.info(f"Parsing JSON-LD tag {idx + 1}...")
                try:
                    data = json.loads(json_ld_tag.text)
                    # Handle both single objects and arrays
                    data_list = data if isinstance(data, list) else [data]
                    
                    for item in data_list:
                        if isinstance(item, dict) and "articleBody" in item:
                            content = item["articleBody"]
                            logger.info(f"✓ Extracted content from JSON-LD. Length: {len(content)} characters")
                            return content, None
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON-LD tag {idx + 1}: {e}")

            # ---- REMOVE NAVIGATION AND NOISE BEFORE EXTRACTION ----
            logger.info("Removing navigation elements...")
            nav_count = 0
            for element in soup.find_all(['nav', 'header', 'footer', 'aside']):
                element.decompose()
                nav_count += 1
            logger.info(f"Removed {nav_count} navigation/header/footer elements")
            
            # Remove specific classes/IDs that contain navigation
            for selector in ['.navigation', '.nav', '.menu', '.header', '.footer', 
                           '.sidebar', '.widget', '#header', '#footer', '#nav',
                           '[role="navigation"]', '[role="banner"]', '[role="complementary"]']:
                removed = soup.select(selector)
                if removed:
                    logger.info(f"Removing {len(removed)} elements matching: {selector}")
                for element in removed:
                    element.decompose()

            # ---- 2. GENERIC ARTICLE SELECTORS (IMPROVED ORDER) ----
            selectors = [
                "[itemprop='articleBody']",  # Most specific
                "article",
                ".article-content",
                ".post-content",
                ".entry-content",
                ".post-body",
                ".blog-post-content",
                ".content",
                "#content",
                "main article",
                "main",
                "div[class*='post']",
                "div[class*='article']",
                "div[class*='content']",
            ]

            logger.info("Trying generic article selectors...")
            for selector in selectors:
                logger.info(f"Trying selector: {selector}")
                tags = soup.select(selector)
                if tags:
                    logger.info(f"✓ Found {len(tags)} element(s) with selector: {selector}")
                    # Try each matching element
                    for idx, tag in enumerate(tags):
                        # Further clean within the article
                        for noise in tag.find_all(['script', 'style', 'iframe', 'noscript']):
                            noise.decompose()
                        
                        text = tag.get_text(separator="\n", strip=True)
                        logger.info(f"Element {idx + 1} text length: {len(text)} characters")
                        if len(text) > 300:
                            logger.info(f"✓ Content extracted successfully using selector: {selector}")
                            return text, None
                        else:
                            logger.warning(f"Element {idx + 1} content too short ({len(text)} chars)")
                else:
                    logger.info(f"✗ No element found for selector: {selector}")

            # ---- 3. AGGRESSIVE DIV SEARCH ----
            logger.info("Trying aggressive div search...")
            all_divs = soup.find_all('div')
            logger.info(f"Found {len(all_divs)} div elements total")
            
            # Find the div with the most paragraph content
            best_div = None
            best_length = 0
            
            for div in all_divs:
                paragraphs = div.find_all('p', recursive=False)
                if paragraphs:
                    text = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
                    if len(text) > best_length:
                        best_length = len(text)
                        best_div = div
            
            if best_div and best_length > 300:
                logger.info(f"✓ Found best div with {best_length} characters of content")
                for noise in best_div.find_all(['script', 'style', 'iframe', 'noscript']):
                    noise.decompose()
                text = best_div.get_text(separator="\n", strip=True)
                return text, None

            # ---- 4. PARAGRAPH FALLBACK (WITH BETTER FILTERING) ----
            logger.info("Falling back to paragraph extraction...")
            # Try to find the main content area first
            main_content = soup.find('main') or soup.find('article') or soup.find('body') or soup
            
            if main_content:
                content_type = main_content.name if hasattr(main_content, 'name') else 'soup'
                logger.info(f"Found main content area: {content_type}")
                paragraphs = main_content.find_all("p")
                logger.info(f"Found {len(paragraphs)} paragraphs")
                
                if paragraphs:
                    valid_paragraphs = [p.get_text(strip=True) for p in paragraphs 
                                       if len(p.get_text(strip=True)) > 30]
                    logger.info(f"Valid paragraphs (>30 chars): {len(valid_paragraphs)}")
                    
                    combined = "\n\n".join(valid_paragraphs)
                    logger.info(f"Combined paragraph length: {len(combined)} characters")
                    
                    if len(combined) > 200:
                        logger.info("✓ Content extracted from paragraphs")
                        return combined, None
                    else:
                        logger.warning(f"Combined paragraphs too short: {len(combined)} chars")
            else:
                logger.warning("Could not find any content area")

            # ---- 5. LAST RESORT: GET ALL TEXT ----
            logger.info("Last resort: extracting all visible text...")
            all_text = soup.get_text(separator="\n", strip=True)
            logger.info(f"All text length: {len(all_text)} characters")
            
            if len(all_text) > 500:
                logger.warning("Returning all text as last resort (may contain noise)")
                return all_text, None

            logger.error("Unable to extract blog content - all methods failed")
            logger.error("Check last_scraped.html to see the page structure")
            return None, "Unable to extract blog content. The page might be JavaScript-rendered or have an unusual structure. Check last_scraped.html for debugging."

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for URL: {url}")
            return None, f"Request timeout after 15 seconds"
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return None, f"HTTP error: {e}"
        except Exception as e:
            logger.error(f"Unexpected error while fetching blog: {e}", exc_info=True)
            return None, f"Error fetching blog: {e}"

    # ---------------------------------------------------------------
    # CLEANING PIPELINE (IMPROVED)
    # ---------------------------------------------------------------
    @staticmethod
    def remove_duplicate_lines(text: str):
        lines = text.splitlines()
        seen = set()
        out = []
        for ln in lines:
            normalized = ln.strip()
            if normalized and normalized not in seen:
                out.append(ln)
                seen.add(normalized)
        return "\n".join(out)

    @staticmethod
    def remove_noise(text: str):
        """Remove common noise patterns from scraped content"""
        noise_patterns = [
            r'Follow us on.*',
            r'Stay up to date.*',
            r'Sign up to.*',
            r'Posted by.*',
            r'Share\s+\w+',
            r'^Advertisement.*',
            r'Cookie Policy.*',
            r'Related Articles.*',
            r'Subscribe to.*',
            r'Read more.*',
            r'Comments?\s*\d*',
            r'Posted on.*',
            r'Published on.*',
            r'\d+\s+min read',
        ]
        for pattern in noise_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
        return text

    @staticmethod
    def remove_navigation_text(text: str):
        """Remove common navigation elements that might slip through"""
        nav_keywords = [
            'Explore', 'Products', 'Earn', 'Resources', 'Ride', 'Experiences',
            'Business', 'Higher Education', 'Transit', 'Company', 'Careers',
            'Engineering', 'Newsroom', 'Uber.com', 'Sign up', 'Log in',
            'More', 'No results', 'Search', 'Overview', 'Backend', 'Culture',
            'Data / ML', 'Mobile', 'Security', 'Uber AI', 'Web', 'Research',
            'Chevron down', 'Linkedin', 'Envelope', 'Link'
        ]
        
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Skip lines that are just navigation keywords
            if line.strip() in nav_keywords:
                continue
            # Skip very short lines that might be navigation
            if len(line.strip()) < 20 and any(kw.lower() in line.lower() for kw in nav_keywords):
                continue
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    @staticmethod
    def remove_footer(text: str):
        """Remove footer content"""
        FOOTERS = [
            "Sign up",
            "Stay up to date",
            "follow us",
            "Privacy",
            "Terms",
            "Cookie",
            "© 20",  # Copyright notices
        ]

        lower = text.lower()
        earliest_footer_idx = len(text)
        
        for word in FOOTERS:
            idx = lower.rfind(word.lower())
            # Only consider it a footer if it's in the last 30% of content
            if idx != -1 and idx > len(text) * 0.7:
                earliest_footer_idx = min(earliest_footer_idx, idx)
        
        if earliest_footer_idx < len(text):
            text = text[:earliest_footer_idx]
        
        return text

    @staticmethod
    def normalize(text: str):
        """Normalize whitespace and special characters"""
        text = text.replace("\xa0", " ")
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Multiple newlines to double
        text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces to single
        text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)  # Leading whitespace
        return text.strip()

    @staticmethod
    def clean_text(text: str):
        """Main cleaning pipeline"""
        if not text:
            return ""

        logger.info("Starting text cleaning pipeline...")
        original_length = len(text)
        
        # Apply cleaning steps in order
        text = ContentExtractor.remove_navigation_text(text)
        logger.info(f"After navigation removal: {len(text)} chars (removed {original_length - len(text)})")
        
        text = ContentExtractor.remove_duplicate_lines(text)
        logger.info(f"After duplicate removal: {len(text)} chars")
        
        text = ContentExtractor.remove_noise(text)
        logger.info(f"After noise removal: {len(text)} chars")
        
        text = ContentExtractor.remove_footer(text)
        logger.info(f"After footer removal: {len(text)} chars")
        
        text = ContentExtractor.normalize(text)
        logger.info(f"After normalization: {len(text)} chars")
        
        logger.info(f"Cleaning complete. Final length: {len(text)} characters")
        return text.strip()

    # ---------------------------------------------------------------
    # MAIN ENTRY
    # ---------------------------------------------------------------
    @staticmethod
    def extract_content(input_text, input_type):
        """
        Main extraction method.
        Args:
            input_text: URL or raw text
            input_type: 'blog', 'youtube', 'text'
        """
        logger.info(f"=" * 80)
        logger.info(f"EXTRACT CONTENT CALLED")
        logger.info(f"Type: {input_type}")
        logger.info(f"Input: {input_text[:100]}..." if len(input_text) > 100 else f"Input: {input_text}")
        logger.info(f"=" * 80)
        
        if input_type == "text":
            logger.info("Processing as raw text")
            return input_text.strip(), None

        elif input_type == "youtube":
            logger.info("Processing as YouTube URL")
            return ContentExtractor.get_youtube_transcript(input_text)

        elif input_type == "blog":
            logger.info("Processing as blog URL")
            raw, err = ContentExtractor.scrape_blog_post(input_text)

            if err:
                logger.error(f"Blog extraction failed: {err}")
                return None, err
            
            cleaned = ContentExtractor.clean_text(raw)
            logger.info("=" * 80)
            logger.info("EXTRACTION COMPLETE")
            logger.info(f"Final content length: {len(cleaned)} characters")
            logger.info("=" * 80)
            print("\n" + "=" * 80)
            print("PREVIEW OF EXTRACTED CONTENT:")
            print("=" * 80)
            print(cleaned)
            print("=" * 80 + "\n")
            
            return cleaned, None

        logger.error(f"Invalid input type: {input_type}")
        return None, "Invalid input type"