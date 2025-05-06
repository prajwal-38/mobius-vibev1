import logging
from llama_cpp import Llama 

class LLMInterface:
    def __init__(self, llm_config):
        self.config = llm_config
        self.model = None
        self._load_model()

    def _load_model(self):
        
        logging.info(f"Loading LLM from: {self.config['model_path']}")
        try:
            
            self.model = Llama(
                model_path=self.config['model_path'],
                n_gpu_layers=self.config['n_gpu_layers'],
                n_ctx=self.config['n_ctx'],
                f16_kv=self.config.get('fp16', True), 
                verbose=False 
            )
            logging.info("LLM loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load LLM: {e}", exc_info=True)
            
            
            raise

    def generate(self, prompt):
        
        if not self.model:
            logging.error("LLM not loaded. Cannot generate text.")
            yield "Error: LLM not available."
            return

        logging.debug(f"Generating streaming response for prompt: {prompt[:50]}...")
        try:
            
            stream = self.model(
                prompt,
                max_tokens=self.config['max_tokens'],
                temperature=self.config['temperature'],
                stop=["User:", "Assistant:"], 
                stream=True
            )

            
            for output in stream:
                token_text = output['choices'][0]['text']
                
                yield token_text

        except Exception as e:
            logging.error(f"Error during LLM streaming generation: {e}", exc_info=True)
            yield "Error: Could not generate response."


if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO)
    dummy_config = {
        'model_path': 'dummy/path/model.gguf',
        'n_gpu_layers': 0, 
        'n_ctx': 512,
        'max_tokens': 100,
        'temperature': 0.7
    }
    
    
    try:
        
        
        
        class MockLLMInterface:
            def __init__(self, config):
                self.config = config
                print(f"Simulating LLM load with config: {config}")
                self.model = "Simulated Llama Model Object"
            def generate(self, prompt):
                print(f"Simulating streaming generation for: {prompt[:50]}...")
                
                response = f"Simulated response to: {prompt}"
                import time
                for char in response:
                    yield char
                    time.sleep(0.02) 

        llm_interface = MockLLMInterface(dummy_config)
        prompt = "Explain the concept of Large Language Models in simple terms."
        print(f"Prompt: {prompt}")
        print("Response (streaming): ", end="")
        full_response = ""
        for token in llm_interface.generate(prompt):
            print(token, end="", flush=True)
            full_response += token
        print() 
        print(f"\nFull collected response: {full_response}")
    except Exception as e:
        print(f"Could not run example: {e}")