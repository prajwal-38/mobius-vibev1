
import logging
import os
import subprocess
import webbrowser
import requests
import urllib.parse 
import shlex 
import whois 
from src.integrations.calendar_service import CalendarService
from src.integrations.email_service import EmailService








class TaskExecutor:
    def __init__(self, api_keys_config, llm_interface=None):
        self.api_keys = api_keys_config
        self.llm = llm_interface 
        
        self.calendar_service = CalendarService(api_keys_config) 
        self.email_service = EmailService(api_keys_config) 
        
        logging.info("Task Executor initialized.")

    def execute_task(self, nlu_result):
        
        intent = nlu_result.get('intent', 'unknown')
        entities = nlu_result.get('entities', {})
        logging.info(f"Executing task for intent: {intent}, Entities: {entities}")

        try:
            
            if intent == 'schedule_meeting':
                
                person = entities.get('person', ['Someone'])[0]
                datetime_str = entities.get('datetime', 'an unspecified time') 
                summary = f"Meeting with {person}"
                
                success, message = self.calendar_service.schedule_event(summary, start_datetime=datetime_str) 
                result = message
                logging.info(f"Task '{intent}' processed by CalendarService. Success: {success}")
            elif intent == 'send_email':
                
                recipient = entities.get('email_address', entities.get('person', [None])[0])
                subject = entities.get('subject', 'Quick Question') 
                body = entities.get('body', '...') 
                if recipient:
                    success, message = self.email_service.send_email(recipient, subject, body)
                    result = message
                    logging.info(f"Task '{intent}' processed by EmailService. Success: {success}")
                else:
                    result = "Error: Could not determine recipient for email."
                    logging.warning(f"Task '{intent}' failed: No recipient found.")
            elif intent == 'send_message': 
                
                recipient = entities.get('person', ['Someone'])[0]
                message_body = entities.get('message_body', '...') 
                result = f"Action Required: Send message to {recipient}. Body: '{message_body}'. (Integration not implemented)"
                logging.info(f"Task '{intent}' triggered.")
            elif intent == 'open_application':
                
                app_name = entities.get('object_name', [None])[0] 
                logging.debug(f"Attempting to open application: {app_name}. Raw entity: {entities.get('object_name')}")
                if app_name:
                    try:
                        
                        
                        
                        
                         
                        os.startfile(app_name) 
                        result = f"Attempting to open {app_name}..."
                        logging.info(f"Task '{intent}': Attempted to open '{app_name}'.")
                    except FileNotFoundError:
                        logging.warning(f"Task '{intent}': FileNotFoundError for '{app_name}'. Trying with '.exe'.")
                        
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
                            
                            result = f"Error: Application or file '{app_name}' not found. Make sure it's in your system's PATH or provide the full path."
                            logging.error(f"Task '{intent}': FileNotFoundError for '{app_name}'.")
                    except OSError as e:
                        
                        result = f"Error: Could not open application '{app_name}' due to an OS error: {e}"
                        logging.error(f"Task '{intent}': Failed to open '{app_name}'. OSError: {e}")
                    except Exception as e:
                        
                        result = f"Error: An unexpected error occurred while trying to open '{app_name}'. {e}"
                        logging.error(f"Task '{intent}': Failed to open '{app_name}'. Unexpected error: {e}", exc_info=True)
                else:
                    result = "Error: No application name specified."
                    logging.warning(f"Task '{intent}' failed: No application name provided.")

            elif intent == 'get_current_datetime':
                
                import datetime
                now = datetime.datetime.now()
                
                
                formatted_dt = now.strftime("%A, %B %d, %Y at %I:%M %p") 
                result = f"The current date and time is {formatted_dt}."
                logging.info(f"Task '{intent}': Provided current date and time.")

            elif intent == 'search_web':
                
                query = entities.get('search_query') 
                logging.debug(f"Attempting web search for: {query}. Raw entity: {entities.get('search_query')}")
                if query:
                    try:
                        
                        encoded_query = urllib.parse.quote_plus(query)
                        api_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&pretty=0&no_html=1&skip_disambig=1"
                        headers = {'User-Agent': 'MobiusVibeAssistant/1.0'}
                        logging.info(f"Querying DuckDuckGo API: {api_url}")
                        response = requests.get(api_url, headers=headers, timeout=10) 
                        response.raise_for_status() 
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
                                if i > 3: 
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

            elif intent == 'run_whois':
                logging.debug(f"TaskExecutor - Received entities for 'run_whois': {entities}") 
                target = entities.get('target_address')
                logging.debug(f"Attempting whois lookup for: {target}. Raw entity: {entities.get('target_address')}")
                if target:
                    try:
                        logging.info(f"Performing WHOIS lookup for '{target}' using python-whois library.")
                        
                        w = whois.whois(target)
                        
                        if not w or w.get('status') == 'No match for domain': 
                            result = f"No WHOIS information found for '{target}'."
                            logging.warning(f"Task '{intent}': No WHOIS match for '{target}'. Result: {w}")
                        else:
                            
                            
                            formatted_result = "\n".join([f"{key}: {value}" for key, value in w.items()])
                            result = f"WHOIS lookup results for {target}:\n{formatted_result}"
                            logging.info(f"Task '{intent}': Successfully executed for '{target}'.")
                    except whois.parser.PywhoisError as e:
                        
                        result = f"Error during WHOIS lookup for '{target}': {e}"
                        logging.error(f"Task '{intent}': Failed for '{target}'. PywhoisError: {e}")
                    except Exception as e:
                        
                        result = f"Error: An unexpected error occurred during WHOIS lookup for '{target}'. {e}"
                        logging.error(f"Task '{intent}': Failed for '{target}'. Unexpected error: {e}", exc_info=True)
                else:
                    result = "Error: No target address (domain or IP) specified for WHOIS lookup."
                    logging.warning(f"Task '{intent}' failed: No target address provided.")

            elif intent == 'run_nmap':
                logging.debug(f"TaskExecutor - Received entities for 'run_nmap': {entities}") 
                target = entities.get('target_address')
                logging.debug(f"Attempting nmap scan for: {target}. Raw entity: {entities.get('target_address')}")
                if target:
                    try:
                        
                        
                        
                        command = ['nmap', target] 
                        logging.info(f"Executing command: {' '.join(command)} (This might take a while...)")
                        
                        completed_process = subprocess.run(command, capture_output=True, text=True, check=False, timeout=120) 
                        if completed_process.returncode == 0:
                            result = f"Nmap scan results for {target}:\n{completed_process.stdout}"
                            logging.info(f"Task '{intent}': Successfully executed for '{target}'. Output length: {len(completed_process.stdout)}")
                        else:
                            error_message = completed_process.stderr or f"'nmap' command failed with return code {completed_process.returncode}. Is 'nmap' installed and in PATH?"
                            result = f"Error running Nmap scan for {target}: {error_message}"
                            logging.error(f"Task '{intent}': Failed for '{target}'. Error: {error_message}")
                    except FileNotFoundError:
                        result = "Error: 'nmap' command not found. Please ensure it is installed and in your system's PATH."
                        logging.error(f"Task '{intent}': 'nmap' command not found.")
                    except subprocess.TimeoutExpired:
                        result = f"Error: Nmap command for '{target}' timed out after 120 seconds."
                        logging.error(f"Task '{intent}': Command timed out for '{target}'.")
                    except Exception as e:
                        result = f"Error: An unexpected error occurred during Nmap scan for '{target}'. {e}"
                        logging.error(f"Task '{intent}': Failed for '{target}'. Unexpected error: {e}", exc_info=True)
                else:
                    result = "Error: No target address (domain or IP) specified for Nmap scan."
                    logging.warning(f"Task '{intent}' failed: No target address provided.")

            elif intent == 'unknown':
                result = "Sorry, I didn't understand that request."
                logging.warning(f"Task execution failed: Intent 'unknown'. NLU Result: {nlu_result}")

            else:
                
                result = f"Action Required: Intent '{intent}' is recognized but not implemented in the task executor yet."
                logging.warning(f"Task execution skipped: Intent '{intent}' not implemented. Entities: {entities}")

        except Exception as e:
            
            logging.error(f"Critical error during task execution for intent '{intent}': {e}", exc_info=True)
            result = f"An unexpected critical error occurred while processing your request for '{intent}'."

        return result