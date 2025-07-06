import tweepy
import os
from typing import Optional, List, Dict, Any, Union

class TwitterService:
    """
    Service wrapper for Twitter API interactions using Tweepy.
    Handles authentication and provides methods for actions like posting tweets.
    """
    _client_v2: Optional[tweepy.Client] = None # For Twitter API v2 (preferred)
    _api_v1: Optional[tweepy.API] = None # For Twitter API v1.1 (e.g., media uploads)

    def __init__(self):
        """
        Initializes the TwitterService.
        Attempts to load credentials from environment variables.
        """
        self.consumer_key = os.getenv("TWITTER_API_KEY")
        self.consumer_secret = os.getenv("TWITTER_API_KEY_SECRET")
        self.access_token = os.getenv("TWITTER_USER_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_USER_TOKEN_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN") # For v2 app-only or some specific endpoints

        if not all([self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret]):
            print("WARN: Twitter User Context (OAuth 1.0a) credentials not fully set. Posting tweets will fail.")
        else:
            try:
                # Client for v2 API (user context for posting)
                self._client_v2 = tweepy.Client(
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )
                # API for v1.1 (needed for media uploads if using OAuth 1.0a)
                auth_v1 = tweepy.OAuth1UserHandler(
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )
                self._api_v1 = tweepy.API(auth_v1)
                print("DEBUG: Tweepy client (v2) and API (v1.1) initialized with User Context.")
            except Exception as e:
                print(f"ERROR: Failed to initialize Tweepy client/API: {e}")

        if not self.bearer_token and not self._client_v2:
             print("WARN: Twitter Bearer Token not set. Some v2 read operations might fail if user context client isn't available.")
        elif not self._client_v2 and self.bearer_token: # Only bearer token is set
            try:
                self._client_v2 = tweepy.Client(bearer_token=self.bearer_token)
                print("DEBUG: Tweepy client (v2) initialized with App Context (Bearer Token).")
            except Exception as e:
                print(f"ERROR: Failed to initialize Tweepy client with Bearer Token: {e}")


    async def test_authentication(self) -> bool:
        """
        Tests if the current credentials (User Context) are valid by fetching authenticated user's info.
        """
        if not self._client_v2 or not self.access_token: # User context client is needed
            print("WARN: test_authentication: Tweepy client (User Context) not initialized or access token missing.")
            return False
        try:
            # Fetching own user details is a good way to test auth
            response = self._client_v2.get_me(user_fields=["id", "username"])
            if response.data:
                print(f"DEBUG: Twitter authentication successful for user @{response.data.username} (ID: {response.data.id})")
                return True
            print(f"WARN: Twitter authentication test failed. Response: {response.errors}")
            return False
        except Exception as e:
            print(f"ERROR: Twitter authentication test failed: {e}")
            return False

    async def post_tweet(self, text: str, media_ids: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Posts a tweet.
        Args:
            text: The text content of the tweet.
            media_ids: Optional list of media IDs to attach to the tweet.
        Returns:
            A dictionary containing the response from Twitter API or None on failure.
        """
        if not self._client_v2:
            print("ERROR: Twitter client (v2 User Context) not initialized. Cannot post tweet.")
            return None
        try:
            print(f"DEBUG: Posting tweet: '{text[:50]}...' with media_ids: {media_ids}")
            response = self._client_v2.create_tweet(text=text, media_ids=media_ids)
            # response.data contains {'id': '...', 'text': '...'}
            print(f"DEBUG: Tweet posted successfully. ID: {response.data['id']}")
            return response.data
        except Exception as e:
            print(f"ERROR: Failed to post tweet: {e}")
            return None

    async def upload_media(self, file_path_or_buffer: Union[str, bytes], media_type: str) -> Optional[str]:
        """
        Uploads media to Twitter (API v1.1 required for this with OAuth 1.0a).
        Args:
            file_path_or_buffer: Path to the media file or bytes buffer.
            media_type: 'image/jpeg', 'image/png', 'image/gif', 'video/mp4'.
        Returns:
            The media_id_string if successful, else None.
        """
        if not self._api_v1: # Needs v1.1 API object
            print("ERROR: Twitter API v1.1 (User Context) not initialized. Cannot upload media.")
            return None
        try:
            print(f"DEBUG: Uploading media of type {media_type}...")
            # Tweepy's media_upload takes filename. For buffers, need to save temporarily or use other means if available.
            # For simplicity, assuming file_path for now. If buffer, would need to write to temp file.
            if isinstance(file_path_or_buffer, str): # It's a file path
                 media = self._api_v1.media_upload(filename=file_path_or_buffer)
            # elif isinstance(file_path_or_buffer, bytes):
                 # For bytes, tweepy.API.media_upload expects a filename.
                 # One way is to save to a temp file:
                 # import tempfile
                 # with tempfile.NamedTemporaryFile(delete=False, suffix="." + media_type.split('/')[-1]) as tmp:
                 #    tmp.write(file_path_or_buffer)
                 #    tmp_path = tmp.name
                 # media = self._api_v1.media_upload(filename=tmp_path)
                 # os.remove(tmp_path)
                 # For now, this example focuses on file_path.
                 # print("ERROR: Media upload from buffer not fully implemented in this stub.")
                 # return None
            else:
                print("ERROR: Invalid media input for upload. Must be file path or bytes.")
                return None

            print(f"DEBUG: Media uploaded successfully. Media ID: {media.media_id_string}")
            return media.media_id_string
        except Exception as e:
            print(f"ERROR: Failed to upload media: {e}")
            return None

# Singleton instance
_twitter_service_instance: Optional[TwitterService] = None

def get_twitter_service() -> TwitterService:
    global _twitter_service_instance
    if _twitter_service_instance is None:
        _twitter_service_instance = TwitterService()
    return _twitter_service_instance

if __name__ == '__main__':
    # Basic test (requires Twitter dev env vars to be set)
    # load_dotenv() # If you have a .env at project root for testing

    async def main():
        twitter_service = get_twitter_service()

        # Test Authentication
        is_authed = await twitter_service.test_authentication()
        print(f"Twitter Authentication Test: {'SUCCESS' if is_authed else 'FAILED'}")

        if is_authed:
            # Test Post Tweet (BE CAREFUL - THIS WILL POST TO TWITTER if creds are live)
            # response_data = await twitter_service.post_tweet(text="Hello from Python LangGraph Agent! (Test)")
            # if response_data:
            #    print(f"Test tweet posted: ID {response_data['id']}")
            # else:
            #    print("Test tweet failed.")
            pass # Commented out actual posting for safety

    # asyncio.run(main()) # Requires async context if you run this file directly
    print("TwitterService stub created. Run its __main__ block manually in an async context for testing if needed.")
