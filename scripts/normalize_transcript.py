"""
DataCatalyst: Automated Transcript Normalizer & Filler Stripper
Converts raw Human Verbatim transcripts into clean Normalized ground-truth.
Usage:
    python scripts/normalize_transcript.py --input-json <path_to_verbatim_json> --output-json <path_to_output>
    python scripts/normalize_transcript.py --text "हाँ मतलब [pause] मैं... मैं कल [filler:haan] 4500 rupees pay कर दूँगा।"
"""

import sys
import re
import json
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Common filler patterns in verbatim Hindi speech
FILLER_PATTERNS = [
    r"\[filler:[^\]]+\]",     # e.g., [filler:haan], [filler:matlab]
    r"\[filler\]",            # generic [filler]
    r"\[pause\]",             # [pause]
    r"\[hesitation\]",        # [hesitation]
    r"\[laughter\]",          # [laughter]
    r"\[cough\]",            # [cough]
    r"\[sigh\]",             # [sigh]
    r"\[crosstalk\]",         # [crosstalk]
    r"\b(हम्म|umm|uhh|uh|er|ah)\b",  # standalone vocalizations
]

# Common Hindi spelling normalizations
SPELLING_NORMALIZATIONS = {
    "हां": "हाँ",
    "किये": "किए",
    "दिये": "दिए",
    "लिये": "लिए",
    "गया": "गया",
}

def clean_stutters(text: str) -> str:
    """Collapses word repetitions and ellipsis stutters like 'मैं... मैं' -> 'मैं'."""
    pattern = r"(?<!\S)([^\s\.,\?!।]+)(?:\s*(?:\.\.\.|,|…|-)\s*|\s+)\1(?!\S)"
    prev = None
    while prev != text:
        prev = text
        text = re.sub(pattern, r"\1", text, flags=re.IGNORECASE | re.UNICODE)
    return text

def normalize_hindi_verbatim(text: str) -> str:
    """Transforms raw verbatim Hindi text into clean normalized text."""
    if not text or not isinstance(text, str):
        return ""

    cleaned = text

    # 1. Strip explicit filler and acoustic tags
    for pat in FILLER_PATTERNS:
        cleaned = re.sub(pat, " ", cleaned, flags=re.IGNORECASE | re.UNICODE)

    # 2. Collapse false-start stutters
    cleaned = clean_stutters(cleaned)

    # 3. Apply standard spelling normalizations
    for raw_word, norm_word in SPELLING_NORMALIZATIONS.items():
        cleaned = re.sub(rf"\b{raw_word}\b", norm_word, cleaned)

    # 4. Clean up ellipses and dangling dashes
    cleaned = re.sub(r"\.{2,}|…", " ", cleaned)
    cleaned = re.sub(r"\s+-\s+", " ", cleaned)

    # 5. Normalize whitespace and trailing punctuation
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # 6. Ensure proper sentence ending (Devanagari purna viram or question mark)
    if cleaned and not cleaned[-1] in ("।", "?", "!", ".", ","):
        cleaned += "।"

    # Clean double punctuation
    cleaned = re.sub(r"([।\?!,\.])\1+", r"\1", cleaned)

    return cleaned

def process_transcript_file(input_path: Path, output_path: Path = None) -> list:
    """Reads a session transcript JSON and adds normalized layer to every utterance."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Supports either list of utterances or dictionary with 'utterances'
    utterances = data if isinstance(data, list) else data.get("utterances", [])

    for utt in utterances:
        raw_verb = utt.get("verbatim", "")
        if raw_verb and not utt.get("normalized"):
            utt["normalized"] = normalize_hindi_verbatim(raw_verb)

    out_file = output_path or input_path
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return utterances

def main():
    parser = argparse.ArgumentParser(description="DataCatalyst Automated Transcript Normalizer & Filler Stripper")
    parser.add_argument("--text", type=str, help="Single verbatim string to normalize")
    parser.add_argument("--input-json", type=str, help="Path to transcript JSON file")
    parser.add_argument("--output-json", type=str, help="Path to save output JSON")
    args = parser.parse_args()

    if args.text:
        res = normalize_hindi_verbatim(args.text)
        print("\n--- TRANSCRIPT NORMALIZATION RESULT ---")
        print(f" Raw Verbatim : {args.text}")
        print(f" Normalized   : {res}\n")
    elif args.input_json:
        in_p = Path(args.input_json)
        out_p = Path(args.output_json) if args.output_json else None
        if not in_p.exists():
            print(f"Error: File not found: {in_p}")
            sys.exit(1)
        utts = process_transcript_file(in_p, out_p)
        print(f"Successfully processed {len(utts)} utterances in {in_p}")
    else:
        # Run demonstration
        demo_samples = [
            "हाँ मतलब [pause] मैं... मैं कल [filler:haan] 4500 rupees pay कर दूँगा।",
            "अच्छा [filler:achha] आप... आप मुझे [PII_PHONE] पर कॉल कॉल कर लेना।",
            "[hesitation] वो क्या है ना... मुझे [laughter] थोड़ा टाइम लगेगा।"
        ]
        print("\n=======================================================")
        print(" DataCatalyst Transcript Normalization Demo")
        print("=======================================================\n")
        for s in demo_samples:
            clean = normalize_hindi_verbatim(s)
            print(f" Raw Verbatim : {s}")
            print(f" Normalized   : {clean}\n")

if __name__ == "__main__":
    main()
