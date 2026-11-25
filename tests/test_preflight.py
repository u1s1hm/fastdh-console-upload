import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('preflight', ROOT/'scripts/preflight.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def table(header, rows):
    return '\n'.join(['| '+' | '.join(header)+' |', '| '+' | '.join(['---']*len(header))+' |'] +
                     ['| '+' | '.join(row)+' |' for row in rows])


def sample():
    rule = ['R01','1','指定模板','true','Comments','111','substring','N/A','EMPTY','EMPTY',
            'After current speech','Resume previous content','Abort remaining steps','0',
            'Per session','60','Synthetic test']
    step = ['R01','1','Switch template','N/A','N/A','N/A','N/A','Fixed category','test_base',
            'true','N/A','Synthetic test']
    return rule, step


class Preflight(unittest.TestCase):
    def test_complete_package_read_only(self):
        r, s = sample()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            for name in ('Soul.md','Agents.md','LiveScript.md','LiveScript_Nonempty_Line_Index.md'):
                (p/name).write_text('Synthetic content', encoding='utf-8')
            (p/'Media_Resources_and_Pending_Checks.md').write_text(table(m.RULE,[r])+'\n\n'+table(m.STEP,[s]), encoding='utf-8')
            (p/'video_template_1.md').write_text('video_template_category: test_base\n',encoding='utf-8')
            before = {f.name:f.read_bytes() for f in p.iterdir()}
            self.assertEqual(m.check(p)['status'],'OK')
            self.assertEqual(before,{f.name:f.read_bytes() for f in p.iterdir()})

    def test_zero_rules(self):
        self.assertEqual(m.validate_tables(table(m.RULE,[])+'\n\n'+table(m.STEP,[]),set())[1],[])

    def test_explicit_no_expiry_distinct_from_missing(self):
        r,s=sample(); r[m.RULE.index('Expiry seconds')]='EMPTY'
        self.assertEqual(m.validate_tables(table(m.RULE,[r])+'\n\n'+table(m.STEP,[s]),{'test_base'})[1],[])
        r[m.RULE.index('Expiry seconds')]=''
        self.assertTrue(m.validate_tables(table(m.RULE,[r])+'\n\n'+table(m.STEP,[s]),{'test_base'})[1])

    def test_bad_steps(self):
        for field, value in [('Rule ID','R99'),('Switch trigger','Before this speech'),
                             ('Template category','missing'),('Step','2')]:
            with self.subTest(field=field):
                r,s=sample(); s[m.STEP.index(field)]=value
                self.assertTrue(m.validate_tables(table(m.RULE,[r])+'\n\n'+table(m.STEP,[s]),{'test_base'})[1])

    def test_missing_tables_legacy_review(self):
        self.assertTrue(m.validate_tables('Existing narrative only',set())[1])

    def test_pending_disabled_and_missing(self):
        for field,value in [('Expiry seconds','PENDING: empty semantics'),('Enabled','false'),('Timing','')]:
            r,s=sample(); r[m.RULE.index(field)]=value
            self.assertTrue(m.validate_tables(table(m.RULE,[r])+'\n\n'+table(m.STEP,[s]),{'test_base'})[1])

    def test_reply_requires_real_prompt(self):
        r,s=sample(); s[m.STEP.index('Action')]='Generate reply'
        s[m.STEP.index('Spoken language')]='English'
        self.assertTrue(m.validate_tables(table(m.RULE,[r])+'\n\n'+table(m.STEP,[s]),{'test_base'})[1])


if __name__ == '__main__': unittest.main()
