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

    # Basic placeholder methods for intent/entity logic
    def _recognize_intent(self, doc):
        # TODO: Implement more sophisticated intent recognition (rules, ML model)
        # Simple example: Check for keywords
        if any(token.lemma_ in ["schedule", "book", "set up"] for token in doc):
            return "schedule_event"
        elif any(token.lemma_ in ["send", "email", "message"] for token in doc):
            return "send_message"
        # Add more rules or integrate a classifier
        return "unknown_intent"

    def _extract_entities(self, doc):
        # Extract entities using spaCy's built-in NER
        entities = {}
        for ent in doc.ents:
            # Use lowercase label for consistency
            entities[ent.label_.lower()] = ent.text
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