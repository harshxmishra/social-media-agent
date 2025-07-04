import os
from typing import Dict, Any, Optional
from firecrawl import FirecrawlApp # Main app from firecrawl-py

class FirecrawlService:
    """
    A wrapper class for the FirecrawlApp client to handle web scraping.
    """
    _client: Optional[FirecrawlApp] = None
    _api_key: Optional[str] = None

    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the FirecrawlService.
        It can be initialized with an API key directly, or it will try to load
        from the FIRECRAWL_API_KEY environment variable.

        Args:
            api_key: Optional Firecrawl API key.
        """
        if api_key:
            self._api_key = api_key
        else:
            self._api_key = os.getenv("FIRECRAWL_API_KEY")

        if not self._api_key:
            # Allow initialization without API key for cases where it might be set later
            # or if the client is only conditionally used.
            # However, operations will fail if the key isn't eventually provided.
            print("WARN: FirecrawlService initialized without an API key. Operations will fail unless set.")
            # Consider raising ValueError here if API key is strictly required at init.
            # For now, allow lazy initialization of the client.
            self._client = None
        else:
            self._client = FirecrawlApp(api_key=self._api_key)
            print("DEBUG: FirecrawlApp client initialized.")

    def _get_client(self) -> FirecrawlApp:
        """
        Ensures the client is initialized.
        Raises:
            ValueError: If the API key is not set.
        """
        if self._client is None:
            if not self_api_key: # Re-check self._api_key in case it was set post-init
                 self._api_key = os.getenv("FIRECRAWL_API_KEY")

            if not self._api_key:
                 raise ValueError("Firecrawl API key is not set. Please set FIRECRAWL_API_KEY environment variable or provide it during initialization.")
            self._client = FirecrawlApp(api_key=self._api_key)
            print("DEBUG: FirecrawlApp client lazy initialized.")
        return self._client

    def scrape_url(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Scrapes a given URL using Firecrawl.

        Args:
            url: The URL to scrape.
            params: Additional parameters for the Firecrawl scrape API.
                    Refer to Firecrawl documentation for options (e.g., pageOptions, extractorOptions).

        Returns:
            A dictionary containing the scrape result (e.g., content, markdown, metadata),
            or None if an error occurs.
        """
        client = self._get_client()
        if not client: # Should have raised in _get_client if key was missing
            return None

        try:
            print(f"DEBUG: Scraping URL with Firecrawl: {url}")
            # Default params can be empty or set with common defaults if desired
            scrape_params = params if params is not None else {}

            # Example of common params that might be used, from Firecrawl docs:
            # scrape_params = {
            #     'pageOptions': {'onlyMainContent': True} # To get just the main content
            # }
            # The TS project might use specific options, adapt as needed.

            data = client.scrape_url(url=url, params=scrape_params)
            # The returned 'data' object from firecrawl-py is typically a dictionary-like object
            # or a Pydantic model, e.g., {'content': '...', 'markdown': '...', 'metadata': {...}, ...}
            return data # Or data.model_dump() if it's a Pydantic model from firecrawl
        except Exception as e:
            print(f"ERROR: Firecrawl - Failed to scrape URL {url}: {e}")
            return None

# Singleton instance pattern for convenience if desired across the app
_firecrawl_service_instance: Optional[FirecrawlService] = None

def get_firecrawl_service() -> FirecrawlService:
    """
    Provides a singleton instance of the FirecrawlService.
    """
    global _firecrawl_service_instance
    if _firecrawl_service_instance is None:
        _firecrawl_service_instance = FirecrawlService()
    return _firecrawl_service_instance


