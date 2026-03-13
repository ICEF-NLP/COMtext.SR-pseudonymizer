from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class Entity:
    """
    The primary data container for a detected entity (Name, Address, Date, etc.).
    It tracks the entity from detection through grammar analysis to final replacement.
    """
    doc_id: str             # Unique ID of the source document (used for seeding)
    sentence_id: str        # ID of the specific sentence within the document
    start_token_num: int    # Starting index in the original token stream
    end_token_num: int      # Ending index in the original token stream
    original_text: str      # The raw text as it appeared in the document
    entity_group: str       # The type (e.g., 'PER', 'LOC', 'ORG', 'ADR')
    
    # rows: A list of dicts containing [token_id, token, lemma, msd]
    # This provides the morphological context needed for Serbian cases.
    rows: Optional[List[Dict[str, str]]] = None 
    
    anonymized_text: Optional[str] = None # The final "fake" version of the text
    
    # Internal processing fields
    seed: Optional[str] = None           # Shared seed for linked entities (e.g., 'Hemofarm')
    original_lemma: Optional[str] = None # Normalized version used for matching

    def get_seed_string(self, entity_seed: str, time_seed: str) -> str:
        """
        Generates a deterministic string to seed the Random Number Generator.
        Combines the entity name, document ID, and session timestamp to ensure:
        1. Consistency within the same document.
        2. Randomness across different documents.
        """
        base = self.seed if self.seed else entity_seed
        return f"{base.lower()}{self.doc_id}{time_seed}"

    def clean_up(self):
        """
        Standardized memory management.
        Crucial for processing large batches: drops the heavy 'rows' (the morphological data)
        once the anonymized_text is generated, keeping the object lightweight.
        """
        self.rows = None
        self.seed = None
        self.original_lemma = None