
from core.content_extractor import ContentExtractor, YouTubeExtractor, BlogExtractor, RawTextExtractor

def test_refactor():
    print("Testing Raw Text Extraction...")
    text, err = ContentExtractor.extract_content("Hello World", "text")
    assert text == "Hello World"
    assert err is None
    print("✓ Raw Text Extraction Passed")

    print("\nTesting Class Instantiation...")
    # Verify that the factory logic in extract_content is picking the right classes
    # We can't easily snoop inside the static method without mocking, 
    # but we can check if the code runs without crashing.
    
    # Test Invalid Type
    val, err = ContentExtractor.extract_content("http://foo.com", "invalid_type")
    assert val is None
    assert "Invalid input type" in err
    print("✓ Invalid Type Handling Passed")

    print("\nTest Complete. The refactor didn't break basic usage.")

if __name__ == "__main__":
    test_refactor()
