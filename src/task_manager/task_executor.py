# src/task_manager/task_executor.py
"""
Task Executor for the Personal Assistant.

Takes the recognized intent and entities from the NLU processor
and executes the corresponding task (e.g., API calls, local scripts).

Inputs:
- NLU processing result (dictionary with intent and entities)
- API keys/configurations (from config.yaml or .env)
- LLM interface (optional, for complex task generation/reasoning)

Outputs:
- Result of the task execution (e.g., success message, error, data retrieved)
- Side effects like sending emails, scheduling meetings, etc.
"""

import logging
# import os
# import subprocess
# from integrations.google_calendar import GoogleCalendarAPI # Example integration
# from integrations.slack import SlackAPI # Example integration

class TaskExecutor:
    def __init__(self, api_keys_config, llm_interface=None):
        self.api_keys = api_keys_config
        self.llm = llm_interface # Optional LLM for complex tasks
        # Initialize API clients here if needed
        # self.google_calendar = GoogleCalendarAPI(api_keys_config.get('google_calendar'))
        # self.slack = SlackAPI(api_keys_config.get('slack_token'))
        logging.info("Task Executor initialized.")

    def execute_task(self, nlu_result):
        """Executes a task based on the NLU result."""
        intent = nlu_result.get('intent', 'unknown')
        entities = nlu_result.get('entities', {})
        logging.info(f"Executing task for intent: {intent}, Entities: {entities}")

        try:
            # Use the intents defined in nlu_processor.py
            if intent == 'schedule_meeting':
                # Placeholder: Call Google Calendar API
                # result = self.google_calendar.schedule_event(entities)
                person = entities.get('person', ['Someone'])[0] # Take first person if list
                datetime_str = entities.get('datetime', 'an unspecified time')
                result = f"[Placeholder] Scheduling meeting with {person} for {datetime_str}. Details: {entities}"
                logging.info(f"Task '{intent}' triggered.")
            elif intent == 'send_email':
                # Placeholder: Call Email API
                recipient = entities.get('email_address', entities.get('person', ['Someone'])[0])
                subject = entities.get('subject', 'Quick Question') # Need NLU to extract subject
                body = entities.get('body', '...') # Need NLU to extract body
                result = f"[Placeholder] Sending email to {recipient} with subject '{subject}'. Details: {entities}"
                logging.info(f"Task '{intent}' triggered.")
            elif intent == 'send_message': # Generic message
                # Placeholder: Call Slack/SMS/etc. API
                recipient = entities.get('person', ['Someone'])[0]
                message_body = entities.get('message_body', '...') # Need NLU to extract
                result = f"[Placeholder] Sending message to {recipient}. Details: {entities}"
                logging.info(f"Task '{intent}' triggered.")
            elif intent == 'open_application':
                # Placeholder: Run local command (use with caution!)
                app_name = entities.get('object_name', [None])[0] # Take first object name if list
                if app_name:
                    # Actual implementation would need os.startfile or subprocess
                    # Example: os.startfile(f"C:\Path\To\{app_name}.exe") or subprocess.run(['open', '-a', app_name]) on macOS
                    result = f"[Placeholder] Attempting to open application: {app_name}"
                    logging.info(f"Task 'open_application' for {app_name} triggered.")
                else:
                    result = "Error: Application name not specified."
                    logging.warning("Task 'open_application' failed: no app name.")
            elif intent == 'close_application':
                 # Placeholder: Find process and terminate (complex and platform-specific)
                app_name = entities.get('object_name', [None])[0]
                if app_name:
                    result = f"[Placeholder] Attempting to close application: {app_name}"
                    logging.info(f"Task 'close_application' for {app_name} triggered.")
                else:
                    result = "Error: Application name not specified for closing."
                    logging.warning("Task 'close_application' failed: no app name.")
            elif intent == 'search_web':
                # Placeholder: Open web browser with search query
                query = entities.get('search_query', '')
                if query:
                    # Actual implementation would use webbrowser.open(f"https://www.google.com/search?q={query}")
                    result = f"[Placeholder] Searching web for: '{query}'"
                    logging.info(f"Task 'search_web' triggered with query: {query}")
                else:
                    result = "Error: No search query provided."
                    logging.warning("Task 'search_web' failed: no query.")
            elif intent == 'set_reminder':
                # Placeholder: Integrate with reminder system/calendar
                datetime_str = entities.get('datetime', 'later')
                reminder_subject = entities.get('reminder_subject', 'something') # Need NLU extraction
                result = f"[Placeholder] Setting reminder about '{reminder_subject}' for {datetime_str}. Details: {entities}"
                logging.info(f"Task '{intent}' triggered.")
            elif intent == 'schedule_event': # Generic event if not meeting
                datetime_str = entities.get('datetime', 'an unspecified time')
                event_details = entities.get('event_details', 'something') # Need NLU extraction
                result = f"[Placeholder] Scheduling event '{event_details}' for {datetime_str}. Details: {entities}"
                logging.info(f"Task '{intent}' triggered.")
            elif intent == 'unknown_intent':
                 result = "I'm not sure how to handle that request yet."
                 logging.info("No specific task triggered for unknown intent.")
            elif intent == 'error': # Handle NLU errors
                error_msg = nlu_result.get('error', 'Unknown NLU error')
                result = f"Sorry, I encountered an error trying to understand that: {error_msg}"
                logging.warning(f"NLU processing error passed to Task Executor: {error_msg}")
            else:
                # Handle other potential intents or errors from NLU
                result = f"Received intent '{intent}', but no specific action is defined for it yet."
                logging.warning(f"Unhandled intent received: {intent}")
            
            return result
        except Exception as e:
            logging.error(f"Error executing task for intent '{intent}': {e}", exc_info=True)
            return f"Error: Failed to execute task '{intent}'."

# Example usage (for testing):
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dummy_api_keys = {
        'google_calendar': 'dummy_key',
        'slack_token': 'dummy_token'
    }
    
    try:
        executor = TaskExecutor(dummy_api_keys)
        
        # Test case 1: Schedule event (using intent from NLU)
        nlu_res_schedule = {'intent': 'schedule_event', 'entities': {'person': 'Alice', 'date': 'tomorrow', 'time': '10 AM'}}
        result1 = executor.execute_task(nlu_res_schedule)
        print(f"Task 1 Result: {result1}")

        # Test case 2: Send message (using intent from NLU)
        nlu_res_message = {'intent': 'send_message', 'entities': {'contact': 'Bob', 'medium': 'email'}}
        result2 = executor.execute_task(nlu_res_message)
        print(f"Task 2 Result: {result2}")

        # Test case 3: Unknown intent
        nlu_res_unknown = {'intent': 'unknown_intent', 'entities': {}}
        result3 = executor.execute_task(nlu_res_unknown)
        print(f"Task 3 Result: {result3}")

    except Exception as e:
        print(f"Could not run Task Executor example: {e}")