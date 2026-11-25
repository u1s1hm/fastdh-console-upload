from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('batch', ROOT/'scripts/batch_config.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def sample():
    target = {'agent_id': 'synthetic-agent', 'scenario_id': 'synthetic-scene'}
    base = {'target': target, 'revision': 'synthetic-rev-1', 'config': {
        'future_field': {'keep': True}, 'live_script_md': 'Hello.\n[Config note]\nGoodbye.',
        'live_programme': {'schema_version': '2', 'elements': []},
        'interaction_workflows': []}}
    return {'target': target, 'baseline': base, 'current': deepcopy(base),
            'changes': {}, 'replace_arrays': ['/live_programme/elements'],
            'checks': {'categories': ['test_base'], 'spoken_lines': [1, 3], 'max_elements': None}}


def programme(count):
    return [{'id': m.element_id('synthetic-scene', f'U{i:02}'), 'name': f'U{i:02}',
             'template_category': 'test_base', 'line_start': 1, 'line_end': 1}
            for i in range(1, count+1)]


class Batch(unittest.TestCase):
    def test_61_elements_one_payload_preserves_input_and_unknown_fields(self):
        data = sample()
        data['changes'] = {'live_programme': {'elements': programme(61)}}
        before = deepcopy(data)
        result = m.prepare(data)
        self.assertEqual(result['status'], 'OK')
        self.assertEqual(len(result['config']['live_programme']['elements']), 61)
        self.assertEqual(result['config']['future_field'], {'keep': True})
        self.assertEqual(data, before)

    def test_confirmed_old_limit_rejects_unknown_limit_does_not_invent_cap(self):
        data = sample()
        data['changes'] = {'live_programme': {'elements': programme(61)}}
        data['checks']['max_elements'] = 50
        self.assertEqual(m.prepare(data)['status'], 'REVIEW')
        data['checks']['max_elements'] = None
        self.assertEqual(m.prepare(data)['status'], 'OK')

    def test_invalid_id_note_range_category_and_duplicate(self):
        for field, value in [('id', 'bad_u06'), ('line_end', 2),
                             ('template_category', 'not_in_this_package')]:
            data = sample()
            items = programme(1)
            items[0][field] = value
            data['changes'] = {'live_programme': {'elements': items}}
            self.assertEqual(m.prepare(data)['status'], 'REVIEW', field)
        data = sample()
        data['changes'] = {'live_programme': {'elements': programme(1)*2}}
        with self.assertRaises(m.Review): m.prepare(data)

    def test_stable_new_id_and_existing_identity_reused(self):
        self.assertEqual(m.element_id('scene', 'U01'), m.element_id('scene', 'U01'))
        self.assertNotEqual(m.element_id('other-scene', 'U01'), m.element_id('scene', 'U01'))
        data = sample()
        old = programme(2)
        old[0]['future_flag'] = {'keep': 1}
        for snapshot in ('baseline', 'current'):
            data[snapshot]['config']['live_programme']['elements'] = deepcopy(old)
        data['changes'] = {'live_programme': {'elements': [
            {'id': old[1]['id'], 'name': 'Moved first'}, {'id': old[0]['id'], 'name': 'Moved last'}]}}
        result = m.prepare(data)['config']['live_programme']['elements']
        self.assertEqual([v['id'] for v in result], [old[1]['id'], old[0]['id']])
        self.assertEqual(result[1]['future_flag'], {'keep': 1})
        self.assertEqual(result[1]['template_category'], 'test_base')

    def test_explicit_array_and_delete_scope(self):
        data = sample()
        for snapshot in ('baseline', 'current'):
            data[snapshot]['config']['live_programme']['elements'] = programme(1)
        data['changes'] = {'live_programme': {'elements': []}}
        with self.assertRaises(m.Review): m.prepare(data)
        data['delete_ids'] = [programme(1)[0]['id']]
        self.assertEqual(m.prepare(data)['status'], 'OK')
        data['replace_arrays'] = []
        with self.assertRaises(m.Review): m.prepare(data)

    def test_parent_clear_cannot_bypass_array_preservation(self):
        data = sample()
        data['changes'] = {'live_programme': None}
        with self.assertRaises(m.Review): m.prepare(data)

    def test_refresh_wrong_agent_or_scenario_stops(self):
        for field in ('agent_id', 'scenario_id'):
            data = sample()
            data['current']['target'][field] = 'different'
            with self.assertRaises(m.Review): m.prepare(data)

    def test_revision_or_unversioned_config_change_stops(self):
        data = sample()
        data['current']['revision'] = 'new-rev'
        with self.assertRaises(m.Review): m.prepare(data)
        data = sample()
        data['current']['config']['future_field']['keep'] = False
        with self.assertRaises(m.Review): m.prepare(data)

    def test_noop_omission_and_explicit_null(self):
        data = sample()
        self.assertFalse(m.prepare(data)['save_needed'])
        data['changes'] = {'optional_field': None}
        result = m.prepare(data)
        self.assertIsNone(result['config']['optional_field'])
        self.assertEqual(result['config']['future_field'], {'keep': True})

    def test_zero_single_and_double_rules_render_as_actual_payload(self):
        for count in (0, 1, 2):
            data = sample()
            # Types/prompts are synthetic: this tests merge/order, not platform enums.
            rules = [{'id': f'R{i}', 'enabled': True, 'steps': [
                {'type': 'synthetic_action', 'prompt': f'Synthetic instruction {i}'}]}
                for i in range(count)]
            data['changes'] = {'interaction_workflows': rules}
            data['replace_arrays'] = ['/interaction_workflows'] + [
                f'/interaction_workflows/{i}/steps' for i in range(count)]
            result = json.loads(json.dumps(m.prepare(data)))
            self.assertEqual(result['status'], 'OK')
            self.assertEqual(result['config']['interaction_workflows'], rules)

    def test_readback_detects_uncommitted_fill_partial_save_and_order(self):
        expected = {'target': sample()['target'], 'config': {
            'live_script_md': 'First.\nLast.',
            'live_programme': {'schema_version': '2', 'elements': programme(2)}}}
        actual = deepcopy(expected)
        actual['config']['live_script_md'] = 'Old field value'
        self.assertEqual(m.compare(expected, actual)['different_paths'], ['/live_script_md'])
        actual = deepcopy(expected)
        actual['config']['live_programme']['elements'].reverse()
        self.assertEqual(m.compare(expected, actual)['status'], 'REVIEW')
        actual = deepcopy(expected)
        actual['config']['live_script_md'] = 'First.\r\nLast.'
        actual['config']['outside_review_scope'] = 1
        self.assertEqual(m.compare(expected, actual)['status'], 'OK')

    def test_compare_rejects_wrong_target_and_changed_prompt(self):
        expected = {'target': sample()['target'], 'config': {'prompt': 'Keep a natural pause.'}}
        actual = deepcopy(expected)
        actual['config']['prompt'] = 'Keep a pause.'
        result = m.compare(expected, actual)
        self.assertEqual(result['different_paths'], ['/prompt'])
        self.assertNotIn('natural', json.dumps(result))
        actual['target']['scenario_id'] = 'other'
        with self.assertRaises(m.Review): m.compare(expected, actual)

    def test_async_timeout_recovery_requires_evidence(self):
        expected = {'document_id': 'synthetic-doc', 'category': 'test_base'}
        cases = [('processing', None, 'wait_existing_job'),
                 ('timeout', None, 'readback_required'),
                 ('failed', None, 'readback_required'),
                 ('saved', deepcopy(expected), 'skip'),
                 ('saved', {'category': 'wrong'}, 'rebase'),
                 ('confirmed_absent', None, 'retry_in_authorized_scope')]
        for state, observed, action in cases:
            self.assertEqual(m.recovery_action(expected, observed, state), action)

    def test_recovery_cli_does_not_retry_unknown_submission(self):
        with tempfile.TemporaryDirectory() as d:
            evidence = Path(d)/'evidence.json'
            evidence.write_text(json.dumps({'expected': {'id': 'test-doc'},
                                           'observed': None, 'state': 'timeout'}), encoding='utf-8')
            proc = subprocess.run([sys.executable, str(ROOT/'scripts/batch_config.py'),
                                   'recover', str(evidence)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['action'], 'readback_required')

    def test_cli_prepares_and_compares_without_source_writes(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d)/'input.json'
            source.write_text(json.dumps(sample()), encoding='utf-8')
            before = source.read_bytes()
            proc = subprocess.run([sys.executable, str(ROOT/'scripts/batch_config.py'),
                                   'prepare', str(source)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            self.assertEqual(result['status'], 'OK')
            self.assertEqual(before, source.read_bytes())
            expected = Path(d)/'expected.json'
            expected.write_text(json.dumps(result), encoding='utf-8')
            proc = subprocess.run([sys.executable, str(ROOT/'scripts/batch_config.py'),
                                   'compare', str(expected), str(expected)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == '__main__':
    unittest.main()
