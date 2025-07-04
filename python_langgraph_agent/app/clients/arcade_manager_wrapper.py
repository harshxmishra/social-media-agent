from langchain_arcade import ArcadeToolManager
import os
from typing import Optional # Added Optional

# Ensure this file is recognized as part of the 'clients' package if not already handled
# by an __init__.py in the clients directory.

class ArcadeManagerSingleton:
    """
    Singleton wrapper for ArcadeToolManager to ensure it's initialized once.
    """
    _tool_manager_instance: Optional[ArcadeToolManager] = None # Type hint for the instance

    @classmethod
    def get_instance(cls) -> ArcadeToolManager: # Return type is ArcadeToolManager
        """
        Gets the singleton instance of ArcadeToolManager.
        Initializes it if it hasn't been already.

        Raises:
            ValueError: If ARCADE_API_KEY environment variable is not set.
        """
        if cls._tool_manager_instance is None:
            api_key = os.getenv("ARCADE_API_KEY")
            if not api_key:
                # In a real app, this might be handled more gracefully or logged.
                # For now, strict check.
                raise ValueError("ARCADE_API_KEY environment variable not set.")
            cls._tool_manager_instance = ArcadeToolManager(api_key=api_key)
            print("DEBUG: ArcadeToolManager initialized.")
        return cls._tool_manager_instance

def get_arcade_tool_manager() -> ArcadeToolManager:
    """
    Convenience function to access the ArcadeToolManager singleton instance.
    """
    return ArcadeManagerSingleton.get_instance()

if __name__ == '__main__':
    # Example usage (requires ARCADE_API_KEY to be set in .env or environment)
    # Load .env variables if you're running this directly and have a .env file
    from dotenv import load_dotenv
    import pathlib

    # Assuming this script is in python_langgraph_agent/app/clients/
    # and .env might be in python_langgraph_agent/ or project root
    env_path_project_root = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
    env_path_agent_root = pathlib.Path(__file__).resolve().parent.parent / '.env'

    if env_path_project_root.exists():
        load_dotenv(dotenv_path=env_path_project_root)
        print(f"Loaded .env from {env_path_project_root}")
    elif env_path_agent_root.exists():
        load_dotenv(dotenv_path=env_path_agent_root)
        print(f"Loaded .env from {env_path_agent_root}")
    else:
        print("DEBUG: No .env file found at expected locations for direct script run.")


    try:
        print("Attempting to get ArcadeToolManager instance...")
        manager1 = get_arcade_tool_manager()
        print(f"Manager 1 instance: {manager1}")

        # Get it again, should be the same instance
        manager2 = get_arcade_tool_manager()
        print(f"Manager 2 instance: {manager2}")

        assert manager1 is manager2, "ArcadeToolManager instances are not the same!"
        print("Successfully retrieved ArcadeToolManager singleton instance(s).")

        # Example: List available toolkits (if API key is valid)
        # This is just to demonstrate manager usage, might fail if key is dummy
        try:
            print("\nAttempting to list toolkits (requires valid API key)...")
            toolkits = manager1.list_toolkits() # Or another simple method
            print("Available toolkits:", toolkits)
        except Exception as e:
            print(f"Could not list toolkits (this is okay if key is dummy/invalid): {e}")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
