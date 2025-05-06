import logging
import os.path
import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class CalendarService:
    def __init__(self, config):
        self.config = config
        
        self.credentials_path = config.get('google_credentials_path', 'credentials.json') 
        self.token_path = config.get('google_token_path', 'token.json') 
        self.credentials = self._load_credentials()
        if self.credentials:
            try:
                self.service = build('calendar', 'v3', credentials=self.credentials)
                logging.info("Google Calendar Service initialized successfully.")
            except Exception as e:
                logging.error(f"Failed to build Google Calendar service: {e}", exc_info=True)
                self.service = None
        else:
            self.service = None
            logging.warning("Calendar Service initialized without valid credentials.")

    def _load_credentials(self):
        
        creds = None
        
        
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                logging.error(f"Error loading credentials from {self.token_path}: {e}")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logging.info("Refreshing expired Google Calendar credentials.")
                    creds.refresh(Request())
                except Exception as e:
                    logging.error(f"Failed to refresh credentials: {e}", exc_info=True)
                    
                    creds = None 
                    
                    
                    
            else:
                
                if not os.path.exists(self.credentials_path):
                    logging.error(f"Credentials file not found at {self.credentials_path}. Cannot initiate OAuth flow.")
                    logging.error("Please download your OAuth 2.0 Client secrets file from Google Cloud Console and save it as 'credentials.json' (or configure path in config.yaml).")
                    return None
                try:
                    logging.info(f"Initiating Google OAuth flow using {self.credentials_path}.")
                    
                    
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                    
                    
                    creds = flow.run_local_server(port=0)
                    logging.info("OAuth flow completed successfully.")
                except FileNotFoundError:
                     logging.error(f"Credentials file not found at {self.credentials_path}. Cannot authenticate.")
                     return None
                except Exception as e:
                    logging.error(f"Error during OAuth flow: {e}", exc_info=True)
                    return None
            
            if creds:
                try:
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                    logging.info(f"Credentials saved to {self.token_path}")
                except Exception as e:
                    logging.error(f"Failed to save credentials to {self.token_path}: {e}")

        if not creds or not creds.valid:
             logging.error("Failed to obtain valid Google Calendar credentials.")
             return None

        return creds

    def schedule_event(self, summary, start_datetime, end_datetime=None, attendees=None, description=None):
        
        if not self.service or not self.credentials or not self.credentials.valid:
            logging.error("Cannot schedule event: Google Calendar service is not available or credentials are invalid.")
            return False, "Error: Calendar service not configured or authentication failed."

        
        
        
        
        
        if not end_datetime:
            
            try:
                start_dt_obj = datetime.datetime.fromisoformat(start_datetime)
                end_dt_obj = start_dt_obj + datetime.timedelta(hours=1)
                end_datetime = end_dt_obj.isoformat()
            except ValueError:
                logging.error(f"Invalid start_datetime format: {start_datetime}. Expected ISO 8601.")
                return False, f"Error: Invalid start date/time format '{start_datetime}'. Use ISO 8601 (e.g., YYYY-MM-DDTHH:MM:SS[-HH:MM])."

        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_datetime,
                
            },
            'end': {
                'dateTime': end_datetime,
                
            },
            'attendees': [{'email': email} for email in attendees] if attendees else [],
            
            
            
            
            
            
            
            
        }

        try:
            logging.info(f"Attempting to insert event: {summary} at {start_datetime}")
            created_event = self.service.events().insert(calendarId='primary', body=event).execute()
            event_link = created_event.get('htmlLink')
            logging.info(f"Event created successfully: {event_link}")
            return True, f"Event '{summary}' scheduled successfully. Link: {event_link}"
        except HttpError as error:
            logging.error(f"An API error occurred: {error}", exc_info=True)
            return False, f"Failed to schedule event due to API error: {error}"
        except Exception as e:
            logging.error(f"Failed to schedule event '{summary}': {e}", exc_info=True)
            return False, f"Failed to schedule event: {e}"


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    
    dummy_config = {
        'google_credentials_path': 'credentials.json',
        'google_token_path': 'token.json'
    }
    calendar_service = CalendarService(dummy_config)
    success, message = calendar_service.schedule_event(
        'Team Meeting',
        '2024-07-28T10:00:00-07:00',
        '2024-07-28T11:00:00-07:00',
        attendees=['attendee1@example.com']
    )
    print(f"Schedule Event Result: {success}, Message: {message}")