import streamlit as st
import os
import sys
import logging

# Add the project root to the Python path to allow imports from src
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
sys.path.insert(0, project_root)

from src.utils.config_loader import load_config
from src.utils.logger_setup import setup_logging
from src.llm.llm_interface import LLMInterface
from src.nlu.nlu_processor import NLUProcessor
from src.memory.memory_manager import MemoryManager
from src.task_manager.task_executor import TaskExecutor
from src.tts.tts_service import speak_text

# --- Configuration and Initialization ---

def load_components():
    """Loads configuration and initializes all necessary components."""
    try:
        config_path = os.path.join(project_root, 'config.yaml')
        config = load_config(config_path)
        # Setup logging (optional for streamlit, but good practice)
        # setup_logging(config['logging'])
        logging.info("Initializing components for Streamlit UI...")

        llm_interface = LLMInterface(config['llm'])
        nlu_processor = NLUProcessor(config['nlu'])
        memory_manager = MemoryManager(config['memory'])
        task_executor = TaskExecutor(config.get('api_keys', {}), llm_interface)

        logging.info("Components initialized successfully.")
        return llm_interface, nlu_processor, memory_manager, task_executor, config
    except FileNotFoundError as e:
        st.error(f"Error: Configuration file not found. {e}")
        logging.error(f"Configuration file error: {e}", exc_info=True)
        return None, None, None, None, None
    except KeyError as e:
        st.error(f"Error: Missing configuration key. Please check config.yaml. Missing key: {e}")
        logging.error(f"Configuration key error: {e}", exc_info=True)
        return None, None, None, None, None
    except Exception as e:
        st.error(f"An unexpected error occurred during initialization: {e}")
        logging.error(f"Initialization error: {e}", exc_info=True)
        return None, None, None, None, None

# --- Streamlit App Logic ---

st.set_page_config(page_title="RAGnarok Assistant", layout="wide", initial_sidebar_state="collapsed")

# --- Custom CSS --- (Injecting CSS for a better look)
st.markdown("""
<style>
    /* General body styling */
    .stApp {
        background-color: #1a1a2e; /* Dark blue background */
        color: #e0e0e0; /* Light grey text */
    }

    /* Main title styling */
    h1 {
        color: #00ffff; /* Cyan title color */
        text-align: center;
        padding-top: 20px;
        font-family: 'Consolas', 'Monaco', monospace;
    }

    /* Chat input styling */
    .stChatInputContainer > div > div > textarea {
        background-color: #2a2a3e;
        color: #e0e0e0;
        border: 1px solid #00ffff;
    }
    .stChatInputContainer > div > button {
        background-color: #00ffff;
        color: #1a1a2e;
        border: none;
    }
    .stChatInputContainer > div > button:hover {
        background-color: #00cccc;
    }

    /* Chat message styling */
    [data-testid="stChatMessage"] {
        background-color: #2a2a3e; /* Slightly lighter background for messages */
        border-radius: 10px;
        padding: 10px 15px;
        margin-bottom: 10px;
        border: 1px solid #4a4a5e;
    }
    [data-testid="stChatMessage"][data-testid*="user"] {
        background-color: #3a3a4e; /* Different background for user */
        border-left: 5px solid #00ffff;
    }
    [data-testid="stChatMessage"][data-testid*="assistant"] {
        border-left: 5px solid #ff69b4; /* Different border for assistant */
    }

    /* Markdown styling within chat */
    [data-testid="stChatMessage"] .stMarkdown p {
        color: #e0e0e0; /* Ensure text color is consistent */
    }

    /* Spinner styling */
    .stSpinner > div {
        border-top-color: #00ffff !important; /* Cyan spinner */
    }

    /* Sidebar styling (if you add one later) */
    [data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }

</style>
""", unsafe_allow_html=True)

st.title(" RAGnarok - Your Cybersecurity Assistant ")

# Initialize components and store in session state if not already done
if 'initialized' not in st.session_state:
    with st.spinner("Initializing RAGnarok..."):
        st.session_state.llm, st.session_state.nlu, st.session_state.memory, st.session_state.executor, st.session_state.config = load_components()
    if st.session_state.llm: # Check if initialization was successful
        st.session_state.initialized = True
        st.session_state.messages = [] # Initialize chat history
        # Add initial assistant message
        st.session_state.messages.append({"role": "assistant", "content": "Hello! I am RAGnarok, your cybersecurity assistant. How can I help you today?"})
        st.toast("RAGnarok is ready!", icon="🤖")
    else:
        st.session_state.initialized = False
        st.warning("Assistant could not be initialized. Please check configuration and logs.")

