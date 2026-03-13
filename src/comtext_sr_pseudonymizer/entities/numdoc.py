from typing import List

from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
class DocumentNumberAnonymizer(BaseAnonymizer):
    """
    Anonymizes ID Card (LK) and Passport (PASS) numbers.
    Follows Serbian and ICAO standards (exactly 9 digits).
    """
    
    # References for Document Structure:
    # 1. Identity Card (LK) MRZ: https://pravno-informacioni-sistem.rs/eli/rep/sgrs/ministarstva/pravilnik/2007/11/1/reg
    #    Registration number occupies positions 6–14 (9 characters).
    # 2. Passport (PASS) ICAO 9303: https://crl.mup.gov.rs/CSCA.html 
    #    Standard allows up to 9, but Serbian passports are exactly 9 digits.
    LEN_NUMDOC: int = 9

    def anonymize(self, list_of_entities: List[Entity]) -> List[Entity]:
        """Processes a list of document numbers and applies 9-digit z-filled anonymization."""
        for entity in list_of_entities:
            if len(entity.original_text) != self.LEN_NUMDOC:
                print(f"WARNING: NUMDOC {entity.original_text} is invalid. Expected exactly {self.LEN_NUMDOC} digits.")
                entity.anonymized_text = entity.original_text
            else:
                self.rng.seed(entity.get_seed_string(entity.original_text, self.timestamp))
                new_val = self.rng.randint(1_000_000, 999_999_999)
                entity.anonymized_text = str(new_val).zfill(self.LEN_NUMDOC)
            entity.clean_up()
        return list_of_entities    