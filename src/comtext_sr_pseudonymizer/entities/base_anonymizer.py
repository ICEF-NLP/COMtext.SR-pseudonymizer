import random
from typing import List

from comtext_sr_pseudonymizer.data_manager import DataManager
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.lex import Lex

class BaseAnonymizer:
    """
    Abstract base class providing a consistent interface for all anonymization types.
    Ensures that every entity follows the same lifecycle: Anonymize -> Clean Up.
    """
    def __init__(self, timestamp: str, rng: random.Random, data_manager: DataManager=None, lex: Lex=None):
        # Global session identifier to ensure consistent seeding across different runs
        self.timestamp = timestamp
        # The primary Random number generator passed from the main controller
        self.rng = rng
        # Access to the data pools (streets, names, cities)
        self.data_manager = data_manager
        # Access to the morphological lexicon for Serbian grammar (cases/MSD)
        self.lex = lex

    def anonymize(self, list_of_entities: List[Entity]) -> List[Entity]: 
        """
        Public method to process a batch of entities. 
        Iterates through detected entities, applies logic, and finalizes the object.
        """
        for entity in list_of_entities:
            # 1. Generate the fake text using the subclass-specific strategy
            entity.anonymized_text = self._anonymize_entity(entity)
            # 2. Perform post-processing (e.g., stripping whitespace, finalizing labels)
            entity.clean_up()
            
        return list_of_entities
    
    def _anonymize_entity(self, entity: Entity) -> str:
        """
        Abstract method. 
        This MUST be overridden by classes like AddressAnonymizer or PersonAnonymizer.
        """
        # This is a safeguard to prevent developers from calling the base class directly
        raise NotImplementedError("Subclasses must implement _anonymize_entity")