"""
Test case loader supporting CSV, JSON, and TXT formats.
"""

from pathlib import Path
from typing import List
import csv
import json

from .config import TestCase


def load_test_cases(file_path: str) -> List[TestCase]:
    """
    Load test cases from CSV, JSON, or TXT file.

    Args:
        file_path: Path to test data file

    Returns:
        List of TestCase objects

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")

    ext = path.suffix.lower()

    if ext == '.csv':
        return load_from_csv(file_path)
    elif ext == '.json':
        return load_from_json(file_path)
    elif ext == '.txt':
        return load_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .csv, .json, or .txt")


def load_from_csv(file_path: str) -> List[TestCase]:
    """
    Load from CSV with columns: entry_ref, sense_id, word, pos.

    Example:
        entry_ref,sense_id,word,pos
        fine_n,fine_n01_1,fine,n
    """
    test_cases = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            # Validate required fields
            required = ['entry_ref', 'sense_id', 'word', 'pos']
            missing = [field for field in required if not row.get(field)]

            if missing:
                print(f"Warning: Row {row_num} missing fields {missing}, skipping")
                continue

            # Parse gold labels if present
            gold_labels = None
            if row.get('gold_labels'):
                gold_labels = [label.strip() for label in row['gold_labels'].split(',') if label.strip()]

            test_cases.append(TestCase(
                entry_ref=row['entry_ref'].strip(),
                sense_id=row['sense_id'].strip(),
                word=row['word'].strip(),
                pos=row['pos'].strip(),
                gold_labels=gold_labels
            ))

    return test_cases


def load_from_json(file_path: str) -> List[TestCase]:
    """
    Load from JSON array of objects.

    Example:
        [
          {
            "entry_ref": "fine_n",
            "sense_id": "fine_n01_1",
            "word": "fine",
            "pos": "n"
          }
        ]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON file must contain an array of objects")

    test_cases = []
    for idx, item in enumerate(data):
        # Validate required fields
        required = ['entry_ref', 'sense_id', 'word', 'pos']
        missing = [field for field in required if field not in item]

        if missing:
            print(f"Warning: Item {idx} missing fields {missing}, skipping")
            continue

        test_cases.append(TestCase(
            entry_ref=item['entry_ref'],
            sense_id=item['sense_id'],
            word=item['word'],
            pos=item['pos'],
            gold_labels=item.get('gold_labels')
        ))

    return test_cases


def load_from_txt(file_path: str) -> List[TestCase]:
    """
    Load from TXT file (space-separated: entry_ref sense_id word pos).

    Example:
        fine_n fine_n01_1 fine n
        fair_n fair_n02_3 fair n
    """
    test_cases = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) < 4:
                print(f"Warning: Line {line_num} invalid format (need 4 fields), skipping")
                continue

            test_cases.append(TestCase(
                entry_ref=parts[0],
                sense_id=parts[1],
                word=parts[2],
                pos=parts[3]
            ))

    return test_cases


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_case_loader.py <test_data_file>")
        sys.exit(1)

    test_cases = load_test_cases(sys.argv[1])
    print(f"Loaded {len(test_cases)} test cases")

    if test_cases:
        print(f"\nFirst test case:")
        tc = test_cases[0]
        print(f"  Entry Ref: {tc.entry_ref}")
        print(f"  Sense ID: {tc.sense_id}")
        print(f"  Word: {tc.word}")
        print(f"  POS: {tc.pos}")
