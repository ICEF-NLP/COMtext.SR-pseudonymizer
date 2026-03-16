import re
from collections import defaultdict
from typing import List

from comtext_sr_pseudonymizer.entities.entity_schema import Entity
from comtext_sr_pseudonymizer.patterns import *


def load_corpus(filepath):
    """
    Parses a CoNLL-U formatted file into a flat list of token dictionaries 
    and a metadata list for full sentence text.
    """
    all_tokens = []
    full_text_metadata = []
    
    doc_id, sent_id, sent_order = "", "", 0
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if not line:
                continue
            if line.startswith('# newdoc id'):
                doc_id = line.split('=')[1].strip()
                continue
            elif line.startswith("# sent_id"):
                sent_order += 1
                sent_id = line.split('=')[1].strip()
                continue
            elif line.startswith("# text"):
                sentence_text = line.split('=')[1].strip()
                full_text_metadata.append({
                    "doc_id": doc_id,
                    "sentence_order": sent_order,
                    "sentence_id": sent_id,
                    'text': sentence_text
                })
                continue
            elif not line.startswith("#"):
                parts = line.split('\t')
                if len(parts) < 2:
                    continue

                all_tokens.append({
                    "doc_id" : doc_id,
                    "sentence_order": sent_order,
                    "sentence_id": sent_id,
                    "token_id": int(parts[0]),
                    "token": parts[1],
                    "lemma": parts[2],
                    'msd': parts[3],
                    "ner": parts[4],
                    "entity_type": parts[4].split('-')[-1]
                })
    return all_tokens, full_text_metadata

def create_input_entity_list(tokens_for_tag, entity_type):
    """
    Groups individual tokens into multi-word 'Entity' objects based on BIO tags.
    For example, it joins [B-PER, I-PER] into a single 'PER' entity.
    """
    entity_list = []
    current_group = []

    for row in tokens_for_tag:
        # Check if this token starts a NEW entity (B- tag)
        # If we already have tokens in current_group, it means the previous entity just finished
        if row["ner"].startswith("B-") and current_group:
            # Save the entity we just finished collecting
            entity_list.append(_build_entity_from_list(current_group, entity_type))
            current_group = []

        current_group.append(row)

    # Don't forget the very last entity in the list
    if current_group:
        entity_list.append(_build_entity_from_list(current_group, entity_type))

    return entity_list

def _build_entity_from_list(group, entity_type):
    """Constructs a single Entity instance from a slice of token dictionaries."""
    return Entity(
        doc_id=group[0]["doc_id"],
        sentence_id=group[0]["sentence_id"],
        start_token_num=int(group[0]["token_id"]),
        end_token_num=int(group[-1]["token_id"]),
        original_text=" ".join(str(row["token"]) for row in group),
        entity_group=entity_type,
        # We pass the list of dicts directly to the Entity
        rows=group 
    )

