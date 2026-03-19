from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.patterns import WORD_BOUNDARY_U_WORD_BOUNDARY

class CourtAnonymizer(BaseAnonymizer):
    """
    Anonymizer for Serbian courts and institutions. 
    It preserves the institutional title but anonymizes the city/location.
    """
    def _anonymize_entity(self, entity: Entity) -> str:
        # Check if the text contains the preposition 'u' (e.g., 'Viši sud u Nišu')
        if not WORD_BOUNDARY_U_WORD_BOUNDARY.search(entity.original_text):
            # If no 'u' is found, we don't have a clear location split; return as-is
            return entity.original_text
            
        # 1. Split the entity into the institutional prefix and the location tokens
        prefix, top_df = self._split_by_preposition_u(entity.rows)
        
        # 2. Anonymize only the location part (the 'Toponym')
        anonymized_top = self._anonymize_top(top_df, entity.doc_id)
        
        # 3. Combine: 'Osnovni sud u' + 'Kruševcu'
        return f"{prefix.strip()} {anonymized_top.strip()}"
    
    def _split_by_preposition_u(self, rows: list[dict]):
        """
        Locates the first occurrence of the preposition 'u' with a Locative MSD ('Sl').
        Everything after this 'u' is considered the location to be changed.
        """
        cut_off_idx = -1
        
        for i, row in enumerate(rows):
            # We look for the literal 'u' tagged as a preposition (Sl)
            if row['token'].lower() == 'u' and row['msd'].startswith('Sl'):
                cut_off_idx = i
                break

        if cut_off_idx != -1:
            # Slicing: Include the preposition 'u' in the prefix
            before_rows = rows[:cut_off_idx + 1]
            before_text = " ".join(str(r['token']) for r in before_rows)
            
            # The remaining rows are the toponym (e.g., 'Beogradu')
            after_rows = rows[cut_off_idx + 1:]
            
            return before_text, after_rows
            
        # Fallback if the grammar search fails
        return "", rows
    
    def _anonymize_top(self, rows: list[dict], doc_id: str) -> str:
        """
        Anonymizes the location part while preserving the correct Serbian case.
        """
        # 1. Join lemmas for seeding to ensure 'Beogradu' and 'Beograda' produce the same fake city
        full_lemma = " ".join(str(r["lemma"]).lower() for r in rows)
        
        # 2. Find the first Proper Noun (Np) to extract the target MSD (case/gender/number)
        # This ensures if the original was Dative/Locative, the fake replacement is too.
        target_row = next((r for r in rows if str(r.get("msd", "")).startswith("Np")), None)
        
        if target_row:
            target_msd = target_row["msd"]
        else:
            # Fallback to the first row's grammar if no Proper Noun is explicitly tagged
            target_msd = rows[0]["msd"]
            
        # 3. Create a stable seed for consistent replacement across the document
        seed_string = f"{full_lemma}{doc_id}{self.timestamp}"
        self.rng.seed(seed_string)
        
        # 4. Generate the new token from the municipality pool using the morphological lexicon
        anonymized_entity = self.lex.anonymize_municipality(target_msd, self.rng)
        entries = self.data_manager.adr_mapping[doc_id]
        current_lemma = full_lemma
        found_fake = None
        for entry in entries:
            if current_lemma == entry['orig_muni']:
                found_fake = entry['fake_muni']
                break
            elif current_lemma == entry['orig_city']:
                found_fake = entry['fake_city']
                break

        if found_fake:
            anonymized_entity = self.lex.get_wordform(found_fake, target_msd)
        
        # Return as Title Case (e.g., 'Čačku')
        return anonymized_entity.title()
