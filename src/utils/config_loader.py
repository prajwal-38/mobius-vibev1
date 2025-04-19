# src/utils/config_loader.py
"""
Utility function to load and validate the configuration from a YAML file.

Inputs:
- Path to the YAML configuration file (e.g., 'config.yaml')

Outputs:
- A dictionary containing the loaded configuration.

Raises:
- FileNotFoundError if the config file doesn't exist.
- YAMLError if the file is not valid YAML.
- Custom validation errors (optional).
"""

import yaml
import os
import logging

def load_config(config_path='config.yaml'):
    """Loads configuration from a YAML file."""
    if not os.path.exists(config_path):
        logging.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logging.info(f"Configuration loaded successfully from {config_path}")
        # TODO: Add schema validation here if needed
        return config
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file {config_path}: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading config: {e}")
        raise