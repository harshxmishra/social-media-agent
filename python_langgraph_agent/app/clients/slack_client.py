import os
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from typing import Optional, List, Dict, Any

class SlackService:
    """
    Service wrapper for Slack API interactions using slack_sdk.
    """
    _client: Optional[AsyncWebClient] = None

    def __init__(self):
        """
        Initializes the SlackService.
        Attempts to load SLACK_BOT_TOKEN from environment variables.
        """
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        if not self.bot_token:
            print("WARN: SLACK_BOT_TOKEN not set. Slack API calls will fail.")
        else:
            self._client = AsyncWebClient(token=self.bot_token)
            print(f"DEBUG: Slack AsyncWebClient initialized. Token set: {bool(self.bot_token)}")

    async def send_message(
        self,
        channel_id: str,
        text: Optional[str] = None,
        blocks: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Sends a message to a Slack channel.
        Args:
            channel_id: The ID of the channel to send the message to.
            text: The plain text message content (fallback or for notifications).
            blocks: Optional list of Slack Block Kit blocks for rich message formatting.
        Returns:
            The API response from Slack or None on failure.
        """
        if not self._client:
            print("ERROR: Slack client not initialized. Cannot send message.")
            return None
        if not text and not blocks:
            print("ERROR: Slack message needs either text or blocks.")
            return None

        try:
            print(f"DEBUG: Sending Slack message to channel {channel_id}. Text: '{text[:50] if text else 'No text'}...', Blocks: {'Yes' if blocks else 'No'}")
            response = await self._client.chat_postMessage(
                channel=channel_id,
                text=text, # Required, even if blocks are used, for notifications and accessibility
                blocks=blocks
            )
            print(f"DEBUG: Slack message sent successfully. Timestamp: {response.get('ts')}")
            return response.data # response is an AwaitableSlackResponse, .data gets the dict
        except SlackApiError as e:
            print(f"ERROR: Failed to send Slack message to {channel_id}: {e.response['error']}")
            return e.response.data
        except Exception as e:
            print(f"ERROR: An unexpected error occurred sending Slack message: {e}")
            return None

    async def get_channel_history(self, channel_id: str, limit: int = 10, oldest: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches message history from a Slack channel.
        Args:
            channel_id: The ID of the channel.
            limit: Maximum number of messages to return.
            oldest: Start of time range of messages to include in results (Unix timestamp).
        Returns:
            A list of message objects or None on failure.
        """
        if not self._client:
            print("ERROR: Slack client not initialized. Cannot get channel history.")
            return None
        try:
            print(f"DEBUG: Fetching Slack channel history for {channel_id}, limit {limit}.")
            response = await self._client.conversations_history(
                channel=channel_id,
                limit=limit,
                oldest=oldest
            )
            messages = response.get("messages")
            if messages is not None: # Check can be [] for empty history within range
                print(f"DEBUG: Fetched {len(messages)} messages from Slack channel {channel_id}.")
                return messages
            else:
                print(f"WARN: No messages found or error in response for channel {channel_id}. Error: {response.get('error')}")
                return [] # Return empty list if no messages key or error
        except SlackApiError as e:
            print(f"ERROR: Failed to get Slack channel history for {channel_id}: {e.response['error']}")
            return None
        except Exception as e:
            print(f"ERROR: An unexpected error occurred fetching Slack history: {e}")
            return None

# Singleton instance
_slack_service_instance: Optional[SlackService] = None

def get_slack_service() -> SlackService:
    global _slack_service_instance
    if _slack_service_instance is None:
        _slack_service_instance = SlackService()
    return _slack_service_instance

if __name__ == '__main__':
    # Basic test (requires SLACK_BOT_TOKEN and a test channel_id)
    # from dotenv import load_dotenv
    # load_dotenv()
    import asyncio

    async def main():
        slack_service = get_slack_service()
        test_channel_id = os.getenv("SLACK_TEST_CHANNEL_ID") # Set this in your .env for testing

        if not slack_service.bot_token:
            print("Skipping Slack tests as SLACK_BOT_TOKEN is not set.")
            return

        if not test_channel_id:
            print("Skipping Slack tests as SLACK_TEST_CHANNEL_ID is not set in env for testing.")
            return

        # Test send_message
        # print("\nTesting send_message...")
        # response_msg = await slack_service.send_message(channel_id=test_channel_id, text="Hello from Python LangGraph Agent! (Test Stub)")
        # if response_msg and response_msg.get("ok"):
        #     print(f"Message sent, ts: {response_msg.get('ts')}")
        # else:
        #     print(f"Failed to send message: {response_msg}")

        # Test get_channel_history
        # print("\nTesting get_channel_history...")
        # messages = await slack_service.get_channel_history(channel_id=test_channel_id, limit=5)
        # if messages is not None:
        #     print(f"Fetched {len(messages)} messages:")
        #     for msg in messages:
        #         print(f"  - {msg.get('ts')}: {msg.get('text', 'No text (possibly blocks only)')[:50]}...")
        # else:
        #     print("Failed to fetch channel history.")
        print("SlackService stub created. Methods are placeholders or basic calls. Run its __main__ block manually for testing.")

    # asyncio.run(main())
    print("SlackService stub created. Run its __main__ block manually in an async context for testing if needed.")
