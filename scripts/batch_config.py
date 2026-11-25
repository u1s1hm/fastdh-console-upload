"""Offline batch merge/validation. No browser, network, credentials or source writes."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import uuid


class Review(ValueError):
    pass


def pointer(path, key):
    return path + '/' + str(key).replace('~', '~0').replace('/', '~1')


def element_id(scenario_id, unit_id):
    """Candidate for NEW schema-v2 elements only; reuse existing bindings first."""
    if not scenario_id or not unit_id:
        raise Review('scenario and stable source unit required')
    return 'lpe_' + uuid.uuid5(uuid.NAMESPACE_URL,
                             json.dumps([scenario_id, unit_id], ensure_ascii=False)).hex


def identified(items, path):
    result = {}
    for item in items:
        if isinstance(item, dict) and 'id' in item:
            ident = item['id']
            if not isinstance(ident, str) or not ident or ident in result:
                raise Review(path + ': empty/duplicate/invalid ID')
            result[ident] = item
    return result


def merge(base, changes, replace_arrays, delete_ids, path=''):
    if isinstance(base, dict) and isinstance(changes, dict):
        result = deepcopy(base)
        for key, value in changes.items():
            result[key] = merge(base.get(key), value, replace_arrays, delete_ids,
                                pointer(path, key))
        return result
    if isinstance(changes, dict):
        return merge({}, changes, replace_arrays, delete_ids, path)
    if isinstance(base, dict):
        raise Review(path + ': object cannot become a scalar')
    if isinstance(changes, list):
        if path not in replace_arrays:
            raise Review(path + ': array replacement must be explicit')
        old = identified(base, path) if isinstance(base, list) else {}
        new = identified(changes, path)
        if set(old) - set(new) - set(delete_ids):
            raise Review(path + ': existing IDs would be removed without explicit scope')
        # Preserve unknown fields on retained identified objects, including nested values.
        return [merge(old[item['id']], item, replace_arrays, delete_ids,
                      pointer(path, i)) if isinstance(item, dict) and item.get('id') in old
                else merge(None, item, replace_arrays, delete_ids, pointer(path, i))
                for i, item in enumerate(changes)]
    if isinstance(base, list):
        raise Review(path + ': use an explicit array replacement, not a scalar/null')
    return deepcopy(changes)


def differences(expected, actual, path='', subset=False):
    """Return paths, never values. Subset is used only at config's top level."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        keys = set(expected) if subset else set(expected) | set(actual)
        result = []
        for key in sorted(keys):
            child = pointer(path, key)
            if key not in expected or key not in actual:
                result.append(child)
            else:
                result.extend(differences(expected[key], actual[key], child))
        return result
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return [path]
        return [p for i, (a, b) in enumerate(zip(expected, actual))
                for p in differences(a, b, pointer(path, i))]
    if isinstance(expected, str) and isinstance(actual, str):
        if path in ('/live_script_md', '/soul_md', '/agents_md'):
            expected, actual = expected.replace('\r\n', '\n'), actual.replace('\r\n', '\n')
    return [] if type(expected) is type(actual) and expected == actual else [path or '/']


