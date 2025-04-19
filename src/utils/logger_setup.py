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

    # Basic configuration
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler() # Also log to console
        ]
    )

    logging.info(f"Logging configured. Level: {log_level}, File: {log_file}")