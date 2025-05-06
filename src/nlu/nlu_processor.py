import logging
import spacy 
import re 

class NLUProcessor:
    def __init__(self, nlu_config):
        self.config = nlu_config
        self.nlp = None
        self._load_nlu_model()

    def _load_nlu_model(self):
        model_name = self.config.get('spacy_model', 'en_core_web_sm')
        logging.info(f"Loading NLU model: {model_name}")
        try:
            self.nlp = spacy.load(model_name)
            logging.info("NLU model loaded successfully.")
        except OSError:
            logging.error(f"Could not find spaCy model '{model_name}'. "
                          f"Please download it (e.g., python -m spacy download {model_name})")
            self.nlp = None 
        except Exception as e:
            logging.error(f"Failed to load NLU model '{model_name}': {e}", exc_info=True)
            self.nlp = None

    def process(self, text):
        if not self.nlp:
            logging.error("NLU model not loaded. Cannot process text.")
            return {'intent': 'error', 'entities': {}, 'error': 'NLU model unavailable'}

        logging.debug(f"Processing NLU for text: {text[:50]}...")
        try:
            doc = self.nlp(text)
            intent = self._recognize_intent(doc) 
            entities = self._extract_entities(doc) 
            
            logging.debug(f"NLU Result - Intent: {intent}, Entities: {entities}")
            return {'intent': intent, 'entities': entities}
        except Exception as e:
            logging.error(f"Error during NLU processing: {e}", exc_info=True)
            return {'intent': 'error', 'entities': {}, 'error': 'NLU processing failed'}

    

    def _recognize_intent(self, doc):
        text_lower = doc.text.lower()
        tokens_lemma = {token.lemma_ for token in doc}

        
        if 'meeting' in tokens_lemma and any(t in tokens_lemma for t in ["schedule", "book", "set up", "arrange"]):
            return "schedule_meeting"
        elif any(t in tokens_lemma for t in ["email", "mail"]) and 'send' in tokens_lemma:
            return "send_email"
        elif any(t in tokens_lemma for t in ["message", "note"]) and 'send' in tokens_lemma:
            return "send_message" 
        
        elif any(t in tokens_lemma for t in ["open", "launch", "start"]):
            
            for token in doc:
                if token.lemma_ in ["open", "launch", "start"] and token.i + 1 < len(doc):
                    
                    next_token = doc[token.i + 1]
                    if next_token.pos_ in ['NOUN', 'PROPN', 'X'] or next_token.is_title or next_token.text.lower() in ['chrome', 'firefox', 'edge', 'notepad', 'calculator']:
                        return "open_application"
            
            
            
        
        elif any(t in tokens_lemma for t in ["search", "find", "look up", "google"]):
            
            
            return "search_web"
        elif any(t in tokens_lemma for t in ["reminder", "remind"]):
             return "set_reminder"
        elif any(t in tokens_lemma for t in ["close", "exit", "quit"]):
             return "close_application" 
        elif any(t in tokens_lemma for t in ["date", "time", "day", "today"]) and not any(t in tokens_lemma for t in ["schedule", "meeting", "reminder"]):
             return "get_current_datetime"

        
        elif any(t in tokens_lemma for t in ["schedule", "book", "set up"]):
            return "schedule_event" 
        elif any(t in tokens_lemma for t in ["send"]):
            return "send_message" 
        elif any(t in tokens_lemma for t in ["nmap"]):
            return "run_nmap"
        elif any(t in tokens_lemma for t in ["whois"]):
            return "run_whois"

        
        return "unknown_intent"

    def _extract_entities(self, doc):
        entities = {}
        
        for ent in doc.ents:
            label = ent.label_.lower()
            
            if label in ['date', 'time']:
                if 'datetime' not in entities:
                    entities['datetime'] = []
                entities['datetime'].append(ent.text)
            elif label == 'person':
                 entities.setdefault('person', []).append(ent.text)
            elif label == 'org' or label == 'product': 
                 entities.setdefault('object_name', []).append(ent.text)
            else:
                entities[label] = ent.text 

        
        if 'datetime' in entities:
            entities['datetime'] = ' '.join(entities['datetime'])

        
        for token in doc:
            if token.like_email:
                entities['email_address'] = token.text

        
        intent = self._recognize_intent(doc) 
        
        if intent in ['open_application', 'close_application'] and 'object_name' not in entities:
            trigger_lemmas = ['open', 'launch', 'start', 'close', 'quit', 'exit']
            for token in doc:
                if token.lemma_ in trigger_lemmas and token.i + 1 < len(doc):
                    
                    potential_name_parts = []
                    for j in range(token.i + 1, len(doc)):
                        next_token = doc[j]
                        
                        if next_token.is_punct or next_token.pos_ == 'VERB':
                            break
                        potential_name_parts.append(next_token.text)
                        
                        if len(potential_name_parts) > 3:
                             break
                    if potential_name_parts:
                        extracted_name = ' '.join(potential_name_parts)
                        
                        if 'object_name' not in entities:
                            entities['object_name'] = []
                        
                        entities['object_name'].append(extracted_name)
                        
                        break 

        
        if intent == 'search_web':
            search_keywords = ['search', 'find', 'look up', 'google']
            prepositions = ['for', 'about', 'on']
            query_parts = []
            start_index = -1
            
            for i, token in enumerate(doc):
                if token.lemma_ in search_keywords:
                    start_index = i
                    break
            
            if start_index != -1:
                current_index = start_index + 1
                
                if current_index < len(doc) and doc[current_index].lemma_ in prepositions:
                    current_index += 1
                
                while current_index < len(doc) and doc[current_index].pos_ in ['DET', 'PRON']:
                    current_index += 1
                
                query_parts = [token.text for token in doc[current_index:]]
            if query_parts:
                entities['search_query'] = ' '.join(query_parts).strip()

        
        if intent in ['run_nmap', 'run_whois'] and 'target_address' not in entities:
            trigger_lemmas = ['nmap', 'whois']
            prepositions = ['at', 'on', 'for']
            ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$") 
            
            start_index = -1
            
            for i, token in enumerate(doc):
                if token.lemma_ in trigger_lemmas:
                    start_index = i
                    break
            
            if start_index != -1:
                logging.debug(f"NLU - Found trigger '{doc[start_index].lemma_}' at index {start_index}")
                potential_target = None
                
                for i in range(start_index + 1, len(doc)):
                    token = doc[i]
                    token_text = token.text.strip()
                    
                    
                    if token.is_punct or token.is_stop or token.lemma_ in prepositions:
                        continue

                    
                    ip_match = ip_pattern.match(token_text)
                    if ip_match:
                        potential_target = token_text
                        logging.info(f"NLU - Found potential target (IP): {potential_target} at index {i}")
                        break 

                    
                    
                    if '.' in token_text and not token.like_num and not token_text.replace('.', '').isdigit():
                         
                         if len(token_text) > 1 and token_text.count('.') >= 1:
                            potential_target = token_text
                            logging.info(f"NLU - Found potential target (Domain): {potential_target} at index {i}")
                            break 
                            
                    
                    
                    
                            
                
                if potential_target:
                    entities['target_address'] = potential_target
                    logging.info(f"NLU - Extracted target_address: {potential_target}")
                else:
                    logging.warning(f"NLU - Could not find a likely IP or domain target after trigger word '{doc[start_index].lemma_}'.")
            else:
                 logging.debug("NLU - Trigger word for nmap/whois not found.")

        return entities


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dummy_config = {'spacy_model': 'en_core_web_sm'}
    
    
    try:
        
        nlu_processor = NLUProcessor(dummy_config)
        if nlu_processor.nlp: 
            text1 = "Schedule a meeting with Bob for next Tuesday at 3 PM."
            result1 = nlu_processor.process(text1)
            print(f"Input Text: {text1}")
            print(f"NLU Result: {result1}")

            text2 = "Send an email to alice@example.com about the project update."
            result2 = nlu_processor.process(text2)
            print(f"\nInput Text: {text2}")
            print(f"NLU Result: {result2}")

            text3 = "nmap scan on 192.168.1.1"
            result3 = nlu_processor.process(text3)
            print(f"\nInput Text: {text3}")
            print(f"NLU Result: {result3}")

            text4 = "whois google.com"
            result4 = nlu_processor.process(text4)
            print(f"\nInput Text: {text4}")
            print(f"NLU Result: {result4}")

            text5 = "run nmap against 8.8.8.8"
            result5 = nlu_processor.process(text5)
            print(f"\nInput Text: {text5}")
            print(f"NLU Result: {result5}")

            text6 = "perform whois lookup for example.org please"
            result6 = nlu_processor.process(text6)
            print(f"\nInput Text: {text6}")
            print(f"NLU Result: {result6}")

        else:
            print("NLU model could not be loaded. Skipping example.")
    except Exception as e:
        print(f"Could not run NLU example: {e}")