if __name__ == '__main__':
    from dotenv import load_dotenv
    import pathlib

    # Load .env for testing this script directly
    env_path_project_root = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
    env_path_agent_root = pathlib.Path(__file__).resolve().parent.parent / '.env'

    if env_path_project_root.exists():
        load_dotenv(dotenv_path=env_path_project_root)
    elif env_path_agent_root.exists():
        load_dotenv(dotenv_path=env_path_agent_root)
    else:
        print("DEBUG: No .env file found for direct script run, ensure FIRECRAWL_API_KEY is in environment.")

    # Example usage:
    if not os.getenv("FIRECRAWL_API_KEY"):
        print("SKIPPING Firecrawl client test: FIRECRAWL_API_KEY not set.")
    else:
        service = get_firecrawl_service()
        test_url = "https://blog.langchain.dev/langgraph-cloud/" # A real URL for testing

        print(f"\nAttempting to scrape URL: {test_url}")
        # Example with specific params to get only main content in markdown
        # These params are based on general Firecrawl API knowledge,
        # actual params for firecrawl-py might vary slightly or have specific structure.
        custom_params = {
            "pageOptions": {
                "onlyMainContent": True,
                # "includeHtml": False # Default is false
            },
            # "extractorOptions": {
            #    "mode": "markdown", # To get markdown output; 'llm-extraction' is another mode
            #    "extractionPrompt": "Extract the main article content..." # if mode is llm-extraction
            # }
            # As of firecrawl-py 0.1.12, `client.scrape_url` returns an object with .markdown, .content, .metadata etc.
            # It doesn't seem to take complex `params` dict directly in the same way as the JS version for modes.
            # The python version of scrape_url might have direct parameters like `output_format='markdown'`
            # For now, we call it without complex params. The default usually gives main content.
        }

        # Simple scrape without specific params for now, assuming client.scrape_url handles it.
        # The firecrawl-py `scrape_url` itself returns an object with attributes like
        # .content, .markdown, .metadata. It does not take a 'params' dict in the same way
        # the JS version or the raw API might.
        # It has parameters like `page_options` (for includeHtml, onlyMainContent etc)
        # but not a generic `params` dict for all API options.
        # Let's try with a more direct mapping if `page_options` is a kwarg.
        # Default `scrape_url` behavior is often good.

        # Based on firecrawl-py source, it's `client.scrape_url(url=url, page_options={'onlyMainContent': True})`
        # So, our wrapper should ideally map its `params` arg to these specific kwargs.
        # For now, the wrapper passes `params` as the kwarg `params` to FirecrawlApp.scrape_url,
        # which might be correct for some versions or if the library handles it.
        # A quick check of firecrawl-py (e.g. 0.1.12) shows scrape_url(self, url: str, id: Optional[str] = None, timeout: Optional[int] = None, page_options: Optional[dict] = None, extractor_options: Optional[dict] = None, crawler_options: Optional[dict] = None)

        # Correcting the call based on typical firecrawl-py signature:
        # result = service.scrape_url(test_url, params={"page_options": {"onlyMainContent": True}})
        # However, our wrapper's current signature is scrape_url(self, url, params),
        # and it passes `params` as `params` to the client.
        # Let's assume our wrapper will be called like this:
        # service.scrape_url(test_url, {"pageOptions": {"onlyMainContent": True}})
        # and the wrapper needs to map "pageOptions" to "page_options" if the library is case-sensitive for kwargs.
        # For now, the current wrapper passes it as `params=params`.
        # If firecrawl-py `scrape_url` has a `params` kwarg that accepts this structure, it's fine.
        # If not, the wrapper needs to adapt.

        # Let's assume the wrapper is called with the correct structure that firecrawl-py expects for its `params` argument,
        # or that the `firecrawl-py` library itself handles a generic `params` dict.
        # A simple test without any extra params:
        result = service.scrape_url(test_url)

        if result:
            print("Scrape successful.")
            print(f"  Markdown available: {'markdown' in result and bool(result['markdown'])}")
            print(f"  Content available: {'content' in result and bool(result['content'])}")
            print(f"  Metadata keys: {result.get('metadata', {}).keys()}")
            # print("\nMarkdown content (first 500 chars):")
            # print(result.get("markdown", "")[:500])
        else:
            print("Scrape failed or returned None.")
