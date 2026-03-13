import random

from comtext_sr_pseudonymizer.constants import STATEHOOD_INDICATORS
from comtext_sr_pseudonymizer.data_manager import DataManager
from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.lex import Lex

class ToponymAnonymizer(BaseAnonymizer):
    """Handles the anonymization of geographic locations (countries, cities, municipalities)."""

    def __init__(self, timestamp: str, rng: random.Random, data_manager: DataManager, lex: Lex) -> None:
        super().__init__(timestamp, rng, data_manager, lex)
        # Strategy mapping: links a category string to the specific Lexicon method
        self._anonymizers = {
            "city": lex.anonymize_city,
            "country": lex.anonymize_country,
            "municipality": lex.anonymize_municipality
        }
        self._categories = list(self._anonymizers.keys())

    def _anonymize_entity(self, entity: Entity) -> str:
        """Determines the toponym category and returns the declined replacement string."""
        rows = entity.rows
        
        # 1. LEMMA NORMALIZATION:
        # We join all tokens' lemmas to handle multi-word locations like 'Ujedinjeno Kraljevstvo'
        # or 'Sremska Mitrovica' during DataManager lookup.
        full_lemma = " ".join(str(r["lemma"]).lower() for r in rows)
        
        # 2. MSD EXTRACTION:
        # We look for the first Proper Noun (Np) in the sequence to determine the correct
        # grammatical case for the entire location. If none found, fallback to the first word.
        target_row = next((r for r in rows if str(r.get("msd", "")).startswith("Np")), None)
        if target_row:
            target_msd = target_row["msd"]
        else:
            target_msd = rows[0]["msd"]

        # 3. DETERMINISTIC SEEDING:
        # Ensures that 'Srbija' always maps to the same replacement (e.g., 'Francuska')
        # throughout the same document run.
        self.rng.seed(entity.get_seed_string(full_lemma, self.timestamp))
        
        # 4. CATEGORIZATION LOGIC:
        # Priorities: Countries/Statehood first, then Cities, then Municipalities.
        
        # Check for explicit country names or statehood indicators (e.g., 'republika', 'federacija')
        if self.data_manager.is_country(full_lemma) or any(t in full_lemma for t in STATEHOOD_INDICATORS):
            category = "country"
        # Check if the location is identified as a city in our database
        elif self.data_manager.is_city(full_lemma):
            category = "city"
        # Check if the location is identified as a municipality (opština)
        elif self.data_manager.is_municipality(full_lemma):
            category = "municipality"
        # FALLBACK: If unknown, pick a random category to ensure it stays a toponym
        else:
            category = self.rng.choice(self._categories)

        # 5. EXECUTION:
        # Call the mapped Lexicon function with the extracted MSD to get a grammatically correct fake name.
        anonymized_entity = self._anonymizers[category](target_msd, self.rng)
        
        # Ensure 'Beograd' -> 'Kragujevac' (Proper Noun casing)
        return anonymized_entity.title()