def replace_with_anonymized_values(all_tokens: List[dict], full_sent_metadata: List[dict], results_entity_list: List[Entity]):
    """
    The 'Surgery' function: Replaces original tokens with pseudonyms.
    Handles the complexity of changing token counts (e.g., 1 word replaced by 2).
    """
    # Indexing for fast lookup
    results_by_sent = defaultdict(list)
    for res in results_entity_list:
        results_by_sent[res.sentence_id].append(res)

    tokens_by_sent = defaultdict(list)
    for tok in all_tokens:
        tokens_by_sent[tok['sentence_id']].append(tok)

    final_all_tokens = []
    final_metadata = []
    for sent_row in full_sent_metadata:
        sent_id = sent_row['sentence_id']
        
        current_tokens = tokens_by_sent.get(sent_id, [])
        if not current_tokens:
            continue

        current_sent_meta = dict(sent_row)
        current_results = results_by_sent.get(sent_id, [])

        if not current_results:
            final_all_tokens.extend(current_tokens)
            final_metadata.append(current_sent_meta)
            continue

        tokens_list = [dict(t) for t in current_tokens]
        # Sort results in reverse order to prevent index shifting during string replacement
        current_results.sort(key=lambda x: x.start_token_num, reverse=True)

        for res in current_results:
            start_tn = res.start_token_num
            end_tn = res.end_token_num
            
            # --- String Replacement Logic ---
            # Locate the original tokens in the 'text' metadata and swap them for anonymized text
            target_tokens = [t['token'] for t in tokens_list 
                             if start_tn <= t['token_id'] <= end_tn]

            if target_tokens:
                pattern = r"\s*".join([re.escape(str(t)) for t in target_tokens])
                matches = list(re.finditer(pattern, current_sent_meta['text']))
                if matches:
                    m = matches[-1] 
                    s_char, e_char = m.span()
                    anon_text = format_anonymized_text(res.anonymized_text, res.entity_group)
                    
                    current_sent_meta['text'] = (
                        current_sent_meta['text'][:s_char] + 
                        anon_text + 
                        current_sent_meta['text'][e_char:]
                    )
            # --- Token List Replacement Logic ---
            # If a name like 'Petar' (1 token) becomes 'Marko Marković' (2 tokens),
            # we must expand the list and re-assign B/I tags
            new_words = str(res.anonymized_text).split()
            idx_to_replace = [i for i, t in enumerate(tokens_list) 
                              if start_tn <= t['token_id'] <= end_tn]
            
            if idx_to_replace:
                template = tokens_list[idx_to_replace[0]]
                ner_raw = template.get('ner', 'O')
                ner_label = ner_raw.split('-')[1] if '-' in ner_raw else ner_raw
                
                new_token_dicts = []
                for i, word in enumerate(new_words):
                    new_t = dict(template)
                    new_t.update({
                        'token': word,
                        'ner': f"B-{ner_label}" if i == 0 else f"I-{ner_label}",
                        'lemma': "UNKNOWNN",
                        'msd': "UNKNOWN"
                    })
                    new_token_dicts.append(new_t)

                # Slice replacement: swap old tokens for the new list of pseudonym tokens
                tokens_list[idx_to_replace[0] : idx_to_replace[-1] + 1] = new_token_dicts

        # Normalize token IDs (1, 2, 3...) after replacements changed the list length
        for i, t in enumerate(tokens_list, 1):
            t['token_id'] = i
            
        final_all_tokens.extend(tokens_list)
        final_metadata.append(current_sent_meta)

    return final_all_tokens, final_metadata

def export_to_conllu(all_tokens: List[dict], all_metadata: List[dict], output_path):
    token_groups = defaultdict(list)
    for tok in all_tokens:
        token_groups[tok['sentence_id']].append(tok)

    for sid in token_groups:
        token_groups[sid].sort(key=lambda x: x['token_id'])

    with open(output_path, 'w', encoding='utf-8', buffering=65536) as f:
        current_doc_id = None
        for sent in all_metadata:
            s_id = sent['sentence_id']
            s_text = sent['text']
            d_id = sent['doc_id']
            
            if d_id != current_doc_id:
                f.write(f"# newdoc id = {d_id}\n")
                current_doc_id = d_id
            f.write(f"# sent_id = {s_id}\n")
            f.write(f"# text = {s_text}\n")
            
            relevant_tokens = token_groups.get(s_id, [])
            for tok in relevant_tokens:
                line = f"{int(tok['token_id'])}\t{tok['token']}\t{tok['ner']}\n"
                f.write(line)
            f.write("\n")

def format_anonymized_text(text, entity_group):
    """Cleans up punctuation and spacing for the final sentence display."""
    text = str(text)
    if entity_group == "DATE":
        text = DOT_WHITESPACE_DIGIT.sub('', text)
        text = DOT_LETTER.sub(' ', text)
    
    text = WHITESPACE_PAREN_OPEN_WHITESPACE.sub(' (', text)
    text = WHITESPACE_PAREN_CLOSE_WHITESPACE.sub(') ', text)
    if entity_group != "MONEY":
        text = WHITESPACE_COMMA_WHITESPACE.sub(', ', text)

    return WHITESPACE_SEQUENCE.sub(' ', text).strip()