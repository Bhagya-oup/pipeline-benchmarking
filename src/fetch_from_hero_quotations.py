#!/usr/bin/env python3
"""
Wrapper for Hero Quotations API.
Matches the production pipeline's quotations_api component.
"""
import requests
from typing import List, Dict, Any


def fetch_quotations_from_hero_api(
    lemma: str,
    part_of_speech: str,
    api_key: str,
    host: str = "https://0zcaaoguqe.execute-api.us-east-1.amazonaws.com/prod",
    random_selection: int = 1000
) -> List[Dict[str, Any]]:
    """
    Fetch quotations from Hero Quotations API.

    Args:
        lemma: Word to search for (e.g., "fine", "aaron")
        part_of_speech: Full POS name (e.g., "noun", "verb", "adjective")
        api_key: Hero API key
        host: API host URL
        random_selection: Number of random quotations to fetch

    Returns:
        List of documents in Haystack-compatible format

    Example:
        >>> quotations = fetch_quotations_from_hero_api(
        ...     lemma="fine",
        ...     part_of_speech="noun",
        ...     api_key="your_key"
        ... )
    """
    url = f"{host.rstrip('/')}/quotations"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "lemma": lemma,
        "part_of_speech": part_of_speech,
        "random_selection": random_selection
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()

        # Convert Hero API response to Haystack Document format
        # Expected response: {"matches": [{"text": "...", "author": "...", ...}, ...]}
        if not data or "matches" not in data:
            return []

        documents = []
        for idx, match in enumerate(data["matches"]):
            doc = {
                "content": match.get("text", ""),
                "meta": {
                    "lemma": lemma,
                    "part_of_speech": part_of_speech,
                    "author": match.get("author", "Unknown"),
                    "title": match.get("title", ""),
                    "year": match.get("year"),
                    "doc_id": match.get("id", f"{lemma}_{idx}"),
                    "quotation_index": idx,
                    "source": "hero_quotations_api"
                }
            }
            documents.append(doc)

        return documents

    except requests.exceptions.RequestException as e:
        raise Exception(f"Hero Quotations API error: {str(e)}")


# Example usage
if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) < 3:
        print("Usage: python fetch_from_hero_quotations.py <lemma> <part_of_speech>")
        print("Example: python fetch_from_hero_quotations.py fine noun")
        sys.exit(1)

    lemma = sys.argv[1]
    part_of_speech = sys.argv[2]

    api_key = os.getenv("HERO_API_KEY")
    if not api_key:
        print("Error: Set HERO_API_KEY environment variable")
        sys.exit(1)

    try:
        documents = fetch_quotations_from_hero_api(
            lemma=lemma,
            part_of_speech=part_of_speech,
            api_key=api_key
        )

        print(f"Fetched {len(documents)} quotations for '{lemma}' ({part_of_speech})")
        if documents:
            print(f"\nFirst quotation:")
            print(f"  Text: {documents[0]['content'][:100]}...")
            print(f"  Author: {documents[0]['meta']['author']}")
            print(f"  Year: {documents[0]['meta']['year']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
