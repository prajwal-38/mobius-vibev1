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
from tts.tts_service import speak_text # Added import

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
                system_prompt = "You are RAGnarok, a helpful AI designed to answer questions and act as a concise personal cybersecurity assistant. You are trained of deepseek ai model. Respond directly to the user's last message, considering the conversation history.Useful for answering general questions about cybersecurity concepts, threats, vulnerabilities, and best practices based on stored documents. Input should be the question itself."
                prompt_parts = [system_prompt] # Start with the system prompt
                for turn in context:
                    prompt_parts.append(f"User: {turn['user']}")
                    prompt_parts.append(f"Assistant: {turn['assistant']}")
                prompt_parts.append(f"User: {user_input}")
                prompt_parts.append("Assistant:") # Prompt the assistant for its turn
                prompt = "\n".join(prompt_parts)

                # 5. Decide Action: Execute Task or Generate LLM Response
                final_response = None
                task_executed = False
                # Check if the intent is one that should trigger a direct task execution
                actionable_intents = [
                    'schedule_meeting', 'send_email', 'send_message', 
                    'open_application', 'close_application', 'search_web', 
                    'set_reminder', 'schedule_event', 'get_current_datetime', # Added date/time intent
                    'run_whois', 'run_nmap' # Added whois and nmap intents
                ]
                logging.debug(f"Checking intent '{intent}' against actionable intents: {actionable_intents}")
                
                if intent in actionable_intents:
                    logging.info(f"Intent '{intent}' is actionable. Executing task...")
                    task_result = self.executor.execute_task(nlu_result)
                    # Log confirmation/snippet instead of full result to avoid console duplication via StreamHandler
                    logging.info(f"Task '{intent}' executed. Result length: {len(str(task_result))}") 
                    final_response = task_result # Use task result as the primary response
                    task_executed = True
                elif intent == 'error': # Handle NLU error explicitly
                    final_response = nlu_result.get('error', 'An NLU processing error occurred.')
                    logging.warning(f"NLU Error reported: {final_response}")
                    task_executed = True # Technically an action (reporting error)
                
                # If no specific task was executed (or intent was unknown/not actionable), generate a response using LLM
                logging.debug(f"Task executed flag: {task_executed}. Intent was: '{intent}'.")
                if not task_executed:
                    logging.info(f"Intent '{intent}' not actionable or task not executed. Generating LLM response and speaking concurrently.")
                    # Generate LLM Response (streaming) and speak sentence by sentence
                    print("Assistant: ", end="", flush=True)
                    full_response = ""
                    current_sentence = ""
                    sentence_ends = {'.', '!', '?'}

                    for token in self.llm.generate(prompt):
                        print(token, end="", flush=True) # Still print token immediately
                        full_response += token
                        current_sentence += token

                        # Check if the token ends a sentence (simple check)
                        # Consider more robust sentence boundary detection if needed
                        if token.strip() and token.strip()[-1] in sentence_ends:
                            # Speak the completed sentence
                            sentence_to_speak = current_sentence.strip()
                            if sentence_to_speak:
                                try:
                                    # Use the existing synchronous wrapper which handles the async call
                                    logging.info(f"CLI: Attempting to speak sentence: '{sentence_to_speak[:30]}...' ") # ADDED LOGGING
                                    speak_text(sentence_to_speak)
                                    logging.info(f"CLI: Finished speaking sentence: '{sentence_to_speak[:30]}...' ") # ADDED LOGGING
                                except Exception as tts_e:
                                    logging.error(f"TTS Error during sentence playback: {tts_e}", exc_info=True)
                                    print("\n(TTS failed for sentence)") # Indicate failure
                            current_sentence = "" # Reset for the next sentence

                    # Speak any remaining part after the loop finishes
                    final_sentence_part = current_sentence.strip()
                    if final_sentence_part:
                        try:
                            logging.info(f"CLI: Attempting to speak final part: '{final_sentence_part[:30]}...' ") # ADDED LOGGING
                            speak_text(final_sentence_part)
                            logging.info(f"CLI: Finished speaking final part: '{final_sentence_part[:30]}...' ") # ADDED LOGGING
                        except Exception as tts_e:
                            logging.error(f"TTS Error for final sentence part: {tts_e}", exc_info=True)
                            print("\n(TTS failed for final part)")

                    print() # Add a newline after the streaming is complete
                    final_response = full_response # Store the complete response for memory
                    logging.info(f"LLM Response (full): {final_response[:100]}...")
                else:
                    # If a task was executed, print its result normally
                    print(f"Assistant: {final_response}")
                    # Speak the task result as well
                    if final_response:
                        try:
                            logging.info(f"CLI: Attempting to speak task result: '{str(final_response)[:30]}...' ") # ADDED LOGGING
                            speak_text(final_response)
                            logging.info(f"CLI: Finished speaking task result: '{str(final_response)[:30]}...' ") # ADDED LOGGING
                        except Exception as tts_e:
                            logging.error(f"TTS Error for task result: {tts_e}", exc_info=True)
                            print("(TTS failed to play task response)")

                # Remove the original speak_text call here as it's handled above
                # if final_response:
                #     try:
                #         speak_text(final_response)
                #     except Exception as tts_e:
                #         logging.error(f"TTS Error: {tts_e}", exc_info=True)
                #         # Optionally inform the user TTS failed, but continue
                #         print("(TTS failed to play response)")

                # 6. Update Memory
                # Use the final response that was generated/executed
                self.memory.add_short_term(user_input, final_response)
                # Optionally save things to long-term memory based on interaction
                # self.memory.save_long_term(...) 

                # 7. Display Response (Handled above for streaming/non-streaming cases)

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
        def generate(self, prompt):
            # Simulate streaming for the dummy
            response = f"Simulated streaming response to: {prompt}"
            import time
            for char in response:
                yield char
                time.sleep(0.01)
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