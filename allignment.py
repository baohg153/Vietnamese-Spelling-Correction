import json
import Levenshtein
from typing import List, Tuple, Optional

# ==========================================
# CONFIGURATION - EDIT THESE VALUES
# ==========================================
INPUT_LABEL = 'my_label.txt'
REF_FILE = 'correct.txt'
OUTPUT_LABEL = 'Label.txt'

THRESHOLD = 0.55
PERFECT_MATCH_THRESHOLD = 0.95
SEARCH_WINDOW = 300
MAX_OCR_LENGTH = 50
# ==========================================

def normalize_for_matching(text: str) -> str:
    text = text.replace('-', ' ').replace('_', ' ')
    text = ' '.join(text.split())
    return text

def load_reference_text(filepath: str) -> Optional[List[str]]:
    """Load and tokenize reference text."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            full_text = f.read().replace('\n', ' ')
            full_text = ' '.join(full_text.split())
            ref_words = full_text.split()
        print(f"Reference loaded: {len(ref_words)} words.")
        return ref_words
    except Exception as e:
        print(f"Error loading reference: {e}")
        return None

def estimate_word_count(text: str) -> int:
    """
    Estimate 'semantic' word count accounting for hyphens.
    'Bình-Định' counts as 2 words, not 1.
    """
    normalized = normalize_for_matching(text)
    return len(normalized.split())

def find_best_match(ocr_text: str, ref_words: List[str], 
                    last_index: int = 0) -> Tuple[str, float, int]:
    normalized_ocr = normalize_for_matching(ocr_text)
    ocr_word_count = len(normalized_ocr.split())
    
    if ocr_word_count == 0:
        return ocr_text, 0.0, last_index
    
    if ocr_word_count > MAX_OCR_LENGTH:
        return ocr_text, 0.0, last_index
    
    best_ratio = 0.0
    best_match_text = ocr_text
    found_index = last_index
    
    max_ref_idx = len(ref_words)
    start_idx = max(0, last_index - SEARCH_WINDOW)
    end_idx = min(last_index + SEARCH_WINDOW + ocr_word_count + 5, max_ref_idx)
    
    primary_region = (start_idx, end_idx)
    
    backup_regions = [
        (0, start_idx),
        (end_idx, max_ref_idx)
    ]
    
    window_sizes = [ocr_word_count, ocr_word_count + 1, ocr_word_count - 1, 
                    ocr_word_count + 2, ocr_word_count - 2, ocr_word_count + 3]
    
    for window_size in window_sizes:
        if window_size <= 0 or window_size > max_ref_idx:
            continue
        
        for region_start, region_end in [primary_region]:
            if region_start >= region_end:
                continue
            
            for i in range(region_start, min(region_end, max_ref_idx - window_size + 1)):
                candidate_words = ref_words[i:i + window_size]
                candidate_text = ' '.join(candidate_words)
                
                norm_candidate = normalize_for_matching(candidate_text)
                
                ratio = Levenshtein.ratio(normalized_ocr, norm_candidate)
                
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match_text = candidate_text
                    found_index = i
                    
                    if ratio >= PERFECT_MATCH_THRESHOLD:
                        return best_match_text, best_ratio, found_index
        
        if best_ratio >= 0.75:
            break
    
    if best_ratio < 0.75:
        for window_size in window_sizes[:4]:
            if window_size <= 0 or window_size > max_ref_idx:
                continue
            
            for region_start, region_end in backup_regions:
                if region_start >= region_end:
                    continue
                
                for i in range(region_start, min(region_end, max_ref_idx - window_size + 1), 10):
                    candidate_words = ref_words[i:i + window_size]
                    candidate_text = ' '.join(candidate_words)
                    norm_candidate = normalize_for_matching(candidate_text)
                    
                    ratio = Levenshtein.ratio(normalized_ocr, norm_candidate)
                    
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match_text = candidate_text
                        found_index = i
                
                if best_ratio >= 0.85:
                    break
            
            if best_ratio >= 0.85:
                break
    
    return best_match_text, best_ratio, found_index

def fix_ppocr_labels():
    """Main correction function."""
    print("=" * 60)
    print("PPOCRLabel Correction Tool")
    print("=" * 60)
    
    print("\n[1/3] Loading Reference Text...")
    ref_words = load_reference_text(REF_FILE)
    if ref_words is None:
        return
    
    print(f"\n[2/3] Processing {INPUT_LABEL}...")
    
    try:
        with open(INPUT_LABEL, 'r', encoding='utf-8') as f_in, \
             open(OUTPUT_LABEL, 'w', encoding='utf-8') as f_out:
            
            lines_processed = 0
            corrections = 0
            skipped = 0
            last_match_index = 0
            
            for line_num, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    parts = line.split('\t', 1)
                    if len(parts) != 2:
                        skipped += 1
                        f_out.write(line + '\n')
                        continue
                    
                    img_path, json_str = parts
                    data = json.loads(json_str)
                    
                    line_had_correction = False
                    
                    for item in data:
                        ocr_text = item.get('transcription', '').strip()
                        if not ocr_text:
                            continue
                        
                        best_match, ratio, found_idx = find_best_match(
                            ocr_text, ref_words, last_match_index
                        )
                        
                        if ratio > THRESHOLD and ocr_text != best_match:
                            item['transcription'] = best_match
                            corrections += 1
                            line_had_correction = True
                            
                            if ratio >= 0.75:
                                last_match_index = found_idx
                            else:
                                last_match_index = max(last_match_index, found_idx - 50)
                            
                            if ratio < 0.75:
                                print(f" Line {line_num} | Confidence: {ratio:.2%}")
                                print(f"  OCR: {ocr_text}")
                                print(f"  Fix: {best_match}\n")
                    
                    f_out.write(f"{img_path}\t{json.dumps(data, ensure_ascii=False)}\n")
                    lines_processed += 1
                    
                    if lines_processed % 100 == 0:
                        print(f"Progress: {lines_processed} lines | {corrections} corrections")
                
                except json.JSONDecodeError:
                    print(f"✗ Line {line_num}: Invalid JSON")
                    skipped += 1
                    f_out.write(line + '\n')
                except Exception as e:
                    print(f"✗ Line {line_num}: {e}")
                    skipped += 1
                    f_out.write(line + '\n')
        
        print("\n" + "=" * 60)
        print("[3/3] Correction Complete!")
        print("=" * 60)
        print(f"Lines processed: {lines_processed}")
        print(f"Corrections made: {corrections}")
        print(f"Lines skipped: {skipped}")
        print(f"Output file: {OUTPUT_LABEL}")
        print("=" * 60)
        
    except FileNotFoundError:
        print(f"Error: Could not find {INPUT_LABEL}")
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    fix_ppocr_labels()
    