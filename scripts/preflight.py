"""Read-only v0.3.1 handoff structure check; no network or credentials."""
import argparse
import hashlib
import json
from pathlib import Path
import re

RULE = ['Rule ID', 'Order', 'Chinese name', 'Enabled', 'Event', 'Keywords',
        'Match semantics', 'Property ID', 'LLM condition', 'Acknowledgement',
        'Timing', 'Completion', 'Failure', 'Cooldown seconds', 'Cooldown scope',
        'Expiry seconds', 'Basis']
STEP = ['Rule ID', 'Step', 'Action', 'Text or prompt', 'Spoken language',
        'Capability', 'Parameters', 'Template mode', 'Template category',
        'Required switch', 'Switch trigger', 'Basis']


def parse_tables(text):
    """Only accept the documented two tables; report malformed/duplicate tables."""
    found, errors = {}, []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.startswith('| Rule ID |'):
            continue
        header = [c.strip() for c in line.strip().strip('|').split('|')]
        kind = 'rules' if 'Order' in header else 'steps'
        if header != (RULE if kind == 'rules' else STEP):
            errors.append(f'{kind}: unsupported header')
        if kind in found:
            errors.append(f'{kind}: duplicate table')
        rows = []
        if i >= len(lines) or not re.fullmatch(r'[\s|:\-]+', lines[i]):
            errors.append(f'{kind}: missing separator')
        else:
            i += 1
        while i < len(lines) and lines[i].startswith('|'):
            cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
            if len(cells) != len(header) or not all(cells):
                errors.append(f'{kind}: empty cell or wrong width at line {i+1}')
            else:
                rows.append(dict(zip(header, cells)))
            i += 1
        found[kind] = rows
    for kind in ('rules', 'steps'):
        if kind not in found:
            errors.append(f'{kind}: missing table (legacy package requires review)')
    return found, errors


def validate_tables(text, categories):
    tables, errors = parse_tables(text)
    if errors:
        return tables, errors
    rules, steps = tables['rules'], tables['steps']
    ids = [r['Rule ID'] for r in rules]
    if len(ids) != len(set(ids)):
        errors.append('duplicate Rule ID')
    if [r['Order'] for r in rules] != [str(i+1) for i in range(len(rules))]:
        errors.append('rule order must follow table order, starting at 1')
    for row in rules + steps:
        if any(v.upper().startswith('PENDING') for v in row.values()):
            errors.append(f"{row['Rule ID']}: pending field requires resolution")
    for rule in rules:
        rid = rule['Rule ID']
        if rule['Event'] == 'Comments' and rule['Enabled'] != 'true':
            errors.append(f'{rid}: configured comment rule must be enabled')
        if rule['Event'] == 'Comments' and rule['Property ID'] != 'N/A':
            errors.append(f'{rid}: comment property ID is not applicable')
        linked = [s for s in steps if s['Rule ID'] == rid]
        if not 1 <= len(linked) <= 8 or [s['Step'] for s in linked] != [str(i+1) for i in range(len(linked))]:
            errors.append(f'{rid}: requires 1-8 contiguous ordered steps')
        for field, lower, upper in [('Cooldown seconds', 0, 86400), ('Expiry seconds', 1, 86400)]:
            value = rule[field]
            if not value.isdigit() or not lower <= int(value) <= upper:
                errors.append(f'{rid}: {field} needs a supported value or manual review')
    for step in steps:
        rid = step['Rule ID']
        if rid not in ids:
            errors.append(f'{rid}: orphan step')
        if step['Template mode'] == 'Fixed category' and step['Template category'] not in categories:
            errors.append(f'{rid}: fixed template category not in package')
        if step['Action'] == 'Switch template' and step['Switch trigger'] != 'N/A':
            errors.append(f'{rid}: standalone switch has no speech trigger')
        if step['Action'] == 'Generate reply' and any(step[f] in ('EMPTY', 'N/A') for f in ('Text or prompt', 'Spoken language')):
            errors.append(f'{rid}: reply needs instruction and spoken language')
    return tables, errors


def check(root):
    root = Path(root)
    errors, fingerprints, categories = [], {}, set()
    required = ['Soul.md', 'Agents.md', 'LiveScript.md',
                'LiveScript_Nonempty_Line_Index.md', 'Media_Resources_and_Pending_Checks.md']
    files = {p.name.casefold(): p for p in root.glob('*.md')}
    texts = {}
    for name in required:
        p = files.get(name.casefold())
        if not p:
            errors.append(f'missing {name}')
            continue
        raw = p.read_bytes()
        texts[name] = raw.decode('utf-8-sig')
        fingerprints[name] = hashlib.sha256(raw).hexdigest()
    for p in root.glob('video_template_*.md'):
        raw = p.read_bytes()
        match = re.search(r'^video_template_category:\s*(\S+)\s*$', raw.decode('utf-8-sig'), re.M)
        if not match:
            errors.append(f'{p.name}: missing category')
        elif match[1] in categories:
            errors.append(f'{p.name}: duplicate category')
        else:
            categories.add(match[1])
        fingerprints[p.name] = hashlib.sha256(raw).hexdigest()
    text = texts.get('Media_Resources_and_Pending_Checks.md', '')
    tables, issues = validate_tables(text, categories)
    errors.extend(issues)
    return {'status': 'REVIEW' if errors else 'OK', 'errors': errors,
            'rules': len(tables.get('rules', [])), 'steps': len(tables.get('steps', [])),
            'template_categories': sorted(categories), 'sha256': fingerprints,
            'scope': 'Structure only; no semantic, bilingual, script-range or platform verification.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    args = parser.parse_args()
    try:
        result = check(args.package)
    except (OSError, UnicodeError) as exc:
        result = {'status': 'ERROR', 'errors': [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'OK' else 1


if __name__ == '__main__':
    raise SystemExit(main())
