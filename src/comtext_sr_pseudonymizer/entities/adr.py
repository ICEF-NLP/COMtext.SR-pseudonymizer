import random
from typing import List

from comtext_sr_pseudonymizer.data_manager import DataManager
from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.entities.helpers import AddressComponent, AddressParser
from comtext_sr_pseudonymizer.lex import Lex

class AddressAnonymizer(BaseAnonymizer):
    def __init__(self, timestamp: str, rng: random.Random, data_manager: DataManager, lex: Lex):
        super().__init__(timestamp, rng, data_manager, lex)
        
        # Independent RNG for geographic elements to ensure city/zip/muni stay 
        # consistent even if street or house numbers change.
        self.city_rng = random.Random()

        # Initialize the parser with the provided data manager
        self.parser = AddressParser(data_manager, False)
        L = self.parser.get_label_for
        
        # Map labels from the AddressLexicon to specific anonymization methods
        self._strategy_map = {
            L("STREET"):         self._anon_street,
            L("HOUSE"):          self._anon_house,
            L("FLOOR"):          self._anon_floor,
            L("APARTMENT"):      self._anon_apt,
            L("ZIP"):            self._anon_zip,
            L("CITY"):           self._anon_city,
            L("MUNI"):           self._anon_muni,
            L("COUNTRY"):        self._anon_country,
            L("AREA"):           self._anon_area,
            L("SECTION"):        self._anon_section,
        }
    
    def _anonymize_entity(self, entity: Entity) -> str:
        """Main entry point for anonymizing a single address entity."""
        # Step 1: Parse the raw tokens into structured address groups
        grouped_parts = self.parser.parse(entity.rows)
        # Step 2: Apply anonymization logic to the structured parts
        anonymized = self._anonymize_grouped_parts(grouped_parts, entity.doc_id)

        # Step 3: Reconstruct the string from anonymized tokens
        tokens = [str(p.token) for p in anonymized]
        raw_string = " ".join(tokens)
        return raw_string

    def _anonymize_grouped_parts(self, grouped_parts: List[AddressComponent], doc_id: str):
        # --- 1. INITIAL SEED EXTRACTION ---
        # Cache labels for performance
        L_STREET = self.parser.get_label_for("STREET")
        L_HOUSE  = self.parser.get_label_for("HOUSE")
        L_CITY   = self.parser.get_label_for("CITY")
        L_MUNI   = self.parser.get_label_for("MUNI")
        L_ZIP    = self.parser.get_label_for("ZIP")

        street_val, house_val = "no_st", "no_h"
        city_val, muni_val = "", ""
        found_geo_labels = set()

        # Identify key anchor points in the original address to use for seeding
        for p in grouped_parts:
            if p.label == L_STREET: street_val = p.token
            elif p.label == L_HOUSE: house_val = p.token
            
            if p.label in {L_ZIP, L_MUNI, L_CITY}:
                if p.label == L_CITY: city_val = p.lemma.lower().strip()
                elif p.label == L_MUNI: muni_val = p.lemma.lower().strip()
                found_geo_labels.add(p.label)

        # --- 2. SEEDING & BUNDLING ---
        # Seed the main RNG with street+house info. This ensures the same street 
        # in the same document always gets the same fake name (Referential Integrity).
        self.rng.seed(f"{street_val}{house_val}{doc_id}{self.timestamp}")
        
        # Use a separate seed for Geo data so that the City/Zip/Muni triplet 
        # is determined by the original city, regardless of the street name.
        geo_seed_basis = city_val if city_val else muni_val
        self.city_rng.seed(f"{geo_seed_basis}{doc_id}{self.timestamp}")

        # BUNDLING: If we find at least two geo-parts (e.g., City + Zip), we fetch a 
        # valid real-world triplet to ensure the fake Zip actually exists in the fake City.
        city_bundle = None
        if len(found_geo_labels) >= 2:
            city_bundle = self.data_manager.get_random_city_zip_muni(self.city_rng)

        # State object to track internal building logic (incremental floors/unique apts)
        state = {
            "current_floor": self.rng.randint(1, 20),
            "used_apts": set(),
            "adr_map": {
                "orig_city": city_val, 
                "orig_muni": muni_val, 
                "fake_city": "", 
                "fake_muni": "" 
            }
        }

        # Step 3: Iterate through parts and apply the mapped strategy
        for comp in grouped_parts:
            method = self._strategy_map.get(comp.label)
            if method:
                # Mutate the token with the anonymized value
                comp.token = method(comp, city_bundle, state)
        
        if city_bundle:
            current_doc_mappings = self.data_manager.adr_mapping.get(doc_id, [])
            exists = any(
                m['orig_city'] == state['adr_map']['orig_city'] and 
                m['orig_muni'] == state['adr_map']['orig_muni'] 
                for m in current_doc_mappings
            )
            if not exists:
                self.data_manager.adr_mapping.setdefault(doc_id, []).append(state['adr_map'])
        return grouped_parts

    def _format_number(self, number, msd):
        """Helper to append dots to ordinal numbers based on MSD tags."""
        is_ordinal = any(msd.startswith(pre) for pre in ["Mrc", "Mlo", "Mdo"])
        if is_ordinal:
            return f"{number}."
        else:
            return f"{number}"
        
    # --- Residence Strategies ---

    def _anon_street(self, comp, bundle, state):
        """Generates a random street name from the pool."""
        fake_name = self.data_manager.get_random_street(self.rng)
        if comp.start_token == 1:
            full_street = f"Ul. {fake_name}"
        else:
            full_street = f"ul. {fake_name}"
        # Cleanup extra whitespace or commas
        return " ".join(full_street.replace(',', ' ,').split())

    def _anon_house(self, comp, bundle, state):
        """Generates a random house number."""
        number = self.rng.randint(1, 200)
        return self._format_number(number, comp.msd)

    def _anon_floor(self, comp, bundle, state):
        """Generates a floor number and increments for subsequent mentions."""
        val = self._format_number(state["current_floor"], comp.msd)
        state["current_floor"] += 1
        return val

    def _anon_apt(self, comp, bundle, state):
        """Generates a unique apartment number based on the floor."""
        new_apt = (state["current_floor"] * 7) + self.rng.randint(1, 7)
        while new_apt in state["used_apts"]: 
            new_apt += 1
        state["used_apts"].add(new_apt)
        return self._format_number(new_apt, comp.msd)

    # --- Geo/Locality Strategies ---

    def _anon_zip(self, comp, bundle, state):
        """Returns bundled ZIP if available, otherwise a random one."""
        if bundle:
            return str(bundle[1]) 
        return str(self.data_manager.get_random_zip(self.city_rng))

    def _anon_city(self, comp, bundle, state):
        """Returns bundled city with correct grammar (MSD) or a random one."""
        if bundle:
            city_lemma = bundle[0]
        else:
            city_lemma = self.lex.anonymize_city(comp.msd, self.city_rng, return_lemma=True)
        state['adr_map']['fake_city'] = city_lemma
        return self.lex.get_wordform(city_lemma, comp.msd)
    
    def _anon_muni(self, comp, bundle, state):
        """Returns bundled municipality with correct grammar or a random one."""
        if bundle:
            muni_lemma = bundle[2]
        else:
            muni_lemma = self.lex.anonymize_municipality(comp.msd, self.city_rng, return_lemma=True)
        state['adr_map']['fake_muni'] = muni_lemma
        return self.lex.get_wordform(muni_lemma, comp.msd)

    def _anon_country(self, comp, bundle, state):
        """Anonymizes country while maintaining correct case/MSD."""
        return self.lex.anonymize_country(comp.msd, self.rng)

    # --- Building Details ---

    def _anon_area(self, comp, bundle, state):
        """Generates a random square footage/area."""
        return str(self.rng.randint(30, 250))

    def _anon_section(self, comp, bundle, state):
        """Generates a random building section/entrance (A-F)."""
        return self.rng.choice(["A", "B", "C", "D", "E", "F"])