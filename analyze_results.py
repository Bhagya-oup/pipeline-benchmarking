#!/usr/bin/env python3
"""Analyze comparison results."""

import pandas as pd

df = pd.read_csv('results/test_run_52/comparison_20260113_190316.csv')

# Show cases where pipelines differ
different = df[df['new_matching_quotations'] != df['old_matching_quotations']]

print('='*80)
print('CASES WHERE PIPELINES DIFFER')
print('='*80)
print(f'\nTotal: {len(different)} cases where pipelines returned different match counts\n')

if len(different) > 0:
    for _, row in different.head(20).iterrows():
        new_match = int(row['new_matching_quotations'])
        old_match = int(row['old_matching_quotations'])
        diff = new_match - old_match
        winner = 'NEW' if diff > 0 else 'OLD'
        print(f'{row["entry_ref"]:20s} (sense {row["sense_id"]})')
        print(f'  NEW: {new_match}/{int(row["new_total_quotations"])} matching  |  OLD: {old_match}/{int(row["old_total_quotations"])} matching  |  Winner: {winner} (+{abs(diff)})')

# Summary stats
print('\n' + '='*80)
print('OVERALL SUMMARY')
print('='*80)
new_total = int(df['new_matching_quotations'].sum())
old_total = int(df['old_matching_quotations'].sum())
print(f'Total matching quotations:')
print(f'  NEW pipeline: {new_total}')
print(f'  OLD pipeline: {old_total}')
if old_total > 0:
    print(f'  Difference: {new_total - old_total} ({(new_total/old_total-1)*100:+.1f}%)')

print(f'\nAverage matching per test case:')
print(f'  NEW pipeline: {df["new_matching_quotations"].mean():.2f}')
print(f'  OLD pipeline: {df["old_matching_quotations"].mean():.2f}')

print(f'\nWin/Loss/Tie breakdown:')
wins = len(df[df['new_matching_quotations'] > df['old_matching_quotations']])
losses = len(df[df['new_matching_quotations'] < df['old_matching_quotations']])
ties = len(df[df['new_matching_quotations'] == df['old_matching_quotations']])
print(f'  NEW wins: {wins}')
print(f'  OLD wins: {losses}')
print(f'  Ties: {ties}')
