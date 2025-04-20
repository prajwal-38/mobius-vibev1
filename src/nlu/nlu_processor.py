# src/nlu/nlu_processor.py
"""
Natural Language Understanding (NLU) Processor.

Handles intent recognition and entity extraction from user input.

Inputs:
- User input text (string)
- NLU configuration (from config.yaml)

Outputs:
- Dictionary containing recognized intent and extracted entities.
  Example: {'intent': 'schedule_meeting', 'entities': {'person': 'Alice', 'time': 'tomorrow 10 AM'}}
"""

import logging
import spacy # Or import from transformers

class NLUProcessor:
    def __init__(self, nlu_config):
        self.config = nlu_config
        self.nlp = None
        self._load_nlu_model()

    def _load_nlu_model(self):
        """Loads the NLU model (e.g., spaCy)."""
        model_name = self.config.get('spacy_model', 'en_core_web_sm')
        logging.info(f"Loading NLU model: {model_name}")
        try:
            # Actual loading of spaCy model
            self.nlp = spacy.load(model_name)
            logging.info("NLU model loaded successfully.")
        except OSError:
            logging.error(f"Could not find spaCy model '{model_name}'. "
                          f"Please download it (e.g., python -m spacy download {model_name})")
            self.nlp = None # Ensure nlp is None if loading fails
        except Exception as e:
            logging.error(f"Failed to load NLU model '{model_name}': {e}", exc_info=True)
            # Consider fallback or raising the error
            self.nlp = None

    def process(self, text):
        """Processes the input text to extract intent and entities."""
        if not self.nlp:
            logging.error("NLU model not loaded. Cannot process text.")
            return {'intent': 'error', 'entities': {}, 'error': 'NLU model unavailable'}

        logging.debug(f"Processing NLU for text: {text[:50]}...")
        try:
            # Actual NLU processing logic
            doc = self.nlp(text)
            intent = self._recognize_intent(doc) # Basic intent logic (can be expanded)
            entities = self._extract_entities(doc) # Basic entity extraction
            
            logging.debug(f"NLU Result - Intent: {intent}, Entities: {entities}")
            return {'intent': intent, 'entities': entities}
        except Exception as e:
            logging.error(f"Error during NLU processing: {e}", exc_info=True)
            return {'intent': 'error', 'entities': {}, 'error': 'NLU processing failed'}

    # --- Intent & Entity Recognition Logic ---

    def _recognize_intent(self, doc):
        """Recognizes intent based on keywords and basic patterns."""
        text_lower = doc.text.lower()
        tokens_lemma = {token.lemma_ for token in doc}

        # Order matters: more specific intents first
        if 'meeting' in tokens_lemma and any(t in tokens_lemma for t in ["schedule", "book", "set up", "arrange"]):
            return "schedule_meeting"
        elif any(t in tokens_lemma for t in ["email", "mail"]) and 'send' in tokens_lemma:
            return "send_email"
        elif any(t in tokens_lemma for t in ["message", "note"]) and 'send' in tokens_lemma:
            return "send_message" # Could be SMS, Slack, etc. - needs context
        # Simplified intent check for opening things
        elif any(t in tokens_lemma for t in ["open", "launch", "start"]):
            # Check if there's a likely object following the verb
            for token in doc:
                if token.lemma_ in ["open", "launch", "start"] and token.i + 1 < len(doc):
                    # Check if the next token is a noun, proper noun, or potentially an app name
                    next_token = doc[token.i + 1]
                    if next_token.pos_ in ['NOUN', 'PROPN', 'X'] or next_token.is_title or next_token.text.lower() in ['chrome', 'firefox', 'edge', 'notepad', 'calculator']:
                        return "open_application"
            # If 'open' is present but no clear object, maybe it's a generic open?
            # Decide if you want a fallback or require an object.
            # For now, let's require an object found above.
        # Relaxed web search intent: trigger on search verbs if not matched elsewhere
        elif any(t in tokens_lemma for t in ["search", "find", "look up", "google"]):
            # Add a check here to avoid capturing things like 'find my keys' if you add a 'find_object' intent later
            # For now, assume if it has a search verb and isn't another intent, it's a web search.
            return "search_web"
        elif any(t in tokens_lemma for t in ["reminder", "remind"]):
             return "set_reminder"
        elif any(t in tokens_lemma for t in ["close", "exit", "quit"]):
             return "close_application" # Added close intent
        elif any(t in tokens_lemma for t in ["date", "time", "day", "today"]) and not any(t in tokens_lemma for t in ["schedule", "meeting", "reminder"]):
             return "get_current_datetime"

        # Generic scheduling/sending if specific type isn't clear
        elif any(t in tokens_lemma for t in ["schedule", "book", "set up"]):
            return "schedule_event" # Generic event
        elif any(t in tokens_lemma for t in ["send"]):
            return "send_message" # Generic send

        # Fallback
        return "unknown_intent"

    def _extract_entities(self, doc):
        """Extracts entities using spaCy NER and basic pattern matching."""
        entities = {}
        # Extract standard NER entities
        for ent in doc.ents:
            label = ent.label_.lower()
            # Consolidate date/time
            if label in ['date', 'time']:
                if 'datetime' not in entities:
                    entities['datetime'] = []
                entities['datetime'].append(ent.text)
            elif label == 'person':
                 entities.setdefault('person', []).append(ent.text)
            elif label == 'org' or label == 'product': # Potential app/company names
                 entities.setdefault('object_name', []).append(ent.text)
            else:
                entities[label] = ent.text # Store other entities directly

        # Combine multiple date/time entities if found
        if 'datetime' in entities:
            entities['datetime'] = ' '.join(entities['datetime'])

        # Simple pattern for email addresses (if not caught by NER)
        for token in doc:
            if token.like_email:
                entities['email_address'] = token.text

        # Simple pattern for application name after 'open'/'close'
        intent = self._recognize_intent(doc) # Re-check intent for context
        # Improved entity extraction for application names
        if intent in ['open_application', 'close_application'] and 'object_name' not in entities:
            trigger_lemmas = ['open', 'launch', 'start', 'close', 'quit', 'exit']
            for token in doc:
                if token.lemma_ in trigger_lemmas and token.i + 1 < len(doc):
                    # Capture the text following the trigger word
                    potential_name_parts = []
                    for j in range(token.i + 1, len(doc)):
                        next_token = doc[j]
                        # Stop if we hit punctuation or another verb perhaps?
                        if next_token.is_punct or next_token.pos_ == 'VERB':
                            break
                        potential_name_parts.append(next_token.text)
                        # Simple heuristic: stop after a few words or if it doesn't look like a name
                        if len(potential_name_parts) > 3:
                             break
                    if potential_name_parts:
                        extracted_name = ' '.join(potential_name_parts)
                        # Ensure 'object_name' is initialized as a list if it doesn't exist
                        if 'object_name' not in entities:
                            entities['object_name'] = []
                        # Append the extracted name to the list
                        entities['object_name'].append(extracted_name)
                        # No direct string assignment needed, always use the list
                        break # Found a potential name after the first trigger word

        # Extract potential search query for 'search_web'
        if intent == 'search_web':
            search_keywords = ['search', 'find', 'look up', 'google']
            prepositions = ['for', 'about', 'on']
            query_parts = []
            start_index = -1
            # Find the keyword that triggered the intent
            for i, token in enumerate(doc):
                if token.lemma_ in search_keywords:
                    start_index = i
                    break
            # Extract text after the keyword and optional preposition
            if start_index != -1:
                current_index = start_index + 1
                # Skip optional preposition
                if current_index < len(doc) and doc[current_index].lemma_ in prepositions:
                    current_index += 1
                # Skip common filler words immediately after keyword/preposition
                skippable_lemmas = {'me', 'us', 'some', 'any', 'a', 'an', 'the'} # Add more if needed
                while current_index < len(doc) and doc[current_index].lemma_ in skippable_lemmas:
                    current_index += 1
                # Take the rest of the sentence as the query
                query_parts = [token.text for token in doc[current_index:]]
            if query_parts:
                entities['search_query'] = ' '.join(query_parts).strip()

        return entities

# Example usage (for testing):
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dummy_config = {'spacy_model': 'en_core_web_sm'}
    
    # In a real scenario, loading might fail if the model isn't downloaded
    try:
        # Ensure the model is downloaded: python -m spacy download en_core_web_sm
        nlu_processor = NLUProcessor(dummy_config)
        if nlu_processor.nlp: # Check if model loaded successfully
            text1 = "Schedule a meeting with Bob for next Tuesday at 3 PM."
            result1 = nlu_processor.process(text1)
            print(f"Input Text: {text1}")
            print(f"NLU Result: {result1}")

            text2 = "Send an email to alice@example.com about the project update."
            result2 = nlu_processor.process(text2)
            print(f"\nInput Text: {text2}")
            print(f"NLU Result: {result2}")
        else:
            print("NLU model could not be loaded. Skipping example.")
    except Exception as e:
        print(f"Could not run NLU example: {e}")