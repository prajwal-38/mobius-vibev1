# src/llm/llm_interface.py
"""
Interface for interacting with the Large Language Model (LLM).

Handles loading the model (e.g., Mistral 7B GGUF), configuring it 
(GPU layers, context size, etc.), and performing inference.

Inputs:
- LLM configuration dictionary (from config.yaml)
- User prompts (strings)

Outputs:
- Generated text responses (strings)
"""

import logging
from llama_cpp import Llama # Assuming use of llama-cpp-python

class LLMInterface:
    def __init__(self, llm_config):
        self.config = llm_config
        self.model = None
        self._load_model()

    def _load_model(self):
        """Loads the GGUF model based on the configuration."""
        logging.info(f"Loading LLM from: {self.config['model_path']}")
        try:
            # Actual model loading logic using llama-cpp-python
            self.model = Llama(
                model_path=self.config['model_path'],
                n_gpu_layers=self.config['n_gpu_layers'],
                n_ctx=self.config['n_ctx'],
                # f16_kv=self.config.get('fp16', True), # Use fp16 key-value cache if enabled in config
                verbose=False # Set verbosity as needed
            )
            logging.info("LLM loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load LLM: {e}", exc_info=True)
            # Depending on the application design, you might want to exit
            # or handle this more gracefully.
            raise

    def generate(self, prompt):
        """Generates a response from the LLM based on the prompt."""
        if not self.model:
            logging.error("LLM not loaded. Cannot generate text.")
            return "Error: LLM not available."

        logging.debug(f"Generating response for prompt: {prompt[:50]}...")
        try:
            # Actual inference logic
            response = self.model(
                prompt,
                max_tokens=self.config['max_tokens'],
                temperature=self.config['temperature'],
                stop=["\n", "User:", "Assistant:"] # Adjust stop sequences as needed
            )
            generated_text = response['choices'][0]['text'].strip()
            
            logging.debug(f"LLM Response: {generated_text[:100]}...")
            return generated_text
        except Exception as e:
            logging.error(f"Error during LLM generation: {e}", exc_info=True)
            return "Error: Could not generate response."

# Example usage (for testing):
if __name__ == '__main__':
    # This part would require a dummy config for direct execution
    logging.basicConfig(level=logging.INFO)
    dummy_config = {
        'model_path': 'dummy/path/model.gguf',
        'n_gpu_layers': 0, 
        'n_ctx': 512,
        'max_tokens': 100,
        'temperature': 0.7
    }
    
    # In a real scenario, loading might fail if the path is invalid or llama-cpp-python is not installed
    try:
        # Note: This example still uses a dummy config and simulates the model object
        # for direct execution without needing the actual model file here.
        # To test the real loading, run the main application.
        class MockLLMInterface:
            def __init__(self, config):
                self.config = config
                print(f"Simulating LLM load with config: {config}")
                self.model = "Simulated Llama Model Object"
            def generate(self, prompt):
                print(f"Simulating generation for: {prompt[:50]}...")
                return f"Simulated response to: {prompt}"

        llm_interface = MockLLMInterface(dummy_config)
        prompt = "Explain the concept of Large Language Models in simple terms."
        response = llm_interface.generate(prompt)
        print(f"Prompt: {prompt}")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Could not run example: {e}")