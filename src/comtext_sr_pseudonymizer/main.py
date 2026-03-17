import argparse
import csv
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from comtext_sr_pseudonymizer.data_manager import DataManager
from comtext_sr_pseudonymizer.entities import ENTITY_MAP
from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.io_helper import (
    load_corpus, 
    create_input_entity_list, 
    export_to_conllu, 
    replace_with_anonymized_values
)
from comtext_sr_pseudonymizer.lex import Lex
from pprint import pprint

def run_anonymization(input_filepath, results_folder="results", selected_entities=None):
    """
    Main pipeline: Loads data -> Anonymizes by category -> Merges results -> Exports.
    """

    print(f"=== LOADING DATA STARTED === {datetime.now().strftime('%Y.%m.%d__%H:%M:%S')}")
    start_time = time.perf_counter()
    # 1. PATH VALIDATION
    abs_input_path = Path(input_filepath).resolve()
    if not abs_input_path.exists():
        print(f"Error: Input file not found at {abs_input_path}")
        return
    else:
        print(f"Loading corpus from: {abs_input_path}")

    # 2. IO INITIALIZATION
    all_tokens, full_text_metadata = load_corpus(input_filepath)
    
    # Setup results directory and filenames with timestamps
    res_path = Path(results_folder)
    res_path.mkdir(parents=True, exist_ok=True)
    results_timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S')
    results_intermed_path = res_path / f"{abs_input_path.stem}_{results_timestamp}_replacements.tsv"
    results_conllu_path = res_path / f"{abs_input_path.stem}_{results_timestamp}.conllu"

    # 3. RESOURCE INITIALIZATION (Singletons) and timestamps
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    lex = Lex()
    data_manager = DataManager()
    shared_rng = random.Random()

    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    print(f"    loading data took: {duration_ms:.2f} ms")

    # 4. PROCESSING LOOP
    print(f"=== ANONYMIZATION STARTED === {datetime.now().strftime('%Y.%m.%d__%H:%M:%S')}")
    start = time.perf_counter()
    entity_result_list = []
    # Determine which entities to process (CLI filtered or all from map)
    target_tags = sorted(selected_entities) if selected_entities else ENTITY_MAP.keys()
    for tag in target_tags:
        config = ENTITY_MAP.get(tag)
        if not config:
            print(f"Warning: Entity type '{tag}' not supported. Skipping.")
            continue
        # Filter tokens belonging to this specific NER category
        tokens_for_tag = [t for t in all_tokens if t['entity_type'] == tag]
        if not tokens_for_tag:
            continue
        # Dependency Injection: Build the arguments required by the specific class constructor
        kwargs = {'timestamp': timestamp, 'rng':shared_rng}
        if 'dm' in config['deps']: kwargs['data_manager'] = data_manager
        if 'lex' in config['deps']: kwargs['lex'] = lex
        try:
            # Instantiate the handler (e.g., ToponymAnonymizer) and run logic
            handler = config['class'](**kwargs)
            # Group tokens into multi-word Entity objects
            entity_list = create_input_entity_list(tokens_for_tag, tag)
            # Execute anonymization and collect results
            result = handler.anonymize(entity_list)
            entity_result_list.extend(result)
        except Exception as e:
            print(f"Error processing {tag}: {e}")

    if not entity_result_list:
        print("No entities were found to anonymize. Exiting gracefully.")
        return
    
    end = time.perf_counter()
    data_manager.clear_mapping()
    print(f"    anonymization took: {(end - start) * 1000:.2f} ms")

    # 5. RESULT SERIALIZATION
    print(f"=== WRITING RESULTS STARTED === {datetime.now().strftime('%Y.%m.%d__%H:%M:%S')}")
    start_time = time.perf_counter()
    # Sort for consistent output (Sentence ID -> Token Order)
    entity_result_list.sort(key=lambda x: (x.sentence_id, x.start_token_num))
    target_headers = [
        "doc_id", 
        "sentence_id", 
        "start_token_num", 
        "end_token_num", 
        "original_text", 
        "entity_group", 
        "anonymized_text"
    ]

    # Write intermediate TSV for debugging/audit trails
    if entity_result_list:
        with open(results_intermed_path, 'w', newline='', encoding='utf-8', buffering=65536) as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(target_headers)
            f.write('\n')
            
            last_doc_id = None  

            for ent in entity_result_list:
                if last_doc_id is not None and ent.doc_id != last_doc_id:
                    f.write('\n') 
                last_doc_id = ent.doc_id
                row = [getattr(ent, h) for h in target_headers]
                writer.writerow(row)
    
    # Perform 'Surgery' on the original tokens to replace them with fake ones
    final_all_tokens, final_metadata = replace_with_anonymized_values(all_tokens, full_text_metadata, entity_result_list)
    # Export back to standardized CoNLL-U format
    export_to_conllu(final_all_tokens, final_metadata, output_path=results_conllu_path)
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    print(f"    writing results took: {duration_ms:.2f} ms")
    print(f"=== EVERYTHING DONE === {datetime.now().strftime('%Y.%m.%d__%H:%M:%S')}")


def main():
    """CLI wrapper using argparse."""
    parser = argparse.ArgumentParser(description="Anonymize sensitive entities in CoNLL-U files.")
    parser.add_argument("--input", "-i", required=True, help="Path to input CoNLL-U file")
    parser.add_argument("--output", "-o", help="Folder to save results.", default="results")
    parser.add_argument("--types", "-t", nargs="+", help="Optional: List of entities to process (e.g., PER ADR)", default=None)
    args = parser.parse_args()

    try:
        run_anonymization(input_filepath=args.input, results_folder=args.output, selected_entities=args.types)
    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()