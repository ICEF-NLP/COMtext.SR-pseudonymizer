from comtext_sr_pseudonymizer.constants import SERBIAN_ALPHABET
from comtext_sr_pseudonymizer.entities.base_anonymizer import BaseAnonymizer
from comtext_sr_pseudonymizer.entities.entity_schema import Entity

class PersonAnonymizer(BaseAnonymizer):
    """Handles the anonymization of personal names with morphological preservation."""

    def _anonymize_entity(self, entity: Entity) -> str:
        """Core logic to process individual name tokens within a person entity."""
        rows = entity.rows
        self._mark_noise(rows)

        first_name_found = False
        final_tokens = []
        for row in rows:
            if row.get("is_noise"):
                final_tokens.append(row["token"])
                continue

            msd: str = row.get("msd")
            lemma: str = row.get("lemma")

            # Use a stable seed for THIS specific token within THIS document
            # Seeding inside the loop ensures 'Petar' always becomes 'Marko' 
            # regardless of whether it's the first or second word.
            self.rng.seed(entity.get_seed_string(lemma.lower(), self.timestamp))
            
            new_val: str = ""
            # --- CATEGORIZATION LOGIC ---
            if msd.startswith("A"):
                print(f"    INFO: PER {row["token"]} is an adjective form, skipping")
                new_val = row["token"]
                
            elif msd.startswith("Y"):
                new_val = f"{self.rng.choice(SERBIAN_ALPHABET)}."
                
            elif self.data_manager.is_male_name(lemma):
                new_val = self.lex.anonymize_male_name(msd, self.rng)
                first_name_found = True
                
            elif self.data_manager.is_female_name(lemma):
                new_val = self.lex.anonymize_female_name(msd, self.rng)
                first_name_found = True
                
            elif self.data_manager.is_surname(lemma) or first_name_found:
                new_val = self.lex.anonymize_surname(msd, self.rng)   
            else:
                # Final Fallback: 50/50 gender guess
                choice: str = self.rng.choice(["m", "f"])
                if choice == "m":
                    new_val = self.lex.anonymize_male_name(msd, self.rng)
                else:
                    new_val = self.lex.anonymize_female_name(msd, self.rng)
                first_name_found = True
            # Apply Title Case to ensure proper name formatting
            final_tokens.append(new_val.title())
        return " ".join(final_tokens)

    def _mark_noise(self, rows: list[dict]) -> list[dict]:
        """Flags tokens that should not be anonymized by adding 'is_noise' key."""
        for row in rows:
            token_low = row["token"].lower()
            msd = row["msd"]
            
            # Condition 1: "rođ." / "rodj." / "rođena"
            is_rodj_marker = (
                (token_low.startswith("rođ") or token_low.startswith("rodj")) and 
                (msd == "Y" or msd.startswith("A"))
            )
            
            # Condition 2: Delimiter Commas, Hyphens
            is_punct = (row["token"] in [",", "-"]) and (msd == "Z")
            
            # Add the flag directly to the dict
            row["is_noise"] = is_rodj_marker or is_punct
            
        return rows