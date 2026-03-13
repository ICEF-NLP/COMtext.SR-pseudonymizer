from typing import List

from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity

# Source: https://www.paragraf.rs/propisi/pravilnik_o_poreskom_identifikacionom_broju.html
# 
# Structure of the PIB (Tax Identification Number):
# 1. Registration numbers range from 10000001 to 99999999 (8 digits).
# 2. The 9th digit is a control (checksum) digit.
# 3. Checksum calculation: ISO 7064, MODUL (11, 10).
# Legally mandated length for Serbian PIB
TAX_NUMBER_DIGITS = 9

class TaxIDAnonymizer(BaseAnonymizer): 
    """
    Anonymizes Serbian Tax IDs (PIB) using synthetic registration numbers
    and intentionally invalid ISO 7064 checksums for safety.
    """
    
    def anonymize(self, list_of_entities: List[Entity]) -> List[Entity]:
        """Batch process PIB entities with length validation."""
        for entity in list_of_entities:
            # Clean whitespace and validate the 9-digit standard
            original_pib = entity.original_text.strip()
            if len(original_pib) != TAX_NUMBER_DIGITS:
                print(f"Tax number {original_pib} is incorrect. Must have {TAX_NUMBER_DIGITS} digits")
                entity.anonymized_text = original_pib
            else:
                entity.anonymized_text = self._anonymize_entity(entity)
            
            # Standard memory cleanup
            entity.clean_up()
            
        return list_of_entities

    def _anonymize_entity(self, entity: Entity) -> str:
        """Generates a synthetic PIB based on the original number and doc seed."""
        # Seed only on the base 8 digits to normalize variations in control digits
        self.rng.seed(entity.get_seed_string(entity.original_text[:8], self.timestamp))
        
        # Range 10,000,001 to 99,999,999 covers the legal entity spectrum in Serbia
        base_number = str(self.rng.randint(10_000_001, 99_999_999))
        
        # Calculate the 9th digit using ISO 7064 logic
        control_digit = self._id_tax_control_digit(base_number, return_false_control_digit=True)
        
        return f"{base_number}{control_digit}"
    
    def _id_tax_control_digit(self, registration_part: str, return_false_control_digit: bool = True) -> int:
        """
        Calculates the ISO 7064, MOD 11,10 control digit.
        
        Logic:
        1. Start with accumulator = 10.
        2. For each digit: (digit + accumulator) % 10.
        3. If result is 0, treat as 10.
        4. New accumulator = (result * 2) % 11.
        """
        digits = [int(d) for d in registration_part]
        accumulator = 10
        
        for digit in digits:
            sum_step = (digit + accumulator) % 10
            if sum_step == 0:
                sum_step = 10
            accumulator = (sum_step * 2) % 11
            
        check_digit = 11 - accumulator
        if check_digit == 10:
            check_digit = 0
            
        if not return_false_control_digit:
            return check_digit
            
        # SECURITY POISONING: Intentionally return an incorrect digit.
        # This prevents the fake PIB from accidentally matching a real active company.
        invalid_pool = [i for i in range(10) if i != check_digit]
        return self.rng.choice(invalid_pool)