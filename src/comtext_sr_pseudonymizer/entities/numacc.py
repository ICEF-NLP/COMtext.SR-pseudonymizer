from typing import List, Tuple, Optional

from comtext_sr_pseudonymizer.constants import SERBIAN_BANK_CODES
from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity

# References for Account Structure:
# 1. Checksum page 3: https://www.nbs.rs/export/sites/NBS_site/documents-eng/propisi/propisi-ps/form_contents_instruments_elements.pdf
# 2. Bank idenfication codes: https://www.nbs.rs/export/sites/NBS_site/documents-eng/platni-sistem/banks_account_numbers.pdf

# NBS Standard Account Structure:
# - First 3 digits: Bank identification code
# - Next 13 digits: Unique account number
# - Last 2 digits: Control number (Checksum) mod 97
LEN_NUMACC_TOTAL = 20
LEN_NUMACC_FIRST = 3
LEN_NUMACC_SECOND = 13
LEN_NUMACC_THIRD = 2

class AccountNumberAnonymizer(BaseAnonymizer):
    """
    Anonymizes Serbian bank account numbers while maintaining the NBS standard structure.
    
    The class validates the input format, randomizes the bank and account sections,
    and calculates a MOD 97 checksum (intentionally invalid by default for safety).
    """

    def __init__(self, timestamp: str, rng) -> None:
        super().__init__(timestamp, rng)
        self.active_codes = list(SERBIAN_BANK_CODES["active"].keys())

    def anonymize(self, list_of_entities: List[Entity]) -> List[Entity]:
        """Processes a list of account dictionaries and adds anonymized text."""
        for entity in list_of_entities:
            entity.original_text, valid = self._validation_check(entity.original_text.strip())
            if not valid or entity.original_text is None:
                # Keep original text if validation fails
                entity.anonymized_text = entity.original_text
            else:
                entity.anonymized_text = self._anonymize_entity(entity)
            entity.clean_up()
        return list_of_entities

    def _anonymize_entity(self, entity: Entity) -> str:
        """Generates a synthetic bank account string using a stable seed."""
        self.rng.seed(entity.get_seed_string(entity.original_text, self.timestamp))
        
        # Determine the bank code (ensuring we rotate to a different active bank)
        first_part = entity.original_text.split("-")[0]
        first_part = self.rng.choice(self.active_codes)
            
        second_part = str(self.rng.randint(0, 9_999_999_999_999)).zfill(LEN_NUMACC_SECOND)
        
        # Generate the checksum segment
        third_part = self._generate_control_digit(first_part, second_part, false_control=True)
        
        return f"{first_part}-{second_part}-{third_part}"

    def _generate_control_digit(self, first: str, second: str, false_control: bool = True) -> str:
        """Calculates the MOD 97 checksum according to the ISO 7064 standard."""
        # Convert concatenated parts to integer for remainder calculation
        number = int(f"{first}{second}00")
        remainder = number % 97
        check_digit = 98 - remainder
        
        if not false_control:
            return str(check_digit).zfill(LEN_NUMACC_THIRD)
            
        # Shift the checksum by a random amount [1-96] to ensure it is invalid
        invalid_check_int = (check_digit + self.rng.randint(1, 96)) % 97
        if invalid_check_int == 0:
            invalid_check_int = 97
            
        return str(invalid_check_int).zfill(LEN_NUMACC_THIRD)

    def _validation_check(self, numacc: str) -> Tuple[Optional[str], bool]:
        """Validates the input string against NBS account formatting rules."""

        if len(numacc) > LEN_NUMACC_TOTAL:
            print(f"NUMACC number {numacc} is invalid. Must be at most {LEN_NUMACC_TOTAL} length")
            return numacc, False
            
        numacc_parts = numacc.split("-")
        if len(numacc_parts) != 3:
            print(f"NUMACC number {numacc} is invalid. There must always be only 2 - characters")
            return numacc, False 
            
        if len(numacc_parts[0]) != LEN_NUMACC_FIRST:
            print(f"NUMACC number {numacc} is invalid. First part must be {LEN_NUMACC_FIRST} digits")
            return numacc, False
            
        if len(numacc_parts[1]) > LEN_NUMACC_SECOND:
            print(f"NUMACC number {numacc} is invalid. Second part must be at most {LEN_NUMACC_SECOND} digits")
            return numacc, False
            
        if len(numacc_parts[2]) > LEN_NUMACC_THIRD:
            print(f"NUMACC number {numacc} is invalid. Third part must be at most {LEN_NUMACC_THIRD} digits")
            return numacc, False

        # If it's already full length, return as is
        if len(numacc) == LEN_NUMACC_TOTAL:
            return numacc, True
            
        # Otherwise, normalize the segments (z-fill)
        first_part = numacc_parts[0]
        second_part = numacc_parts[1].zfill(LEN_NUMACC_SECOND)
        third_part = numacc_parts[2].zfill(LEN_NUMACC_THIRD)
        
        # Verify that all segments contain only digits to avoid ValueError later
        if not (first_part.isdigit() and second_part.isdigit() and third_part.isdigit()):
            print(f"NUMACC number {numacc} contains non-digit characters")
            return None, False
            
        return f"{first_part}-{second_part}-{third_part}", True