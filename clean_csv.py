"""Clean and validate a customer CSV locally. Python 3.10+, standard library only."""
import argparse
import csv
import html
import json
import re
from collections import Counter
from pathlib import Path

FIELDS = ['customer_id', 'name', 'email', 'country']

def process(source):
    accepted, rejected, issues = [], [], []
    seen, counts = set(), Counter()
    with Path(source).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, strict=True)
        headers = reader.fieldnames
        if headers is None:
            raise ValueError('CSV has no header.')
        normalized = [h.strip().lower().replace(' ', '_') for h in headers]
        if len(set(normalized)) != len(normalized):
            raise ValueError('Duplicate column names after header normalization.')
        if set(normalized) != set(FIELDS):
            raise ValueError('Expected exactly these columns: ' + ', '.join(FIELDS))
        for record, raw in enumerate(reader, 1):
            counts['input_records'] += 1
            start_issues = len(issues)
            def note(severity, code, detail):
                issues.append(dict(record=record, severity=severity, code=code, detail=detail))
            if None in raw or any(value is None for value in raw.values()):
                note('error', 'column_count', 'Record has too many or too few cells.')
                rejected.append(dict(record=record, reason='column_count', original_json=json.dumps(raw, ensure_ascii=False)))
                continue
            row = dict(zip(normalized, raw.values()))
            original = row.copy()
            if not any(v.strip() for v in row.values()):
                note('error', 'empty_record', 'All fields are empty.')
            row = {key: value.strip() for key, value in row.items()}
            row['name'] = ' '.join(row['name'].split())
            row['country'] = row['country'].upper()
            # Preserve the email local part; only normalize the domain.
            if row['email'].count('@') == 1:
                local, domain = row['email'].split('@')
                row['email'] = local + '@' + domain.lower()
            if row != original:
                counts['normalized_records'] += 1
                note('info', 'normalized', 'Trimmed whitespace, collapsed name spacing, uppercased country, or lowercased email domain.')
            for key in FIELDS:
                if not row[key]:
                    note('error', 'missing_' + key, key + ' is required.')
            if row['email'] and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', row['email']):
                note('error', 'invalid_email', 'Email failed a basic format check; no mailbox verification performed.')
            if row['country'] and not re.fullmatch(r'[A-Z]{2}', row['country']):
                note('error', 'invalid_country', 'Country must be two ASCII letters; country existence is not checked.')
            for key, value in row.items():
                if value.startswith(('=', '+', '-', '@')):
                    note('error', 'spreadsheet_formula', key + ' starts with a spreadsheet formula indicator.')
            errors = [item['code'] for item in issues[start_issues:] if item['severity'] == 'error']
            if not errors:
                identity = tuple(row[key] for key in FIELDS)
                if identity in seen:
                    note('warning', 'duplicate', 'Exact normalized duplicate removed; no fuzzy matching.')
                    errors = ['duplicate']
                else:
                    seen.add(identity)
            if errors:
                rejected.append(dict(record=record, reason='; '.join(errors), original_json=json.dumps(original, ensure_ascii=False)))
            else:
                accepted.append(row)
    counts['accepted_records'] = len(accepted)
    counts['rejected_records'] = len(rejected)
    counts['duplicate_records'] = sum(item['code'] == 'duplicate' for item in issues)
    counts['error_records'] = len({item['record'] for item in issues if item['severity'] == 'error'})
    return accepted, rejected, issues, dict(counts)

def safe_cell(value):
    """Protect spreadsheet consumers of audit files against formula-like strings."""
    value = str(value)
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value

def write_csv(path, fields, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: safe_cell(v) for k, v in row.items()} for row in rows)

def report_html(stats, accepted, rejected, issues):
    esc = lambda value: html.escape(str(value))
    def table(fields, rows):
        return '<div class="scroll"><table><thead><tr>' + ''.join('<th>'+esc(f.replace('_',' '))+'</th>' for f in fields) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+esc(row[f])+'</td>' for f in fields)+'</tr>' for row in rows) + '</tbody></table></div>'
    cards = ''.join('<div class="card"><span>'+esc(k.replace('_',' '))+'</span><strong>'+esc(stats.get(k,0))+'</strong></div>' for k in ['input_records','accepted_records','rejected_records','normalized_records'])
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>CSV Quality Report</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f1f5f9;color:#152337;font:16px/1.55 Arial,sans-serif}main{max-width:1120px;margin:40px auto;padding:0 28px 36px}header{background:#112c42;color:white;padding:30px;border-radius:16px}header small{color:#7ce3c5;font-weight:bold;letter-spacing:2px}h1{font-size:34px;margin:10px 0}header p{margin:0;color:#d5e1eb}h2{font-size:21px;margin:30px 0 12px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0}.card{background:white;border:1px solid #d9e3eb;border-radius:12px;padding:20px}.card span{display:block;text-transform:uppercase;font-size:11px;letter-spacing:1px;color:#54677c}.card strong{font-size:36px}.scroll{overflow:auto;background:white;border:1px solid #d9e3eb;border-radius:10px}table{width:100%;border-collapse:collapse;text-align:left;font-size:13px}th{background:#e8eff5;text-transform:capitalize}td,th{padding:12px;border-bottom:1px solid #e3eaf0;vertical-align:top}td{overflow-wrap:anywhere}footer{color:#54677c;font-size:13px;margin-top:24px}.note{color:#54677c;font-size:14px}@media(max-width:650px){.cards{grid-template-columns:repeat(2,1fr)}h1{font-size:26px}}
    </style><main><header><small>PYTHON AUTOMATION · PORTFOLIO DEMO</small><h1>CSV Data Cleaner &amp; Validator</h1><p>Local processing. Explicit validation. Traceable results.</p></header>''' + '<div class="cards">'+cards+'</div><p class="note">Accepted + rejected = input records. Rejected includes duplicates and validation failures. Normalized records may overlap either group. Blank physical lines are ignored by the CSV reader.</p><h2>Clean output</h2>' + table(FIELDS, accepted[:20]) + '<h2>Issue audit</h2>'+table(['record','severity','code','detail'], issues[:50])+'<footer>Preview limited to 20 accepted records and 50 issues. Full audit and rejected records are in the exported CSV files. This sample uses synthetic customer data; it does not represent paid client work.</footer></main></html>'

def run(source, output):
    source, output = Path(source), Path(output)
    names = ['cleaned.csv','rejected.csv','issues.csv','summary.json','report.html']
    if any(source.resolve() == (output/name).resolve() for name in names):
        raise ValueError('Output would overwrite the input. Choose a different output folder.')
    if any((output/name).exists() for name in names):
        raise ValueError('Output files already exist. Choose a new output folder.')
    accepted, rejected, issues, stats = process(source)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output/'cleaned.csv', FIELDS, accepted)
    write_csv(output/'rejected.csv', ['record','reason','original_json'], rejected)
    write_csv(output/'issues.csv', ['record','severity','code','detail'], issues)
    (output/'summary.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
    (output/'report.html').write_text(report_html(stats, accepted, rejected, issues), encoding='utf-8')
    return stats

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.input,args.output),indent=2))
    except (ValueError, OSError, csv.Error, UnicodeError) as error:
        parser.exit(1, 'Error: '+str(error)+'\n')
