"""Summarize indexed workbook validation and detected layouts as JSON.

Run index_reports.py first. Optionally compare states with a prior JSON array of
{sha, state} records using --before PATH. Source workbooks are never modified.
"""
import argparse
from collections import Counter
import json
from index_reports import connect


def audit(db, before=None):
    counts, issues, transitions = Counter(), Counter(), Counter()
    normalized = reversed_order = secondary = 0
    old = {r['sha']: r['state'] for r in before or []}
    versions = Counter()
    for row in db.execute('SELECT sha,state,error,issues,daily,parser_version FROM workbooks'):
        counts[row['state']] += 1
        versions[row['parser_version']] += 1
        if row['sha'] in old:
            transitions[old[row['sha']]+' -> '+row['state']] += 1
        day = json.loads(row['daily'] or '{}')
        notes = day.get('normalizations', [])
        normalized += bool(notes)
        secondary += any('secondary rows' in note for note in notes)
        reversed_order += any(l['columns'].get('retail_buy')=='E' and
                              l['columns'].get('institutional_buy')=='D'
                              for l in day.get('layouts', []))
        for issue in json.loads(row['issues'] or '[]'):
            category = ('footer mismatch' if 'footer mismatch' in issue else
                        'Turnover total mismatch' if 'Turnover total mismatch' in issue else
                        issue.split(':', 1)[0])
            issues[category] += 1
    return {'workbooks': dict(counts), 'parser_versions': dict(versions),
            'workbooks_with_layout_notes': normalized,
            'institutional_first_workbooks': reversed_order,
            'workbooks_with_secondary_rows_excluded': secondary,
            'issue_occurrences': dict(issues), 'state_transitions': dict(transitions),
            'active_dates': db.execute('SELECT COUNT(*) FROM active_reports').fetchone()[0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=argparse.FileType('r', encoding='utf-8'))
    args = parser.parse_args()
    with connect() as db:
        print(json.dumps(audit(db, json.load(args.before) if args.before else None),
                         ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
