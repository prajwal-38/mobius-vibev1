import logging
import os 
from utils.config_loader import load_config
from utils.logger_setup import setup_logging
from llm.llm_interface import LLMInterface
from nlu.nlu_processor import NLUProcessor
from memory.memory_manager import MemoryManager
from task_manager.task_executor import TaskExecutor
from ui.cli_interface import CommandLineInterface 

def main():
    
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config.yaml')
    try:
        config = load_config(config_path) 
        setup_logging(config['logging'])
        logging.info("Starting Mobius Vibe Assistant...")

        
        logging.info("Initializing components...")
        llm_interface = LLMInterface(config['llm'])
        nlu_processor = NLUProcessor(config['nlu'])
        memory_manager = MemoryManager(config['memory'])
        
        task_executor = TaskExecutor(config.get('api_keys', {}), llm_interface) 

        
        ui_type = config.get('ui', {}).get('interface_type', 'cli') 
        logging.info(f"Initializing UI: {ui_type}")
        if ui_type == 'cli':
            ui = CommandLineInterface(llm_interface, nlu_processor, memory_manager, task_executor)
        
        
        
        
        
        
        
        else:
            logging.error(f"Unsupported interface type: {ui_type}")
            raise ValueError(f"Unsupported interface type: {ui_type}")

        
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
    
    

if __name__ == "__main__":
    main()