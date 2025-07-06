from typing import Dict, Any, List
from ...state import GeneratePostState # Changed import
from ...clients.firecrawl_client import get_firecrawl_service # Import Firecrawl service

async def verify_general_content(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]: # Changed signature
    """
    Verifies general web content using Firecrawl to scrape the page.
    Processes state.links[0].
    """
    if not state.links:
        print("ERROR: verify_general_content called with no links in state.")
        return {"pageContents": [], "relevantLinks": [], "imageOptions": []}

    link_to_process = state.links[0]
    print(f"DEBUG: Verifying general content for link: {link_to_process} using Firecrawl.")

    page_contents_list: List[str] = []
    relevant_links_list: List[str] = [link_to_process] # Default to include the input link
    image_options_list: List[str] = [] # Keep mock for now or try to extract from metadata

    try:
        firecrawl_service = get_firecrawl_service()
        # Adjust params for what firecrawl-py expects for its scrape_url method.
        # The `scrape_url` method in firecrawl-py returns an object with attributes like .markdown, .content, .metadata
        # It takes `page_options` for things like `onlyMainContent`.
        scrape_result = firecrawl_service.scrape_url(
            url=link_to_process,
            # Parameters for firecrawl-py's scrape_url:
            # page_options={'onlyMainContent': True} # This is a common parameter structure
            # The FirecrawlService wrapper needs to correctly pass these.
            # For now, let's assume the wrapper's `params` argument can take this:
            params={'pageOptions': {'onlyMainContent': True}}
        )

        if scrape_result:
            # firecrawl-py returns an object that can be dict-like or attribute-access
            # Prefer markdown if available, else content.
            content_to_use = None
            if hasattr(scrape_result, 'markdown') and scrape_result.markdown:
                content_to_use = scrape_result.markdown
            elif hasattr(scrape_result, 'content') and scrape_result.content:
                content_to_use = scrape_result.content
            elif isinstance(scrape_result, dict) and scrape_result.get('markdown'): # if it's a dict
                 content_to_use = scrape_result.get('markdown')
            elif isinstance(scrape_result, dict) and scrape_result.get('content'):
                 content_to_use = scrape_result.get('content')


            if content_to_use:
                page_contents_list.append(content_to_use)
                print(f"DEBUG: Firecrawl successfully scraped content for {link_to_process} (first 100 chars): {content_to_use[:100]}...")
            else:
                page_contents_list.append(f"Firecrawl could not extract main content from {link_to_process}, but the URL was reachable.")
                print(f"WARN: Firecrawl did not return 'markdown' or 'content' for {link_to_process}")

            # Potentially extract image options from metadata if Firecrawl provides them
            metadata = None
            if hasattr(scrape_result, 'metadata'):
                metadata = scrape_result.metadata
            elif isinstance(scrape_result, dict) and scrape_result.get('metadata'):
                metadata = scrape_result.get('metadata')

            if metadata and metadata.get('ogImage'):
                image_options_list.append(metadata['ogImage'])
        else:
            page_contents_list.append(f"Failed to scrape content from {link_to_process} using Firecrawl.")
            print(f"ERROR: Firecrawl scrape_url returned None or empty for {link_to_process}")

    except Exception as e:
        print(f"ERROR: Exception during Firecrawl operation for {link_to_process}: {e}")
        page_contents_list.append(f"Error scraping {link_to_process}: {str(e)}")

    return {
        "pageContents": page_contents_list,
        "relevantLinks": relevant_links_list, # Could add more links if found during scrape
        "imageOptions": image_options_list if image_options_list else [f"https://example.com/mock_images/{link_to_process.replace('https://', '').replace('/', '_')}.jpg"] # Fallback mock
    }
