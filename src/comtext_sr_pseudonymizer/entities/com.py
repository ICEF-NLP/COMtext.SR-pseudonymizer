from typing import List

from comtext_sr_pseudonymizer.entities.corporate_base import _BaseCorporateAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity

class CompanyAnonymizer(_BaseCorporateAnonymizer):
    """
    Specialized anonymizer for Serbian corporate entities (DOO, AD, etc.).
    Inherits from _BaseCorporateAnonymizer to reuse shared parsing logic.
    """

    def anonymize(self, list_of_entites: List[Entity]) -> List[Entity]:
        """
        Executes the corporate anonymization pipeline.
        
        Passes the company-specific 'generic_terms' and the 'get_random_com' 
        data pool function to the shared _base_anonymize logic.
        """
        return self._base_anonymize(
            list_of_entites, 
            {"drustvo", "društvo", "ogranak"}, 
            self.data_manager.get_random_com  # The specific pool for company names
        )