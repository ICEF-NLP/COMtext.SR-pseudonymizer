from typing import Any, List

from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.patterns import (
    ABBR_J_P_DOT_SPACE_OPTIONAL,
    CORPORATE_STRIP_PUNCTUATION_AND_QUOTES,
    EXACT_COMPANY_SUFFIX_OR_PREPOSITION,
    WHITESPACE_SEQUENCE,
)

class _BaseCorporateAnonymizer(BaseAnonymizer):
    """Internal base class to handle shared logic for ORG and COM."""
    
    def _base_anonymize(self, list_of_entities: List[Entity], generic_terms: set[str], random_func: Any) -> List[Entity]:
        """
        Coordinates the full pipeline: Preprocess (link mentions) -> Seed -> Anonymize.
        """
        # 1. First pass: Identify which entities are the same and assign matching seeds
        list_of_entities = self._preprocess_list(list_of_entities, generic_terms)
        
        for entity in list_of_entities:
            # Check if it's just a generic word (e.g., "Društvo") with no specific name
            if self._is_generic_legal_term(entity.rows, generic_terms):
                # Don't anonymize generic legal terms that lack a proper name
                entity.anonymized_text = entity.original_text
            else:
                # Use the calculated seed to ensure "Apple" always becomes "Orange" in this doc
                self.rng.seed(entity.get_seed_string(entity.seed.lower(), self.timestamp))
                entity.anonymized_text = random_func(self.rng)
            
            # Finalize the entity (strips whitespace, etc.)
            entity.clean_up()
        return list_of_entities
    
    def _preprocess_list(self, list_of_entities: List[Entity], generic_terms: set[str]):
        """
        Groups different mentions of the same company (e.g., 'Hemofarm' and 'Hemofarm AD').
        """
        for entity in list_of_entities:
            # Ignore purely generic terms during the seeding process
            if self._is_generic_legal_term(entity.rows, generic_terms):
                entity.seed, entity.original_lemma = "", "INVALID"
                continue
            
            # Extract and normalize the corporate name from lemmas
            text = self._concat_lemmas(entity.rows)
            # Normalize 'J.P.' or 'Javno Preduzeće' to 'jp' for better matching
            text = ABBR_J_P_DOT_SPACE_OPTIONAL.sub('jp', text.lower())
            text = text.replace('.', '').replace('javni preduzeće', 'jp')
            entity.original_lemma = WHITESPACE_SEQUENCE.sub(' ', text).strip()

        # SORT BY LENGTH: This is critical. We want to find the shortest version of the 
        # name first (the "Base") so longer versions can be matched against it.
        list_of_entities.sort(key=lambda x: len(x.original_lemma) or 1000)

        compare_list = []
        for entity in list_of_entities:
            if entity.original_lemma == "INVALID":
                continue
            
            current_name = entity.original_lemma
            # Check if this name contains a previously seen (shorter) name as a subsequence
            found_match = next((base for base in compare_list 
                               if self._is_sub_sequence(base, current_name)), None)
            
            if found_match:
                # Link this mention to the existing seed
                entity.seed = found_match
            else:
                # This is a new unique company in the document
                entity.seed = current_name
                compare_list.append(current_name)
                
        return list_of_entities
    
    def _is_generic_legal_term(self, rows, generic_terms: set[str]) -> bool:
        """Determines if the entity is a lone generic word (e.g., 'Ogranak')."""
        if rows and len(rows) == 1:
            return rows[0]["lemma"] in generic_terms
        return False

    def _concat_lemmas(self, rows) -> str:
        """
        Joins lemmas into a string, stopping before legal suffixes (DOO, AD, etc.).
        This ensures 'Hemofarm DOO' becomes just 'hemofarm' for seeding.
        """
        final_lemmas = []
    
        for row in rows:
            l = str(row['lemma'])
            # Remove quotes and punctuation from the lemma
            l_clean = CORPORATE_STRIP_PUNCTUATION_AND_QUOTES.sub('', l).lower()
            
            # Stop if we hit a suffix (DOO, AD) or a preposition (za, o)
            if EXACT_COMPANY_SUFFIX_OR_PREPOSITION.match(l_clean):
                break 
                
            final_lemmas.append(l_clean)
            
        return " ".join(final_lemmas)

    def _is_sub_sequence(self, small_phrase: str, large_phrase: str) -> bool:
        """
        Checks if the words in small_phrase appear in the exact same order 
        inside large_phrase. (e.g., 'Novi Sad' is a sub-sequence of 'Grad Novi Sad').
        """
        small = small_phrase.split()
        large = large_phrase.split()
        n, m = len(small), len(large)

        if n == 0: return True  
        if n > m: return False
        
        # Sliding window comparison
        for i in range(m - n + 1):
            if large[i] == small[0]:
                match = True
                for j in range(1, n):
                    if large[i + j] != small[j]:
                        match = False
                        break
                if match:
                    return True
        return False