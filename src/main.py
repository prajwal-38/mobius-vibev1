# src/main.py
"""
Main entry point for the Mobius Vibe Personal Assistant.

Initializes all components (LLM, NLU, Memory, Task Manager, UI)
and starts the main application loop.

Inputs:
- Configuration from config.yaml
- Environment variables from .env (for API keys)
- User input via the chosen UI (CLI, Gradio, etc.)

Outputs:
- Assistant responses to the UI
- Logs to assistant.log
- Actions performed via integrations (e.g., calendar events, messages)
"""

import logging
# Assuming utils are in the same parent directory or PYTHONPATH is set
from utils.config_loader import load_config
from utils.logger_setup import setup_logging
from llm.llm_interface import LLMInterface
from nlu.nlu_processor import NLUProcessor
from memory.memory_manager import MemoryManager
from task_manager.task_executor import TaskExecutor
from ui.cli_interface import CommandLineInterface # Or other UI

def main():
    # 1. Load Configuration
    # Use absolute path or ensure config.yaml is in the correct relative path when running
    # For simplicity, assuming it's in the parent directory of src
    try:
        config = load_config('config.yaml') 
        setup_logging(config['logging'])
        logging.info("Starting Mobius Vibe Assistant...")

        # 2. Initialize Components
        logging.info("Initializing components...")
        llm_interface = LLMInterface(config['llm'])
        nlu_processor = NLUProcessor(config['nlu'])
        memory_manager = MemoryManager(config['memory'])
        # Pass only the relevant api_keys part of the config
        task_executor = TaskExecutor(config.get('api_keys', {}), llm_interface) # Pass LLM if needed for tasks

        # 3. Initialize UI
        ui_type = config.get('ui', {}).get('interface_type', 'cli') # Safer access
        logging.info(f"Initializing UI: {ui_type}")
        if ui_type == 'cli':
            ui = CommandLineInterface(llm_interface, nlu_processor, memory_manager, task_executor)
        # elif ui_type == 'gradio':
        #     # Initialize Gradio UI (implementation needed)
        #     logging.warning("Gradio UI not yet implemented.")
        #     pass # Replace with Gradio initialization
        # elif ui_type == 'web':
        #      logging.warning("Web UI not yet implemented.")
        #      pass # Replace with Web UI initialization
        else:
            logging.error(f"Unsupported interface type: {ui_type}")
            raise ValueError(f"Unsupported interface type: {ui_type}")

        # 4. Start Interaction Loop
        logging.info("Starting interaction loop.")
        ui.run()

    except FileNotFoundError as e:
        print(f"Error: Configuration file not found. {e}")
        logging.error(f"Configuration file error: {e}", exc_info=True)
    except KeyError as e:
        print(f"Error: Missing configuration key. Please check config.yaml. Missing key: {e}")
        logging.error(f"Configuration key error: {e}", exc_info=True)
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}")
        logging.error(f"Initialization error: {e}", exc_info=True)
    finally:
        logging.info("Mobius Vibe Assistant finished.")
    # print("Mobius Vibe Assistant - Placeholder Entry Point") # Placeholder removed

if __name__ == "__main__":
    main()