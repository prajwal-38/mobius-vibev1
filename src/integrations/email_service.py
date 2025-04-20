# src/integrations/email_service.py
"""
Handles sending emails via SMTP or API.
"""

import logging
import smtplib
from email.mime.text import MIMEText

class EmailService:
    def __init__(self, config):
        self.config = config
        # Example: Load SMTP settings from config
        # Load SMTP settings from config - User needs to configure these!
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587) # Default to 587 (TLS)
        self.smtp_user = config.get('smtp_user')
        self.smtp_password = config.get('smtp_password') # IMPORTANT: Use secure storage (e.g., env vars, secrets manager)
        self.sender_email = config.get('sender_email', self.smtp_user) # Use smtp_user as sender if not specified

        if not all([self.smtp_server, self.smtp_port, self.smtp_user, self.smtp_password, self.sender_email]):
            logging.warning("Email Service is not fully configured. Please provide smtp_server, smtp_port, smtp_user, smtp_password, and sender_email in config.")
            self.configured = False
        else:
            self.configured = True
            logging.info("Email Service initialized with SMTP configuration.")

    def send_email(self, recipient, subject, body):
        """Sends an email.

        Args:
            recipient (str): The email address of the recipient.
            subject (str): The subject of the email.
            body (str): The body content of the email.

        Returns:
            bool: True if successful, False otherwise.
            str: Status message.
        """
        if not self.configured:
            logging.error("Cannot send email: Email Service is not configured.")
            return False, "Error: Email service not configured. Please check SMTP settings."

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = recipient

        try:
            logging.info(f"Attempting to send email via {self.smtp_server}:{self.smtp_port} from {self.sender_email} to {recipient}")
            # Connect to SMTP server (TLS is common)
            # Use SMTP_SSL for port 465, or SMTP with starttls() for port 587
            if self.smtp_port == 465:
                 server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else: # Assume port 587 or other requires STARTTLS
                 server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                 server.starttls() # Secure the connection

            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.sender_email, [recipient], msg.as_string())
            server.quit()
            logging.info(f"Email sent successfully to {recipient}")
            return True, f"Email successfully sent to {recipient}."
        except smtplib.SMTPAuthenticationError:
             logging.error(f"SMTP Authentication failed for user {self.smtp_user}. Check credentials.", exc_info=True)
             return False, "Failed to send email: Authentication error. Check username/password."
        except smtplib.SMTPServerDisconnected:
             logging.error(f"SMTP server disconnected unexpectedly ({self.smtp_server}:{self.smtp_port}).", exc_info=True)
             return False, "Failed to send email: Server disconnected."
        except smtplib.SMTPConnectError:
             logging.error(f"Could not connect to SMTP server ({self.smtp_server}:{self.smtp_port}). Check server/port.", exc_info=True)
             return False, "Failed to send email: Connection error. Check server/port."
        except Exception as e:
            logging.error(f"Failed to send email to {recipient}: {e}", exc_info=True)
            return False, f"Failed to send email due to an unexpected error: {e}"

# Example usage (for testing):
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Dummy config for testing - Replace with your actual SMTP details
    # Ensure these are added to your config.yaml or loaded securely
    dummy_config = {
        'smtp_server': 'smtp.gmail.com', # Example: Gmail SMTP
        'smtp_port': 587, # Example: Gmail TLS port
        'smtp_user': 'your_email@gmail.com', # Your email
        'smtp_password': 'your_app_password', # Your Gmail App Password
        'sender_email': 'your_email@gmail.com'
    }
    email_service = EmailService(dummy_config)
    success, message = email_service.send_email('test@example.com', 'Test Subject', 'This is a test email body.')
    print(f"Send Email Result: {success}, Message: {message}")