

import logging
import smtplib
from email.mime.text import MIMEText

class EmailService:
    def __init__(self, config):
        self.config = config
        
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587) 
        self.smtp_user = config.get('smtp_user')
        self.smtp_password = config.get('smtp_password') 
        self.sender_email = config.get('sender_email', self.smtp_user) 

        if not all([self.smtp_server, self.smtp_port, self.smtp_user, self.smtp_password, self.sender_email]):
            logging.warning("Email Service is not fully configured. Please provide smtp_server, smtp_port, smtp_user, smtp_password, and sender_email in config.")
            self.configured = False
        else:
            self.configured = True
            logging.info("Email Service initialized with SMTP configuration.")

    def send_email(self, recipient, subject, body):
        
        if not self.configured:
            logging.error("Cannot send email: Email Service is not configured.")
            return False, "Error: Email service not configured. Please check SMTP settings."

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = recipient

        try:
            logging.info(f"Attempting to send email via {self.smtp_server}:{self.smtp_port} from {self.sender_email} to {recipient}")
            
            
            if self.smtp_port == 465:
                 server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else: 
                 server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                 server.starttls() 

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


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    
    dummy_config = {
        'smtp_server': 'smtp.gmail.com', 
        'smtp_port': 587, 
        'smtp_user': 'your_email@gmail.com', 
        'smtp_password': 'your_app_password', 
        'sender_email': 'your_email@gmail.com'
    }
    email_service = EmailService(dummy_config)
    success, message = email_service.send_email('test@example.com', 'Test Subject', 'This is a test email body.')
    print(f"Send Email Result: {success}, Message: {message}")