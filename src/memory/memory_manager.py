import logging

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime 
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

Base = declarative_base() 


class LongTermMemory(Base):
    __tablename__ = 'long_term_memory'
    id = Column(Integer, primary_key=True)
    category = Column(String, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MemoryManager:
    def __init__(self, memory_config):
        self.config = memory_config
        self.short_term_memory = [] 
        self.db_connection = None
        self.db_session = None 
        self._connect_db()

    def _connect_db(self):
        
        db_type = self.config.get('database_type', 'sqlite')
        logging.info(f"Connecting to {db_type} database...")
        try:
            if db_type == 'sqlite':
                db_path = self.config.get('database_path', 'mobius_memory.db')
                
                engine = create_engine(f'sqlite:///{db_path}') 
                Base.metadata.create_all(engine) 
                Session = sessionmaker(bind=engine)
                self.db_session = Session()
                self.db_connection = engine 
                logging.info(f"Connected to SQLite database: {db_path}")
            
            
            
            
            
            
            
            
            
            
            
            
            
            else:
                logging.error(f"Unsupported database type: {db_type}")
                raise ValueError(f"Unsupported database type: {db_type}")
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}", exc_info=True)
            
            self.db_connection = None
            self.db_session = None

    def add_short_term(self, user_input, assistant_response):
        
        turn = {'user': user_input, 'assistant': assistant_response}
        self.short_term_memory.append(turn)
        
        limit = self.config.get('short_term_limit', 10)
        if len(self.short_term_memory) > limit:
            self.short_term_memory.pop(0)
        logging.debug(f"Added to short-term memory. Current size: {len(self.short_term_memory)}")

    def get_short_term_context(self):
        
        return self.short_term_memory

    def save_long_term(self, category, key, value):
        
        if not self.db_session:
            logging.error("Database session not available. Cannot save long-term memory.")
            return False
        logging.debug(f"Saving to long-term memory: Category='{category}', Key='{key}'")
        try:
            
            existing_memory = self.db_session.query(LongTermMemory).filter_by(key=key).first()
            if existing_memory:
                existing_memory.value = value
                existing_memory.category = category
                
            else:
                new_memory = LongTermMemory(category=category, key=key, value=value)
                self.db_session.add(new_memory)
            self.db_session.commit()
            logging.info(f"Saved/Updated long-term memory: {category}/{key}")
            return True
        except Exception as e:
            logging.error(f"Error saving to long-term memory: {e}", exc_info=True)
            if self.db_session: self.db_session.rollback() 
            return False

    def retrieve_long_term(self, key):
        
        if not self.db_session:
            logging.error("Database session not available. Cannot retrieve long-term memory.")
            return None
        logging.debug(f"Retrieving from long-term memory: Key='{key}'")
        try:
            
            memory_item = self.db_session.query(LongTermMemory).filter_by(key=key).first()
            if memory_item:
                
                
                
                
                logging.info(f"Retrieved long-term memory for key: {key}")
                return {'category': memory_item.category, 'value': memory_item.value, 'last_accessed': memory_item.last_accessed_at}
            else:
                logging.info(f"No long-term memory found for key: {key}")
                return None
        except Exception as e:
            logging.error(f"Error retrieving from long-term memory: {e}", exc_info=True)
            return None

    def prune_old_memory(self):
        
        if not self.db_session:
            logging.warning("Database session not available. Cannot prune memory.")
            return
        
        pruning_days = self.config.get('long_term_pruning_days', 180)
        if pruning_days <= 0:
            logging.info("Long-term memory pruning is disabled (pruning_days <= 0).")
            return

        cutoff_date = datetime.utcnow() - timedelta(days=pruning_days)
        logging.info(f"Pruning long-term memory last accessed before {cutoff_date}...")
        try:
            
            deleted_count = self.db_session.query(LongTermMemory)\
                .filter(LongTermMemory.last_accessed_at < cutoff_date)\
                .delete(synchronize_session=False) 
            self.db_session.commit()
            logging.info(f"Pruned {deleted_count} old memory entries.")
        except Exception as e:
            logging.error(f"Error pruning long-term memory: {e}", exc_info=True)
            if self.db_session: self.db_session.rollback()

    def close(self):
        
        if self.db_session:
            try:
                self.db_session.close()
                logging.info("Database session closed.")
            except Exception as e:
                logging.error(f"Error closing database session: {e}", exc_info=True)
        
        if self.db_connection and hasattr(self.db_connection, 'dispose'):
             try:
                self.db_connection.dispose()
                logging.info("Database connection pool disposed.")
             except Exception as e:
                 logging.error(f"Error disposing database connection pool: {e}", exc_info=True)
        self.db_connection = None
        self.db_session = None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dummy_config = {
        'database_type': 'sqlite',
        'database_path': ':memory:', 
        'short_term_limit': 5,
        'long_term_pruning_days': 30
    }

    try:
        
        memory = MemoryManager(dummy_config)
        
        if memory.db_session: 
            
            memory.add_short_term("Hello", "Hi there!")
            memory.add_short_term("How are you?", "I'm doing well, thanks!")
            print("Short-term context:", memory.get_short_term_context())

            
            print("\n--- Long-Term Memory Test ---")
            save_ok = memory.save_long_term('preference', 'favorite_color', 'blue')
            print(f"Save successful: {save_ok}")
            save_ok_2 = memory.save_long_term('fact', 'capital_france', 'Paris')
            print(f"Save successful: {save_ok_2}")
            
            retrieved = memory.retrieve_long_term('favorite_color')
            print("Retrieved 'favorite_color':", retrieved)
            retrieved_nonexistent = memory.retrieve_long_term('nonexistent_key')
            print("Retrieved 'nonexistent_key':", retrieved_nonexistent)

            
            update_ok = memory.save_long_term('preference', 'favorite_color', 'green')
            print(f"Update successful: {update_ok}")
            retrieved_updated = memory.retrieve_long_term('favorite_color')
            print("Retrieved updated 'favorite_color':", retrieved_updated)

            
            print("\n--- Pruning Test ---")
            memory.prune_old_memory()
            
            memory.close()
            print("\nMemory manager closed.")
        else:
            print("Database session not initialized. Skipping tests.")
            
    except Exception as e:
        print(f"Could not run memory manager example: {e}")