import json
import pathlib
import subprocess
import tempfile
import unittest
from observstory.workspace import errors, publish

class WorkspaceTest(unittest.TestCase):
    def declaration(self):
        return {"schema":"observstory.workspace/v1","records":[{"id":"research","title":"Undated research","kind":"research"}],"relations":[]}

    def test_rejects_unknown_fields_duplicate_ids_and_dangling_relations(self):
        d=self.declaration()
        self.assertEqual(errors(d), [])
        d['records'][0]['owner']='invented'
        self.assertTrue(errors(d))
        del d['records'][0]['owner']
        d['records']*=2
        self.assertTrue(errors(d))
        d=self.declaration(); d['relations']=[{'from':'research','to':'missing','type':'supports'}]
        self.assertTrue(errors(d))

    def test_git_projection_ignores_dirty_working_tree_and_retains_revision(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp); subprocess.run(['git','init','-q',temp],check=True)
            (root/'.observstory').mkdir(); p=root/'.observstory/workspace.json'; p.write_text(json.dumps(self.declaration()))
            subprocess.run(['git','-C',temp,'add','.'],check=True)
            subprocess.run(['git','-C',temp,'-c','user.name=Test','-c','user.email=test@example.com','commit','-qm','test'],check=True)
            p.write_text('{broken')
            publish(root,'HEAD',root/'out')
            data=json.loads((root/'out/data/workspace.json').read_text())
            self.assertEqual(data['records'][0]['kind'],'research')
            self.assertEqual(len(data['source_commit']),40)

    def test_coarse_dates_are_not_silently_made_precise(self):
        d=self.declaration();d['records'][0]['planned']={'start':'2026-11','precision':'day'}
        self.assertTrue(errors(d))
