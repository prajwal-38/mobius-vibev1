# src/utils/logger_setup.py
"""
Utility function to configure logging for the application.

Inputs:
- Logging configuration dictionary (from config.yaml)

Outputs:
- Configured root logger.
"""

import logging
import os

def setup_logging(log_config):
    """Configures logging based on the provided dictionary."""
    log_level = log_config.get('level', 'INFO').upper()
    log_file = log_config.get('log_file', 'assistant.log')

    # Ensure log directory exists if log_file has a path
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Clear existing handlers (optional, but good practice to avoid duplicates)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create and add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Create and add file handler (re-enable if needed, ensure path is correct)
    # try:
    #     file_handler = logging.FileHandler(log_file, encoding='utf-8')
    #     file_handler.setFormatter(formatter)
    #     root_logger.addHandler(file_handler)
    # except Exception as e:
    #     print(f"Error setting up file handler for {log_file}: {e}") # Print directly as logging might not be fully up
    #     logging.error(f"Failed to set up file handler: {e}", exc_info=True) # Also log if possible

    logging.info(f"Logging configured. Level: {log_level}, File: {log_file}")