def validate(config, checks):
    issues = []
    programme = config.get('live_programme')
    if programme is not None:
        if not isinstance(programme, dict) or programme.get('schema_version') != '2':
            raise Review('live_programme: only observed schema_version "2" is checked')
        elements = programme.get('elements')
        if not isinstance(elements, list):
            raise Review('live_programme.elements must be an array')
        identified(elements, '/live_programme/elements')
        limit = checks.get('max_elements')
        if limit is not None and (type(limit) is not int or limit < 1):
            raise Review('max_elements needs current positive integer evidence or null')
        if limit is not None and len(elements) > limit:
            issues.append('programme exceeds supplied current limit')
        for i, item in enumerate(elements):
            path = f'/live_programme/elements/{i}'
            if not isinstance(item, dict):
                issues.append(path + ': object required')
                continue
            if not re.fullmatch(r'lpe_[a-f0-9]{32}', str(item.get('id', ''))):
                issues.append(path + ': invalid observed v2 element ID')
            category = item.get('template_category')
            if category and category not in checks.get('categories', []):
                issues.append(path + ': category absent from confirmed package mapping')
            start, end = item.get('line_start'), item.get('line_end')
            if start not in (None, 0) or end not in (None, 0):
                if type(start) is not int or type(end) is not int or not 1 <= start <= end:
                    issues.append(path + ': invalid nonempty line range')
                else:
                    allowed = set(checks.get('spoken_lines', []))
                    if end - start + 1 > len(allowed) or any(n not in allowed for n in range(start, end + 1)):
                        issues.append(path + ': range contains unapproved/note lines')
    rules = config.get('interaction_workflows', [])
    if not isinstance(rules, list):
        raise Review('interaction_workflows must be an array')
    identified(rules, '/interaction_workflows')
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict) or type(rule.get('enabled')) is not bool:
            issues.append(f'/interaction_workflows/{i}: object and enabled boolean required')
            continue
        steps = rule.get('steps')
        if not isinstance(steps, list) or not 1 <= len(steps) <= 8:
            issues.append(f'/interaction_workflows/{i}: requires 1-8 ordered steps')
    return issues


def identity(snapshot, target):
    if (set(target) != {'agent_id', 'scenario_id'}
            or not all(isinstance(v, str) and v for v in target.values())
            or snapshot.get('target') != target):
        raise Review('target identity mismatch or missing actual IDs')
    if not isinstance(snapshot.get('config'), dict):
        raise Review('config object required')


def prepare(data):
    target, base, current = data['target'], data['baseline'], data['current']
    identity(base, target)
    identity(current, target)
    if not base.get('revision') or not current.get('revision'):
        raise Review('fresh baseline/current revision required')
    if base['revision'] != current['revision'] or base['config'] != current['config']:
        raise Review('baseline changed: re-read and rebase before submitting')
    if not isinstance(data['changes'], dict):
        raise Review('changes must be an object')
    config = merge(base['config'], data['changes'], data.get('replace_arrays', []),
                   data.get('delete_ids', []))
    issues = validate(config, data.get('checks', {}))
    if issues:
        return {'status': 'REVIEW', 'issues': issues}
    paths = differences(base['config'], config)
    return {'status': 'OK', 'target': target, 'revision': current['revision'],
            'changed_paths': paths, 'save_needed': bool(paths), 'config': config,
            'scope': 'Local merge and selected invariants only; server/schema/readback still required.'}


def compare(expected, actual):
    identity(expected, expected['target'])
    identity(actual, expected['target'])
    paths = differences(expected['config'], actual['config'], subset=True)
    return {'status': 'REVIEW' if paths else 'OK', 'different_paths': paths,
            'scope': 'Provided config scope only; not proof of server origin or live behaviour.'}


def recovery_action(expected, observed, state):
    """Offline decision aid: unknown/failed observations never authorize blind retry."""
    if state == 'processing':
        return 'wait_existing_job'
    if state == 'saved' and observed is not None:
        return 'skip' if expected == observed else 'rebase'
    if state == 'confirmed_absent':
        return 'retry_in_authorized_scope'
    return 'readback_required'


def load(path):
    def reject_constant(value):
        raise Review('nonfinite JSON number: ' + value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_constant=reject_constant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('prepare').add_argument('input')
    cmp = sub.add_parser('compare')
    cmp.add_argument('expected')
    cmp.add_argument('actual')
    sub.add_parser('recover').add_argument('input')
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            result = prepare(load(args.input))
        elif args.command == 'compare':
            result = compare(load(args.expected), load(args.actual))
        else:
            data = load(args.input)
            result = {'status': 'OK', 'action': recovery_action(
                data['expected'], data.get('observed'), data['state']),
                'scope': 'Decision from supplied evidence only; performs no retry or write.'}
    except (Review, OSError, ValueError, KeyError, TypeError) as exc:
        result = {'status': 'REVIEW', 'issues': [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result['status'] == 'OK' else 1


if __name__ == '__main__':
    raise SystemExit(main())
