import os
from typing import Optional, Dict, Any

# Assuming LangGraph's RunnableConfig is a dict-like object or we extract relevant parts.
# For now, we'll work with the structure seen in the TypeScript.
# from langgraph.runnables import RunnableConfig # This might be the actual import
from urllib.parse import urlparse
from typing import Literal # For UrlType

# Define constants for keys used in config, mirroring TypeScript
POST_TO_LINKEDIN_ORGANIZATION_KEY = "postToLinkedInOrganization" # from generate-post-state.ts
# TEXT_ONLY_MODE_KEY = "textOnlyMode" # from generate-post-state.ts - not used here yet

UrlType = Literal["github", "youtube", "general", "twitter", "reddit", "luma", None]


def get_config_value(
    config: Optional[Dict[str, Any]],
    key: str,
    env_var_name: str,
    default: bool = False
) -> bool:
    """
    Helper to get a boolean value from config, falling back to an environment variable,
    then to a default.
    """
    if config and config.get("configurable"):
        configurable_dict = config.get("configurable", {})
        if key in configurable_dict and configurable_dict[key] is not None:
            return bool(configurable_dict[key])

    env_value = os.getenv(env_var_name)
    if env_value is not None:
        return env_value.lower() == "true"

    return default

def should_post_to_linkedin_org(config: Optional[Dict[str, Any]]) -> bool:
    """
    Checks if posts should be made to a LinkedIn organization.
    Mirrors the logic in src/agents/utils.ts
    """
    return get_config_value(
        config,
        POST_TO_LINKEDIN_ORGANIZATION_KEY,
        "POST_TO_LINKEDIN_ORGANIZATION",
        default=False
    )

def use_arcade_auth() -> bool:
    """
    Checks if Arcade authentication should be used.
    Mirrors the logic in src/agents/utils.ts
    """
    return os.getenv("USE_ARCADE_AUTH", "false").lower() == "true"

# Constant for textOnlyMode key, mirroring state.py or a future constants.py
TEXT_ONLY_MODE_KEY = "textOnlyMode"

def is_text_only(config: Optional[Dict[str, Any]]) -> bool:
    """
    Checks if the graph should run in text-only mode.
    Mirrors the logic in src/agents/utils.ts isTextOnly.
    """
    return get_config_value(
        config,
        TEXT_ONLY_MODE_KEY,
        "TEXT_ONLY_MODE", # Environment variable name
        default=False # Default if not set anywhere
    )

def get_url_type(url: str) -> UrlType:
    """
    Determines the type of a URL (e.g., github, youtube, twitter, reddit, luma, general).
    Mirrors the logic in src/agents/utils.ts getUrlType.
    """
    if not url or not isinstance(url, str):
        return None

    try:
        # Ensure the URL has a scheme, default to https if missing for parsing
        formatted_url = url
        if not url.startswith(('http://', 'https://', 'ftp://', 'file://')):
            # Check if it looks like a domain/path without scheme
            if '.' in url.split('/')[0]: # Simple check for a dot in the first path segment
                formatted_url = f"https://{url}"
            else: # Does not look like a typical URL host
                return None


        parsed_url = urlparse(formatted_url)
        hostname = parsed_url.hostname

        if not hostname:
            return None

        if "github.com" == hostname and not hostname.endswith("github.io"): # Explicitly github.com
            return "github"
        if "youtube.com" in hostname or "youtu.be" in hostname:
            return "youtube"
        if "twitter.com" in hostname or "x.com" in hostname:
            return "twitter"
        if "reddit.com" in hostname or "np.reddit.com" in hostname or "redd.it" in hostname:
            return "reddit"
        if "lu.ma" == hostname: # lu.ma is specific
            return "luma"

        # Default to general for other valid URLs
        return "general"

    except ValueError: # Handles errors from urlparse on severely malformed URLs
        return None


# Placeholder for other utility functions from utils.ts as they are needed.
# For example:
# def is_text_only(config: Optional[Dict[str, Any]]) -> bool:
#     return get_config_value(config, TEXT_ONLY_MODE_KEY, "TEXT_ONLY_MODE", default=False)

if __name__ == '__main__':
    # Example Usage (requires environment variables to be set for full testing)

    # Mock config
    mock_config_org_true = {"configurable": {POST_TO_LINKEDIN_ORGANIZATION_KEY: True}}
    mock_config_org_false = {"configurable": {POST_TO_LINKEDIN_ORGANIZATION_KEY: False}}
    mock_config_org_none = {"configurable": {POST_TO_LINKEDIN_ORGANIZATION_KEY: None}}
    mock_config_empty = {"configurable": {}}

    print(f"--- Testing should_post_to_linkedin_org ---")
    # Test with config
    print(f"Config True: {should_post_to_linkedin_org(mock_config_org_true)}") # True
    print(f"Config False: {should_post_to_linkedin_org(mock_config_org_false)}") # False

    # Test with env var (assuming POST_TO_LINKEDIN_ORGANIZATION is set or not)
    os.environ["POST_TO_LINKEDIN_ORGANIZATION"] = "true"
    print(f"Env True (config None): {should_post_to_linkedin_org(mock_config_org_none)}")
    print(f"Env True (config empty): {should_post_to_linkedin_org(mock_config_empty)}")

    os.environ["POST_TO_LINKEDIN_ORGANIZATION"] = "false"
    print(f"Env False (config None): {should_post_to_linkedin_org(mock_config_org_none)}")

    if "POST_TO_LINKEDIN_ORGANIZATION" in os.environ: del os.environ["POST_TO_LINKEDIN_ORGANIZATION"]
    print(f"No Env, Config None: {should_post_to_linkedin_org(mock_config_org_none)}")
    print(f"No Env, Config Empty: {should_post_to_linkedin_org(mock_config_empty)}")
    print(f"No Env, No Config: {should_post_to_linkedin_org(None)}")

    print(f"\n--- Testing use_arcade_auth ---")
    os.environ["USE_ARCADE_AUTH"] = "true"
    print(f"Env True: {use_arcade_auth()}")
    os.environ["USE_ARCADE_AUTH"] = "false"
    print(f"Env False: {use_arcade_auth()}")
    if "USE_ARCADE_AUTH" in os.environ: del os.environ["USE_ARCADE_AUTH"]
    print(f"No Env: {use_arcade_auth()}")


    print(f"\n--- Testing get_url_type ---")
    test_cases = {
        "https://github.com/langchain-ai/langgraph": "github",
        "https://www.youtube.com/watch?v=example": "youtube",
        "https://youtu.be/example": "youtube",
        "https://twitter.com/LangChainAI/status/123": "twitter",
        "https://x.com/LangChainAI/status/123": "twitter",
        "https://www.reddit.com/r/MachineLearning/comments/123": "reddit",
        "https://np.reddit.com/r/MachineLearning/comments/123": "reddit",
        "https://redd.it/123": "reddit",
        "https://lu.ma/event-id": "luma",
        "https://blog.langchain.dev/some-post": "general",
        "https://user.github.io/project/": "general", # github.io is general
        "not a url": None,
        "example.com/path": "general", # Handled by adding scheme
        "http://example.com/another": "general",
        "": None, # Empty string
        "ftp://example.com": "general" # Other schemes also general
    }
    for url, expected in test_cases.items():
        assert get_url_type(url) == expected, f"Expected {expected} for {url}, got {get_url_type(url)}"
        print(f"URL: {url}, Type: {get_url_type(url)}")
    print("get_url_type tests passed!")