# Display chat messages from history
if st.session_state.initialized:
    # Create a container for chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Accept user input - Place input at the bottom
    if prompt := st.chat_input("Ask RAGnarok..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message immediately in the container
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # --- Process Input and Generate Response (Adapted from CLI) ---
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty() # Placeholder for streaming response
                full_response = ""
                final_response_for_memory = ""

                try:
                    # 1. Process NLU
                    nlu_result = st.session_state.nlu.process(prompt)
                    intent = nlu_result.get('intent', 'unknown')
                    entities = nlu_result.get('entities', {})
                    logging.info(f"NLU Result: Intent={intent}, Entities={entities}")

                    # 2. Decide Action: Task or LLM
                    # Ensure config and actionable_intents are loaded correctly
                    actionable_intents = []
                    if st.session_state.config and 'nlu' in st.session_state.config and 'actionable_intents' in st.session_state.config['nlu']:
                        actionable_intents = st.session_state.config['nlu']['actionable_intents']
                    else:
                        logging.warning("Could not load 'actionable_intents' from config. Using empty list.")
                        st.toast("Warning: Actionable intents configuration missing.", icon="⚠️")

                    task_executed = False

                    if intent in actionable_intents:
                        logging.info(f"Intent '{intent}' is actionable. Executing task...")
                        with st.spinner(f"RAGnarok is working on: {intent}..."):
                            task_result = st.session_state.executor.execute_task(nlu_result)
                        logging.info(f"Task '{intent}' executed. Result snippet: {str(task_result)[:100]}")
                        final_response_for_memory = str(task_result) # Ensure it's a string
                        message_placeholder.markdown(final_response_for_memory)
                        task_executed = True
                    elif intent == 'error':
                        final_response_for_memory = nlu_result.get('error', 'An NLU processing error occurred.')
                        logging.warning(f"NLU Error reported: {final_response_for_memory}")
                        message_placeholder.error(f"NLU Error: {final_response_for_memory}") # Use st.error for errors
                        task_executed = True # Technically an action (reporting error)

                    # 3. Generate LLM Response if no task was run
                    if not task_executed:
                        logging.info(f"Intent '{intent}' not actionable or task not executed. Generating LLM response...")
                        # Retrieve context for prompt
                        context = st.session_state.memory.get_short_term_context()
                        # Ensure config and system_prompt are loaded correctly
                        system_prompt = "You are RAGnarok, a helpful AI cybersecurity assistant."
                        if st.session_state.config and 'llm' in st.session_state.config and 'system_prompt' in st.session_state.config['llm']:
                            system_prompt = st.session_state.config['llm']['system_prompt']
                        else:
                            logging.warning("Could not load 'system_prompt' from config. Using default.")

                        prompt_parts = [system_prompt]
                        for turn in context:
                            prompt_parts.append(f"User: {turn['user']}")
                            prompt_parts.append(f"Assistant: {turn['assistant']}")
                        prompt_parts.append(f"User: {prompt}")
                        prompt_parts.append("Assistant:")
                        llm_prompt = "\n".join(prompt_parts)

                        # Stream response
                        try:
                            stream = st.session_state.llm.generate(llm_prompt)
                            for token in stream:
                                full_response += token
                                message_placeholder.markdown(full_response + "▌") # Show cursor during streaming
                            message_placeholder.markdown(full_response) # Final response without cursor
                            final_response_for_memory = full_response
                            logging.info(f"LLM Response (full): {final_response_for_memory[:100]}...")
                        except Exception as llm_e:
                            logging.error(f"LLM generation error: {llm_e}", exc_info=True)
                            message_placeholder.error(f"Error generating response: {llm_e}")
                            final_response_for_memory = f"Error generating response: {llm_e}"

                    # 4. Speak the response (LLM or Task Result)
                    if final_response_for_memory and isinstance(final_response_for_memory, str):
                        try:
                            logging.info(f"Streamlit: Attempting to speak: '{final_response_for_memory[:50]}...' ")
                            # Consider making TTS optional via config or UI toggle
                            speak_text(final_response_for_memory) # Uncommented this line
                            logging.info(f"Streamlit: Finished speaking (or TTS skipped).")
                        except Exception as tts_e:
                            logging.error(f"TTS Error in Streamlit: {tts_e}", exc_info=True)
                            st.toast("TTS failed to play response.", icon="🔇") # Non-blocking notification

                    # 5. Update Memory & Add assistant response to chat history
                    if isinstance(final_response_for_memory, str):
                        st.session_state.memory.add_short_term(prompt, final_response_for_memory)
                        st.session_state.messages.append({"role": "assistant", "content": final_response_for_memory})
                    else:
                        # Handle cases where the response might not be a string (e.g., task error object)
                        logging.warning(f"Response for memory was not a string: {type(final_response_for_memory)}")
                        st.session_state.memory.add_short_term(prompt, "[Non-textual response]")
                        st.session_state.messages.append({"role": "assistant", "content": "[Non-textual response]"})

                except Exception as e:
                    logging.error(f"An error occurred processing input in Streamlit: {e}", exc_info=True)
                    error_msg = f"Sorry, an internal error occurred: {e}"
                    st.error(error_msg)
                    # Add error message to chat history
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

        # Rerun to clear the input box and refresh the chat display
        st.rerun()

# Optional: Add a way to clear history or re-initialize in a sidebar?
# with st.sidebar:
#    st.header("Controls")
#    if st.button("Clear Chat History"):
#        st.session_state.messages = [
#            {"role": "assistant", "content": "Hello! I am RAGnarok, your cybersecurity assistant. How can I help you today?"}
#        ]
#        st.session_state.memory.clear_short_term() # Assuming a method to clear memory
#        st.rerun()

# To run this app:
# 1. Make sure you have streamlit installed: pip install streamlit
# 2. Navigate to the project root directory in your terminal.
# 3. Run: streamlit run src/ui/streamlit_app.py