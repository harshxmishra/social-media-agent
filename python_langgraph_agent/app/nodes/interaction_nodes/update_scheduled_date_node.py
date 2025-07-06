from typing import Dict, Any, Optional
import datetime
from dateutil import parser as dateutil_parser # For robust date parsing
from ...state import GeneratePostState, DateType # Corrected relative import

# Define the specific string literals for DateType if needed for validation, though DateType already includes them
DATE_LITERALS = ["p1", "p2", "p3", "r1", "r2", "r3"]

async def update_scheduled_date_node(state: GeneratePostState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates the post's scheduled date based on user input (natural language or specific keywords).
    """
    user_input_for_date = state.userResponse

    print(f"DEBUG: Node: update_scheduled_date_node. User input for date: '{user_input_for_date}'")

    new_schedule_date: Optional[DateType] = state.scheduleDate # Default to current if parsing fails or no input

    if user_input_for_date:
        user_input_lower = user_input_for_date.strip().lower()

        if user_input_lower in DATE_LITERALS:
            new_schedule_date = user_input_lower # It's one of "p1", "p2", etc.
            print(f"DEBUG: Parsed schedule date as literal: {new_schedule_date}")
        elif user_input_lower in ["clear", "none", "remove", "cancel"]:
            new_schedule_date = None
            print("DEBUG: Schedule date cleared by user input.")
        else:
            try:
                # Use dateutil.parser for flexible date string parsing
                # fuzzy=True can help with more natural language but can also be too lenient.
                # default can be used to fill in missing parts (e.g. if only time is given, use today's date)
                parsed_datetime = dateutil_parser.parse(user_input_for_date, fuzzy=False)
                new_schedule_date = parsed_datetime.date() # We only store the date part for now as per DateType
                print(f"DEBUG: Parsed schedule date using dateutil: {new_schedule_date}")
            except (ValueError, OverflowError) as e: # Catch parsing errors
                print(f"DEBUG: Could not parse '{user_input_for_date}' as a date using dateutil.parser: {e}. Keeping current date: {state.scheduleDate}")
                new_schedule_date = state.scheduleDate # Keep original if parsing fails

    else:
        print("DEBUG: No user input provided for date update. Keeping current date.")

    # Clear userResponse after processing, and return the updated scheduleDate
    return {"scheduleDate": new_schedule_date, "userResponse": None}
