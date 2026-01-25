
import unittest
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from content_extractor import ContentExtractor

class TestSecurity(unittest.TestCase):
    def test_safe_urls(self):
        safe_urls = [
            "https://google.com",
            "http://example.com/foo",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        for url in safe_urls:
            print(f"Testing SAFE url: {url}")
            self.assertTrue(ContentExtractor.is_safe_url(url), f"Should be safe: {url}")

    def test_unsafe_urls(self):
        unsafe_urls = [
            "file:///etc/passwd",
            "ftp://example.com",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://0.0.0.0",
            "http://192.168.1.1",
            "http://10.0.0.1",
            "javascript:alert(1)"
        ]
        for url in unsafe_urls:
            print(f"Testing UNSAFE url: {url}")
            self.assertFalse(ContentExtractor.is_safe_url(url), f"Should be unsafe: {url}")

if __name__ == '__main__':
    unittest.main()
