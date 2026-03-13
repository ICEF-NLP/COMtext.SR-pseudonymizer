from typing import List

from comtext_sr_pseudonymizer.entities.corporate_base import _BaseCorporateAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity

class OtherOrgAnonymizer(_BaseCorporateAnonymizer):
    """
    Anonymizes miscellaneous legal entities that are not standard corporations.
    
    This specifically targets entities like trade unions (sindikat) or 
    societies (društvo) that don't fall under the standard 'Company' category.
    """
    
    def anonymize(self, list_of_entites: List[Entity]) -> List[Entity]:
        """
        Executes the base corporate anonymization logic with NGO-specific parameters.
        """
        # We pass three things to the base logic:
        # 1. The list of Entity objects to process.
        # 2. A set of lowercase keywords that identify this organization type 
        #    (including support for both Latin and Cyrillic/diacritic variations).
        # 3. The specific DataManager method used to pull a fake NGO name.
        return self._base_anonymize(
            list_of_entites, 
            {"drustvo", "društvo", "sindikat"}, 
            self.data_manager.get_random_ngo
        )