import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('preparation',Path(__file__).resolve().parents[1]/'agent-workflow/scripts/prepare-dashboard-migration.py')
preparation=importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparation)


class PreparationTests(unittest.TestCase):
    def test_lossless_snapshot_dedupes_symlink_projects_and_never_changes_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'My'; home=root/'agent-workflow/firstmate'
            (root/'data').mkdir(parents=True)
            (home/'data').mkdir(parents=True)
            (home/'projects').mkdir()
            (home/'projects/My').symlink_to(root,target_is_directory=True)
            (home/'projects/Extra').mkdir()
            other=Path(tmp)/'personal'; other.mkdir()
            (home/'data/projects.md').write_text('- My [local-only] - Main\n- Extra [local-only] - Extra\n')
            (home/'data/captain.md').write_text('Existing preferences\n')
            workspace={'projects':[{'id':'p','path':str(root),'title':'Alias','custom':[1]},
                                   {'id':'q','path':str(other),'title':'Personal'}],
                       'tasks':[{'id':'same','title':'Task','status':'done','notes':'Keep all fields'}],
                       'reminders':[{'id':'same','title':'Reminder','due':None}], 'focus':'unrelated'}
            raw=json.dumps(workspace,ensure_ascii=False).encode()
            (root/'data/todos.json').write_bytes(raw)
            output=Path(tmp)/'prepared'
            result=preparation.prepare(root,output)
            self.assertEqual(result['project_links'],{'p':'My'})
            self.assertEqual(result['unmatched_dashboard_project_ids'],['q'])
            self.assertEqual(result['firstmate_only_projects'],['Extra'])
            self.assertEqual((root/'data/todos.json').read_bytes(),raw)
            self.assertEqual((output/'snapshot/data/todos.json').read_bytes(),raw)
            self.assertEqual((home/'data/captain.md').read_text(),'Existing preferences\n')
            self.assertEqual((output.stat().st_mode & 0o777),0o700)
            with self.assertRaises(ValueError): preparation.prepare(root,output)

    def test_ambiguous_registry_matches_and_duplicate_ids_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp); (home/'projects').mkdir()
            (home/'projects/One').mkdir()
            (home/'projects/Two').symlink_to(home/'projects/One',target_is_directory=True)
            w={'projects':[{'id':'p','path':str(home/'projects/One')}],'tasks':[],'reminders':[]}
            with self.assertRaises(ValueError):
                preparation.reconcile(w,'- One [local-only] - One\n- Two [local-only] - Two\n',home)
            w['tasks']=[{'id':'a'},{'id':'a'}]
            with self.assertRaises(ValueError): preparation.reconcile(w,'',home)


if __name__=='__main__': unittest.main()
