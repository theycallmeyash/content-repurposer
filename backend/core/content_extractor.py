import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import re
import json
from urllib.parse import urlparse, parse_qs
import logging
import socket
import ipaddress
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('content_extractor.log')  
    ]
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------

class SecurityUtils:
    @staticmethod
    def is_safe_url(url: str) -> bool:
        """
        Check if URL is safe to scrape (prevents SSRF).
        - Must be http or https
        - Must not be local/private IP
        """
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                logger.warning(f"Unsafe scheme: {parsed.scheme}")
                return False

            hostname = parsed.hostname
            if not hostname:
                return False

            try:
                ip_list = socket.getaddrinfo(hostname, None)
            except socket.gaierror:
                # Could not resolve, might be obscure internal name
                logger.warning(f"Could not resolve hostname: {hostname}")
                return False

            for item in ip_list:
                # item is (family, type, proto, canonname, sockaddr)
                ip_addr_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_addr_str)

                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                    logger.warning(f"Blocked private/local IP: {ip_addr_str} for host {hostname}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating URL safety: {e}")
            return False


class ContentCleaner:
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
        text = ContentCleaner.remove_navigation_text(text)
        logger.info(f"After navigation removal: {len(text)} chars (removed {original_length - len(text)})")
        
        text = ContentCleaner.remove_duplicate_lines(text)
        logger.info(f"After duplicate removal: {len(text)} chars")
        
        text = ContentCleaner.remove_noise(text)
        logger.info(f"After noise removal: {len(text)} chars")
        
        text = ContentCleaner.remove_footer(text)
        logger.info(f"After footer removal: {len(text)} chars")
        
        text = ContentCleaner.normalize(text)
        logger.info(f"After normalization: {len(text)} chars")
        
        logger.info(f"Cleaning complete. Final length: {len(text)} characters")
        return text.strip()


# ---------------------------------------------------------------
# STRATEGY PATTERN: EXTRACTORS
# ---------------------------------------------------------------

class BaseExtractor(ABC):
    """Abstract base class for all content extractors"""
    
    @abstractmethod
    def extract(self, source: str) -> tuple[str | None, str | None]:
        """
        Extract content from source.
        Returns: (content_text, error_message)
        """
        pass


class YouTubeExtractor(BaseExtractor):
    """Extractor for YouTube video transcripts"""
    
    def extract(self, url: str) -> tuple[str | None, str | None]:
        logger.info(f"Starting YouTube transcript extraction for: {url}")
        
        # Security check
        if not SecurityUtils.is_safe_url(url):
             return None, "Invalid or unsafe URL (security restricted)"

        try:
            video_id = self._extract_youtube_id(url)
            if not video_id:
                logger.error("Invalid YouTube URL - no video ID found")
                return None, "Invalid YouTube URL"

            logger.info(f"Fetching transcript for video ID: {video_id}")
            
            # Support both v1.x (instance) and v0.x (static) APIs
            if hasattr(YouTubeTranscriptApi, 'get_transcript'):
                # v0.x API
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            else:
                # v1.x API
                try:
                    yt = YouTubeTranscriptApi()
                    transcript_data = yt.fetch(video_id)
                except Exception as e:
                     raise e

            logger.info(f"Successfully fetched transcript with {len(transcript_data)} segments")

            # Combine transcript text
            parts = []
            for item in transcript_data:
                if isinstance(item, dict):
                    parts.append(item.get("text", ""))
                elif hasattr(item, "text"):
                     parts.append(item.text)
                else:
                    parts.append(str(item))

            full_transcript = " ".join(parts)
            full_transcript = re.sub(r"\s+", " ", full_transcript)

            logger.info(f"Transcript extracted successfully. Length: {len(full_transcript)} characters")
            return full_transcript.strip(), None

        except Exception as e:
            logger.error(f"Error extracting YouTube transcript: {str(e)}", exc_info=True)
            return None, f"Error extracting YouTube transcript: {str(e)}"

    def _extract_youtube_id(self, url):
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


