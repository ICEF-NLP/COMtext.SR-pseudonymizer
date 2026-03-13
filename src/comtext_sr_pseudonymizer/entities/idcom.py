from typing import List

from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity

# Legally mandated length for Serbian Matični Broj (MB)
IDCOM_DIGITS = 8

class CompanyIDAnonymizer(BaseAnonymizer):
    """
    Anonymizes Serbian Company Registration Numbers (Matični Broj).
    
    This class uses a DataManager to perform context-aware substitution. 
    It identifies whether an ID belongs to a commercial company or an NGO 
    to ensure the anonymized data maintains the same entity type.
    """

    def anonymize(self, list_of_entities: List[Entity]) -> List[Entity]:
        """
        Public entry point for processing a batch of ID entities.
        Includes a validation check for the Serbian 8-digit standard.
        """
        for entity in list_of_entities:
            # VALIDATION: Serbian MB must be exactly 8 digits.
            if len(entity.original_text) != IDCOM_DIGITS:
                # If the ID is malformed, we log an error and leave it alone to avoid 
                # introducing corrupted data into the document.
                print(f"IDCOM number {entity.original_text} is incorrect. Must have {IDCOM_DIGITS} digits")
                entity.anonymized_text = entity.original_text
            else:
                # Apply the specific anonymization strategy
                entity.anonymized_text = self._anonymize_entity(entity)
            
            # Standard memory cleanup (drops rows/metadata)
            entity.clean_up()
        return list_of_entities

    def _anonymize_entity(self, entity: Entity) -> str:
        """
        Determines the entity type and retrieves a corresponding random 
        ID from the DataManager pool.
        """
        # SEEDING: We seed based on the original ID + doc_id + timestamp.
        # This ensures that if MB '01234567' appears multiple times, it 
        # is always replaced by the same fake MB in this document.
        self.rng.seed(entity.get_seed_string(entity.original_text, self.timestamp))
        
        # TYPE PRESERVATION: We check the DataManager's internal sets/databases
        # to see if the ID belongs to a 'Privredno društvo' (COM) or an 'Udruženje' (NGO).
        
        # 1. Check if the entity is a Commercial Company
        if self.data_manager.is_id_com(entity.original_text):
            anonymized_idcom = self.data_manager.get_random_id_com(self.rng)
            
        # 2. Check if the entity is a Non-Governmental Organization (NGO)
        elif self.data_manager.is_id_ngo(entity.original_text):
            anonymized_idcom = self.data_manager.get_random_id_ngo(self.rng)
            
        # 3. FALLBACK: If the ID isn't in our known database
        else:
            # We use a weighted random choice to pick a replacement type 
            # so the fake ID at least looks like a valid Serbian MB.
            entity_type_choice = self.rng.choice(["ngo", "com"])
            
            if entity_type_choice == "ngo":
                anonymized_idcom = self.data_manager.get_random_id_ngo(self.rng)
            else:
                anonymized_idcom = self.data_manager.get_random_id_com(self.rng)
                
        return anonymized_idcom