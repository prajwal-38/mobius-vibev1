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
import os
import subprocess
import webbrowser
import requests
import urllib.parse # Ensure urllib is imported
from integrations.calendar_service import CalendarService
from integrations.email_service import EmailService
# import os
# import subprocess
# import webbrowser
# import os
# import subprocess
# from integrations.google_calendar import GoogleCalendarAPI # Example integration
# from integrations.slack import SlackAPI # Example integration

class TaskExecutor:
    def __init__(self, api_keys_config, llm_interface=None):
        self.api_keys = api_keys_config
        self.llm = llm_interface # Optional LLM for complex tasks
        # Initialize API clients here
        self.calendar_service = CalendarService(api_keys_config) # Initialize CalendarService
        self.email_service = EmailService(api_keys_config) # Initialize EmailService
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
                # Call Calendar Service
                person = entities.get('person', ['Someone'])[0]
                datetime_str = entities.get('datetime', 'an unspecified time') # NLU needs to provide structured datetime
                summary = f"Meeting with {person}"
                # TODO: Convert natural language datetime_str to ISO format for API
                success, message = self.calendar_service.schedule_event(summary, start_datetime=datetime_str) # Pass extracted info
                result = message
                logging.info(f"Task '{intent}' processed by CalendarService. Success: {success}")
            elif intent == 'send_email':
                # Call Email Service
                recipient = entities.get('email_address', entities.get('person', [None])[0])
                subject = entities.get('subject', 'Quick Question') # NLU needs better extraction
                body = entities.get('body', '...') # NLU needs better extraction
                if recipient:
                    success, message = self.email_service.send_email(recipient, subject, body)
                    result = message
                    logging.info(f"Task '{intent}' processed by EmailService. Success: {success}")
                else:
                    result = "Error: Could not determine recipient for email."
                    logging.warning(f"Task '{intent}' failed: No recipient found.")
            elif intent == 'send_message': # Generic message
                # Placeholder: Call Slack/SMS/etc. API
                recipient = entities.get('person', ['Someone'])[0]
                message_body = entities.get('message_body', '...') # Need NLU to extract
                result = f"Action Required: Send message to {recipient}. Body: '{message_body}'. (Integration not implemented)"
                logging.info(f"Task '{intent}' triggered.")
            elif intent == 'open_application':
                # Placeholder: Run local command (use with caution!)
                app_name = entities.get('object_name', [None])[0] # Take first object name if list
                logging.debug(f"Attempting to open application: {app_name}. Raw entity: {entities.get('object_name')}")
                if app_name:
                    try:
                        # Use os.startfile on Windows for opening files/apps associated with their default program
                        # For more control or cross-platform, subprocess might be needed, but requires careful handling.
                        # Ensure the app_name is correctly formatted (e.g., 'notepad.exe', 'C:\path\to\app.exe')
                        # Using subprocess might be more robust for specific commands:
                        # subprocess.Popen([app_name]) 
                        os.startfile(app_name) # Relies on file associations and PATH
                        result = f"Attempting to open {app_name}..."
                        logging.info(f"Task '{intent}': Attempted to open '{app_name}'.")
                    except FileNotFoundError:
                        logging.warning(f"Task '{intent}': FileNotFoundError for '{app_name}'. Trying with '.exe'.")
                        # On Windows, try appending .exe if the initial name fails
                        if os.name == 'nt' and not app_name.lower().endswith('.exe'):
                            try:
                                app_name_exe = app_name + '.exe'
                                os.startfile(app_name_exe)
                                result = f"Attempting to open {app_name_exe}..."
                                logging.info(f"Task '{intent}': Attempted to open '{app_name_exe}' after adding .exe.")
                            except FileNotFoundError:
                                result = f"Error: Application or file '{app_name}' (or '{app_name_exe}') not found. Make sure it's in your system's PATH or provide the full path."
                                logging.error(f"Task '{intent}': FileNotFoundError for both '{app_name}' and '{app_name_exe}'.")
                            except Exception as e_inner:
                                result = f"Error: Could not open application '{app_name_exe}' even after adding .exe. Error: {e_inner}"
                                logging.error(f"Task '{intent}': Failed to open '{app_name_exe}'. Error: {e_inner}")
                        else:
                            # If not Windows or already ends with .exe, report original error
                            result = f"Error: Application or file '{app_name}' not found. Make sure it's in your system's PATH or provide the full path."
                            logging.error(f"Task '{intent}': FileNotFoundError for '{app_name}'.")
                    except OSError as e:
                        # Catch broader OS errors, e.g., permission issues or invalid operations
                        result = f"Error: Could not open application '{app_name}' due to an OS error: {e}"
                        logging.error(f"Task '{intent}': Failed to open '{app_name}'. OSError: {e}")
                    except Exception as e:
                        # Catch any other unexpected errors
                        result = f"Error: An unexpected error occurred while trying to open '{app_name}'. {e}"
                        logging.error(f"Task '{intent}': Failed to open '{app_name}'. Unexpected error: {e}", exc_info=True)
                else:
                    result = "Error: No application name specified."
                    logging.warning(f"Task '{intent}' failed: No application name provided.")

            elif intent == 'get_current_datetime':
                # Get current date and time
                import datetime
                now = datetime.datetime.now()
                # Format it nicely
                # Example format: Tuesday, March 28, 2023 at 10:35 AM
                formatted_dt = now.strftime("%A, %B %d, %Y at %I:%M %p") 
                result = f"The current date and time is {formatted_dt}."
                logging.info(f"Task '{intent}': Provided current date and time.")

            elif intent == 'search_web':
                # Correctly retrieve the search query string
                query = entities.get('search_query') 
                logging.debug(f"Attempting web search for: {query}. Raw entity: {entities.get('search_query')}")
                if query:
                    try:
                        # Use DuckDuckGo Instant Answer API
                        encoded_query = urllib.parse.quote_plus(query)
                        api_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&pretty=0&no_html=1&skip_disambig=1"
                        headers = {'User-Agent': 'MobiusVibeAssistant/1.0'}
                        logging.info(f"Querying DuckDuckGo API: {api_url}")
                        response = requests.get(api_url, headers=headers, timeout=10) # Added timeout
                        response.raise_for_status() # Raise an exception for bad status codes
                        data = response.json()
                        logging.debug(f"DuckDuckGo API Response: {data}")

                        summary = ""
                        if data.get('AbstractText'):
                            summary += f"Summary: {data['AbstractText']}\n"
                            if data.get('AbstractSource') and data.get('AbstractURL'):
                                summary += f"Source: {data['AbstractSource']} ({data['AbstractURL']})\n"
                        elif data.get('Definition'):
                             summary += f"Definition: {data['Definition']}\n"
                             if data.get('DefinitionSource') and data.get('DefinitionURL'):
                                summary += f"Source: {data['DefinitionSource']} ({data['DefinitionURL']})\n"
                        elif data.get('Answer'):
                            summary += f"Answer: {data['Answer']}\n"
                        elif data.get('RelatedTopics'):
                            summary += "Related Topics:\n"
                            for i, topic in enumerate(data['RelatedTopics']): 
                                if topic.get('Text'):
                                    summary += f"- {topic['Text']}\n"
                                if i > 3: # Limit related topics shown
                                    summary += "- ...and more.\n"
                                    break
                        
                        if not summary:
                            result = f"I couldn't find a direct answer or summary for '{query}'. You can try searching directly: https://duckduckgo.com/?q={encoded_query}"
                        else:
                            result = summary.strip()
                        
                        logging.info(f"Task '{intent}': Successfully retrieved search result for '{query}'.")

                    except requests.exceptions.RequestException as e:
                        result = f"Error: Could not connect to the search service. {e}"
                        logging.error(f"Task '{intent}': Failed API request for '{query}'. Error: {e}", exc_info=True)
                    except Exception as e:
                        result = f"Error: An unexpected error occurred during the web search for '{query}'. {e}"
                        logging.error(f"Task '{intent}': Failed processing search for '{query}'. Error: {e}", exc_info=True)
                else:
                    result = "Error: No search query specified."
                    logging.warning(f"Task '{intent}' failed: No search query provided.")

            elif intent == 'unknown':
                result = "Sorry, I didn't understand that request."
                logging.warning(f"Task execution failed: Intent 'unknown'. NLU Result: {nlu_result}")

            else:
                # Fallback for intents defined in NLU but not handled here yet
                result = f"Action Required: Intent '{intent}' is recognized but not implemented in the task executor yet."
                logging.warning(f"Task execution skipped: Intent '{intent}' not implemented. Entities: {entities}")

        except Exception as e:
            # General exception handler for the entire execute_task method
            logging.error(f"Critical error during task execution for intent '{intent}': {e}", exc_info=True)
            result = f"An unexpected critical error occurred while processing your request for '{intent}'."

        return result