class BlogExtractor(BaseExtractor):
    """Extractor for Blog Posts / Web Articles"""

    def extract(self, url: str) -> tuple[str | None, str | None]:
        logger.info(f"Starting blog scraping for URL: {url}")
        
        # SSRF Check
        if not SecurityUtils.is_safe_url(url):
            logger.error(f"Security blocked URL: {url}")
            return None, "I cannot scrape this URL. It might be local, private, or unsafe."

        try:
            headers = {
                "User-Agent": (
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                 "AppleWebKit/537.36 (KHTML, like Gecko) "
                 "Chrome/123.0.0.0 Safari/537.36"
                 ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                # ... other headers
            }

            logger.info("Sending HTTP request...")
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            logger.info(f"Request successful. Status code: {resp.status_code}")
            
            soup = BeautifulSoup(resp.text, "html.parser")
            logger.info("HTML parsed successfully with BeautifulSoup")
            
            # Extraction Pipeline
            content = self._try_json_ld(soup)
            if content: return self._finalize(content)

            self._remove_noise_elements(soup)
            
            content = self._try_generic_selectors(soup)
            if content: return self._finalize(content)

            content = self._try_aggressive_div_search(soup)
            if content: return self._finalize(content)

            content = self._try_paragraph_fallback(soup)
            if content: return self._finalize(content)
            
            # Last Resort
            return self._finalize(soup.get_text(separator="\n", strip=True), is_last_resort=True)

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for URL: {url}")
            return None, f"Request timeout after 15 seconds"
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return None, f"HTTP error: {e}"
        except Exception as e:
            logger.error(f"Unexpected error while fetching blog: {e}", exc_info=True)
            return None, f"Error fetching blog: {e}"

    def _finalize(self, text, is_last_resort=False):
        """Run the cleaner on the extracted raw text."""
        if not text or len(text) < 100:
             if is_last_resort:
                 return text, None # Return whatever we have
             return None # Keep trying
        
        cleaned = ContentCleaner.clean_text(text)
        return cleaned, None

    def _remove_noise_elements(self, soup):
        """Remove navigation, header, footer, etc from soup in place."""
        for element in soup.find_all(['nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        for selector in ['.navigation', '.nav', '.menu', '.header', '.footer', 
                        '.sidebar', '.widget', '#header', '#footer', '#nav',
                        '[role="navigation"]', '[role="banner"]', '[role="complementary"]']:
            for element in soup.select(selector):
                element.decompose()

    def _try_json_ld(self, soup):
        json_ld_tags = soup.find_all("script", type="application/ld+json")
        for tag in json_ld_tags:
            try:
                data = json.loads(tag.text)
                data_list = data if isinstance(data, list) else [data]
                for item in data_list:
                    if isinstance(item, dict) and "articleBody" in item:
                        return item["articleBody"]
            except:
                continue
        return None

    def _try_generic_selectors(self, soup):
        selectors = [
            "[itemprop='articleBody']", "article", ".article-content", ".post-content",
            ".entry-content", ".post-body", ".blog-post-content", ".content",
            "#content", "main article", "main", "div[class*='post']",
            "div[class*='article']"
        ]
        for selector in selectors:
            tags = soup.select(selector)
            if tags:
                for tag in tags:
                    for noise in tag.find_all(['script', 'style', 'iframe', 'noscript']):
                        noise.decompose()
                    text = tag.get_text(separator="\n", strip=True)
                    if len(text) > 300:
                        return text
        return None

    def _try_aggressive_div_search(self, soup):
        all_divs = soup.find_all('div')
        best_div, best_length = None, 0
        for div in all_divs:
            paragraphs = div.find_all('p', recursive=False)
            if paragraphs:
                text = "\n\n".join([p.get_text(strip=True) for p in paragraphs])
                if len(text) > best_length:
                    best_length = len(text)
                    best_div = div
        
        if best_div and best_length > 300:
            for noise in best_div.find_all(['script', 'style', 'iframe', 'noscript']):
                noise.decompose()
            return best_div.get_text(separator="\n", strip=True)
        return None

    def _try_paragraph_fallback(self, soup):
        main_content = soup.find('main') or soup.find('article') or soup.find('body') or soup
        if main_content:
            paragraphs = main_content.find_all("p")
            if paragraphs:
                valid = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]
                combined = "\n\n".join(valid)
                if len(combined) > 200:
                    return combined
        return None


class RawTextExtractor(BaseExtractor):
    """Passthrough for raw text input"""
    def extract(self, source: str) -> tuple[str | None, str | None]:
        logger.info("Processing as raw text")
        return source.strip(), None


# ---------------------------------------------------------------
# FACADE CLASS (Backward Compatibility Maintained)
# ---------------------------------------------------------------

class ContentExtractor:
    """
    Facade for the extraction subsystem.
    Routes requests to the appropriate extractor.
    """
    
    @staticmethod
    def extract_content(input_text, input_type):
        """
        Main extraction method.
        Args:
            input_text: URL or raw text
            input_type: 'blog', 'youtube', 'text'
        """
        logger.info(f"=" * 80)
        logger.info(f"EXTRACT CONTENT CALLED (Strategy Pattern)")
        logger.info(f"Type: {input_type}")
        logger.info(f"=" * 80)

        extractor: BaseExtractor

        if input_type == "youtube":
            extractor = YouTubeExtractor()
        elif input_type == "blog":
            extractor = BlogExtractor()
        elif input_type == "text":
            extractor = RawTextExtractor()
        else:
            logger.error(f"Invalid input type: {input_type}")
            return None, "Invalid input type"

        return extractor.extract(input_text)