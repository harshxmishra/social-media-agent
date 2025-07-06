import requests
import os
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

GITHUB_API_BASE_URL = "https://api.github.com"

class GitHubService:
    """
    Service wrapper for GitHub API interactions.
    Uses a Personal Access Token (PAT) for authentication.
    """
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        else:
            print("WARN: GITHUB_TOKEN not set. GitHub API calls will be unauthenticated (rate-limited, restricted access).")

        print(f"DEBUG: GitHubService initialized. Token set: {bool(self.token)}")

    def _parse_repo_url(self, repo_url: str) -> Optional[Tuple[str, str]]:
        """Helper to extract owner and repo name from various GitHub URL formats."""
        try:
            parsed = urlparse(repo_url)
            if parsed.hostname == "github.com":
                path_parts = [part for part in parsed.path.strip('/').split('/') if part]
                if len(path_parts) >= 2:
                    owner, repo = path_parts[0], path_parts[1]
                    # Remove .git suffix if present
                    if repo.endswith(".git"):
                        repo = repo[:-4]
                    return owner, repo
        except Exception as e:
            print(f"ERROR: Could not parse GitHub repo URL '{repo_url}': {e}")
        return None

    async def get_repo_info(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """Placeholder: Fetches basic information for a repository."""
        owner_repo = self._parse_repo_url(repo_url)
        if not owner_repo:
            return {"error": f"Invalid GitHub repository URL format: {repo_url}"}
        owner, repo = owner_repo

        api_url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}"
        print(f"INFO: GitHubService.get_repo_info for {owner}/{repo}. Making API call to {api_url} (stub: will not actually call yet).")
        # In a real implementation:
        # try:
        #     response = requests.get(api_url, headers=self.headers)
        #     response.raise_for_status() # Raise an exception for HTTP errors
        #     return response.json()
        # except requests.exceptions.RequestException as e:
        #     print(f"ERROR: GitHub API request failed for {api_url}: {e}")
        #     return {"error": str(e)}
        return {"name": repo, "owner": owner, "description": "Mock description from stub.", "url": repo_url, "stub": True}

    async def get_file_content(self, repo_url: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Placeholder: Fetches the content of a file from a repository."""
        owner_repo = self._parse_repo_url(repo_url)
        if not owner_repo:
            return {"error": f"Invalid GitHub repository URL format: {repo_url}"}
        owner, repo = owner_repo

        api_url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/contents/{file_path.lstrip('/')}"
        print(f"INFO: GitHubService.get_file_content for {owner}/{repo}/{file_path}. Making API call to {api_url} (stub: will not actually call yet).")
        # Actual implementation would fetch and decode base64 content.
        return {"name": os.path.basename(file_path), "path": file_path, "content_base64": "bW9jayBjb250ZW50...", "stub": True}

# Singleton instance
_github_service_instance: Optional[GitHubService] = None

def get_github_service() -> GitHubService:
    global _github_service_instance
    if _github_service_instance is None:
        _github_service_instance = GitHubService()
    return _github_service_instance

if __name__ == '__main__':
    # Basic test (requires GITHUB_TOKEN for authenticated calls if implemented)
    # from dotenv import load_dotenv
    # load_dotenv()
    import asyncio

    async def main():
        github_service = get_github_service()

        # Test get_repo_info
        # repo_info = await github_service.get_repo_info("https://github.com/langchain-ai/langgraph")
        # print(f"Repo Info: {repo_info}")

        # Test get_file_content
        # file_content = await github_service.get_file_content("https://github.com/langchain-ai/langgraph", "README.md")
        # print(f"File Content: {file_content}")
        print("GitHubService stub created. Methods are placeholders and do not make live API calls yet.")

    # asyncio.run(main())
    print("GitHubService stub created. Run its __main__ block manually in an async context for testing if needed.")
