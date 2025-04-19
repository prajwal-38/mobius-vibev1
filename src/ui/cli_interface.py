# src/ui/cli_interface.py
"""
Command Line Interface (CLI) for the Personal Assistant.

Handles the main interaction loop: getting user input, processing it,
and displaying the assistant's response.

Inputs:
- LLM Interface instance
- NLU Processor instance
- Memory Manager instance
- Task Executor instance

Outputs:
- Prints assistant responses to the console.
"""

import logging

class CommandLineInterface:
    def __init__(self, llm_interface, nlu_processor, memory_manager, task_executor):
        self.llm = llm_interface
        self.nlu = nlu_processor
        self.memory = memory_manager
        self.executor = task_executor
        logging.info("Command Line Interface initialized.")

    def run(self):
        """Starts the main interaction loop for the CLI."""
        print("Mobius Vibe Assistant CLI started. Type 'quit' or 'exit' to end.")
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['quit', 'exit']:
                    logging.info("Exiting CLI loop.")
                    break

                if not user_input:
                    continue

                # 1. Process NLU
                nlu_result = self.nlu.process(user_input)
                intent = nlu_result.get('intent', 'unknown')
                entities = nlu_result.get('entities', {})
                logging.info(f"NLU Result: Intent={intent}, Entities={entities}")

                # 2. Retrieve relevant memory
                context = self.memory.get_short_term_context()
                # long_term_info = self.memory.retrieve_long_term(...) # Example

                # 3. Generate Prompt for LLM (incorporating context/memory)
                prompt_parts = []
                for turn in context:
                    prompt_parts.append(f"User: {turn['user']}")
                    prompt_parts.append(f"Assistant: {turn['assistant']}")
                prompt_parts.append(f"User: {user_input}")
                prompt_parts.append("Assistant:") # Prompt the assistant for its turn
                prompt = "\n".join(prompt_parts)

                # 4. Get LLM Response
                assistant_response = self.llm.generate(prompt)
                logging.info(f"LLM Response: {assistant_response[:100]}...")

                # 5. Decide Action: Execute Task or Generate LLM Response
                final_response = None
                task_executed = False
                # Check if the intent is one that should trigger a direct task execution
                actionable_intents = [
                    'schedule_meeting', 'send_email', 'send_message', 
                    'open_application', 'close_application', 'search_web', 
                    'set_reminder', 'schedule_event'
                ]
                if intent in actionable_intents:
                    task_result = self.executor.execute_task(nlu_result)
                    logging.info(f"Task Execution Result: {task_result}")
                    final_response = task_result # Use task result as the primary response
                    task_executed = True
                elif intent == 'error': # Handle NLU error explicitly
                    final_response = nlu_result.get('error', 'An NLU processing error occurred.')
                    task_executed = True # Technically an action (reporting error)
                # elif intent == 'unknown_intent': # Let LLM handle unknown intents
                #     pass # Fall through to LLM generation
                
                # If no specific task was executed, generate a response using LLM
                if not task_executed:
                    # 4. Get LLM Response (using context)
                    final_response = self.llm.generate(prompt)
                    logging.info(f"LLM Response: {final_response[:100]}...")

                # 6. Update Memory
                # Use the final response that was shown to the user
                self.memory.add_short_term(user_input, final_response)
                # Optionally save things to long-term memory based on interaction
                # self.memory.save_long_term(...) 

                # 7. Display Response
                print(f"Assistant: {final_response}")

            except KeyboardInterrupt:
                logging.info("Keyboard interrupt received. Exiting.")
                break
            except Exception as e:
                logging.error(f"An error occurred in the main loop: {e}", exc_info=True)
                print("Assistant: Sorry, an internal error occurred. Please check the logs.")

        # Cleanup
        self.memory.close()
        logging.info("CLI loop finished.")

# Example usage (requires dummy components if run directly)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("Running CLI Interface example requires setting up dummy components.")
    # Dummy components for basic testing (replace with actual instances)
    class DummyLLM: 
        def generate(self, prompt): return f"Simulated LLM response to: {prompt}"
    class DummyNLU: 
        def process(self, text): return {'intent': 'simulated_intent', 'entities': {'text': text}}
    class DummyMemory: 
        def add_short_term(self, u, a): pass
        def get_short_term_context(self): return []
        def save_long_term(self, c, k, v): pass
        def retrieve_long_term(self, k): return None
        def close(self): pass
    class DummyExecutor:
        def execute_task(self, nlu_res): return f"Simulated task execution for: {nlu_res}"

    try:
        cli = CommandLineInterface(DummyLLM(), DummyNLU(), DummyMemory(), DummyExecutor())
        # cli.run() # Uncomment to run the loop (will use dummy components)
        print("Dummy CLI initialized. Uncomment 'cli.run()' to start interaction.")
    except Exception as e:
        print(f"Could not run CLI example: {e}")