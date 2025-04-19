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
            if intent == 'schedule_event':
                # Placeholder: Call Google Calendar API
                # result = self.google_calendar.schedule_event(entities)
                result = f"[Placeholder] Scheduling event with details: {entities}"
                logging.info(f"Task '{intent}' triggered.")
            elif intent == 'send_message':
                # Placeholder: Call Slack/Email API
                # result = self.slack.send_message(entities.get('channel'), entities.get('message'))
                result = f"[Placeholder] Sending message with details: {entities}"
                logging.info(f"Task '{intent}' triggered.")
            # Example for a potential future 'open_application' intent
            # elif intent == 'open_application':
            #     # Placeholder: Run local command (use with caution!)
            #     app_name = entities.get('app_name')
            #     if app_name:
            #         # Be very careful with subprocess on Windows
            #         # Example: os.startfile(f"C:\Path\To\{app_name}.exe")
            #         result = f"[Placeholder] Opening application: {app_name}"
            #         logging.info(f"Task 'open_application' for {app_name} triggered.")
            #     else:
            #         result = "Error: Application name not specified."
            #         logging.warning("Task 'open_application' failed: no app name.")
            # Add more intent handlers here
            elif intent == 'unknown_intent':
                 result = "I'm not sure how to handle that request yet."
                 logging.info("No specific task triggered for unknown intent.")
            else:
                # Handle other potential intents or errors from NLU
                result = f"Received intent '{intent}', but no specific action is defined."
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