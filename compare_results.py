#!/usr/bin/env python3
"""
Compare results from multiple pipeline runs.

Usage:
    python compare_results.py results/base_run/*.csv results/hybrid_run/*.csv
    python compare_results.py pipeline1.csv pipeline2.csv pipeline3.csv
"""

import sys
import pandas as pd
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_results.py <csv1> <csv2> [csv3 ...]")
        print("\nExample:")
        print("  python compare_results.py results/base_run/*.csv results/hybrid_run/*.csv")
        sys.exit(1)

    # Load all CSV files
    csv_files = sys.argv[1:]
    dataframes = []
    names = []

    for csv_file in csv_files:
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"Error: File not found: {csv_file}")
            continue

        df = pd.read_csv(csv_path)
        dataframes.append(df)

        # Extract pipeline name from filename
        name = csv_path.stem.split('_')[0]  # e.g., "oed-quotations" from "oed-quotations_20260113.csv"
        names.append(name)

    if len(dataframes) < 2:
        print("Error: Need at least 2 valid CSV files to compare")
        sys.exit(1)

    print("="*80)
    print("PIPELINE COMPARISON")
    print("="*80)
    print(f"\nComparing {len(dataframes)} pipelines:")
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}")

    print("\n" + "="*80)
    print("OVERALL STATISTICS")
    print("="*80)
    print()

    # Overall stats for each pipeline
    results = []
    for name, df in zip(names, dataframes):
        total_quotations = df['total_quotations'].sum()
        total_matching = df['matching_quotations'].sum()
        match_rate = (total_matching / total_quotations * 100) if total_quotations > 0 else 0
        avg_matches = df['matching_quotations'].mean()
        errors = (df['error'] != '').sum()

        results.append({
            'Pipeline': name,
            'Total Quotations': total_quotations,
            'Matching Quotations': total_matching,
            'Match Rate (%)': f"{match_rate:.1f}%",
            'Avg Matches/Case': f"{avg_matches:.2f}",
            'Errors': errors
        })

    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))

    # Head-to-head comparison
    print("\n" + "="*80)
    print("HEAD-TO-HEAD COMPARISON")
    print("="*80)
    print()

    # Merge all dataframes on sense_id
    merged = dataframes[0][['sense_id', 'entry_ref', 'word', 'matching_quotations']].copy()
    merged = merged.rename(columns={'matching_quotations': f'{names[0]}_matches'})

    for i in range(1, len(dataframes)):
        df = dataframes[i][['sense_id', 'matching_quotations']].copy()
        df = df.rename(columns={'matching_quotations': f'{names[i]}_matches'})
        merged = merged.merge(df, on='sense_id', how='outer')

    # Find cases where pipelines differ
    match_cols = [col for col in merged.columns if col.endswith('_matches')]

    # Calculate if all pipelines have same match count
    merged['all_same'] = merged[match_cols].nunique(axis=1) == 1
    different = merged[~merged['all_same']]

    print(f"Total test cases: {len(merged)}")
    print(f"Cases where pipelines agree: {(~merged['all_same']).sum()}")
    print(f"Cases where pipelines differ: {len(different)}")

    if len(different) > 0:
        print(f"\nTop 20 cases with different results:\n")

        # Show differences
        display_cols = ['entry_ref', 'word'] + match_cols
        print(different[display_cols].head(20).to_string(index=False))

        # Winner summary
        print("\n" + "="*80)
        print("WIN/LOSS SUMMARY")
        print("="*80)
        print()

        for i, name in enumerate(names):
            wins = 0
            for j, other_name in enumerate(names):
                if i != j:
                    wins += (merged[f'{name}_matches'] > merged[f'{other_name}_matches']).sum()

            print(f"{name}: {wins} cases where it has the most matches")

    # Perfect matches (100% match rate per case)
    print("\n" + "="*80)
    print("PERFECT MATCHES (100% for any pipeline)")
    print("="*80)
    print()

    for i, (name, df) in enumerate(zip(names, dataframes)):
        perfect = df[(df['matching_quotations'] == df['total_quotations']) & (df['total_quotations'] > 0)]
        print(f"{name}: {len(perfect)}/{len(df)} cases ({len(perfect)/len(df)*100:.1f}%)")

    # Zero matches
    print("\n" + "="*80)
    print("ZERO MATCHES (cases needing investigation)")
    print("="*80)
    print()

    for i, (name, df) in enumerate(zip(names, dataframes)):
        zero = df[df['matching_quotations'] == 0]
        print(f"{name}: {len(zero)}/{len(df)} cases ({len(zero)/len(df)*100:.1f}%)")

        if len(zero) > 0:
            print(f"  First 5: {', '.join(zero['entry_ref'].head(5).tolist())}")


if __name__ == '__main__':
    main()
