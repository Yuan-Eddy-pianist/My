import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
from agenda_fixture import reply

import serve
from firstmate_context import ContextStore,ContextConflict,ContextError,render_context,parse_context

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('migration',ROOT/'agent-workflow/scripts/migrate-dashboard-context.py')
migration=importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)


class PersonalContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name).resolve()
        self.home=self.root/'agent-workflow/firstmate'
        (self.home/'.pi').mkdir(parents=True); (self.home/'data').mkdir()
        (self.home/'projects').mkdir(); (self.home/'projects/My').symlink_to(self.root,target_is_directory=True)
        (self.home/'projects/Extra').mkdir()
        (self.home/'data/projects.md').write_text('- My [local-only] - Existing project\n- Extra [local-only] - Registry only\n')
        (self.home/'data/captain.md').write_text('Keep preferences unchanged\n')
        (self.home/'AGENTS.md').write_text('Fixture')
        subprocess.run(['git','init','-q',str(self.home)],check=True)
        (self.home/'.pi/settings.json').write_text(json.dumps({'extensions':['other.ts','../../integrations/my-dashboard/extension.ts'],'other':True}))
        integration=self.root/'agent-workflow/integrations/personal-context'
        integration.mkdir(parents=True)
        (integration/'extension.ts').write_bytes((ROOT/'agent-workflow/integrations/personal-context/extension.ts').read_bytes())
        (integration/'client.py').write_bytes((ROOT/'agent-workflow/integrations/personal-context/client.py').read_bytes())
        for name in ('firstmate_context.py','personal_records.py'):
            (self.root/name).write_bytes((ROOT/name).read_bytes())
        self.data={'projects':[{'id':'p','title':'My alias','path':str(self.root),'status':'active','goal':'Goal','progress':'Past','created':'before','updated':'before','unknown':{'keep':1}}],
                   'tasks':[{'id':'t','title':'Task','status':'open','due':None,'created':'before','notes':'note','extra':True}],
                   'reminders':[{'id':'r','title':'Legacy reminder','due':None,'status':'open','created':'before','notes':''}],
                   'focusHistory':[1,2]}
        (self.root/'data').mkdir()
        (self.root/'data/todos.json').write_text(json.dumps(self.data))
        self.original={k:getattr(serve,k) for k in ('DATA','INBOX','INBOX_PENDING','ARCHIVE','STATUS','PROGRESS_STATE')}
        serve.DATA=self.root/'data'; self.legacy_path=serve.DATA/'todos.json'
        for name,file in [('INBOX','inbox.md'),('INBOX_PENDING','.inbox-pending.md'),('ARCHIVE','inbox-archive.md'),('STATUS','.agent-status.json'),('PROGRESS_STATE','.project-progress.json')]: setattr(serve,name,serve.DATA/file)
        serve._workspace_agent_active=False
        serve.atomic_write(serve.INBOX,serve.INBOX_HEADER+'\n## Note\n\nfinish the task\n')
        serve.atomic_write(serve.ARCHIVE,'# Inbox archive\n')
        self.store=ContextStore(self.home)

    def tearDown(self):
        for k,v in self.original.items(): setattr(serve,k,v)
        serve._workspace_agent_active=False
        self.tmp.cleanup()

    def migrate(self):
        return migration.migrate(self.root,stopped_check=lambda:None)

    def test_migration_preserves_fields_and_old_unrelated_data_and_registrations(self):
        registry=(self.home/'data/projects.md').read_bytes()
        prefs=(self.home/'data/captain.md').read_bytes()
        result=self.migrate()
        self.assertEqual(result['counts'],{'projects':1,'tasks':1,'reminders':1})
        self.assertEqual(result['projection_counts']['projects'],2)
        payload,_=parse_context(self.store.path.read_text())
        self.assertEqual(payload['workspace'],{k:self.data[k] for k in ('projects','tasks','reminders')})
        self.assertEqual(payload['project_links'],{'p':'My'})
        self.assertEqual(json.loads(self.legacy_path.read_text()),{'projects':[],'tasks':[],'reminders':[],'focusHistory':[1,2]})
        self.assertEqual((self.home/'data/projects.md').read_bytes(),registry)
        self.assertEqual((self.home/'data/captain.md').read_bytes(),prefs)
        settings=json.loads((self.home/'.pi/settings.json').read_text())
        self.assertEqual(settings['extensions'],['other.ts','../../integrations/personal-context/extension.ts'])
        self.assertTrue(settings['other'])
        with self.assertRaises(RuntimeError): self.migrate()
        serve.ensure_data()
        self.assertEqual(json.loads(self.legacy_path.read_text())['tasks'],[])

    def test_mutations_are_shared_with_dashboard_and_do_not_need_server(self):
        self.migrate(); browser=serve.read_workspace_snapshot()
        self.store.apply([{'op':'update','collection':'tasks','id':'t','fields':{'status':'done'}}],browser['_version'],serve.now_iso())
        self.assertEqual(serve.read_workspace()['tasks'][0]['status'],'done')
        with self.assertRaises(serve.WorkspaceConflict): serve.update_workspace(browser,browser['_version'])
        current=serve.read_workspace_snapshot(); current['tasks'][0]['notes']='Browser changed this'
        serve.update_workspace(current,current['_version'])
        self.assertEqual(self.store.snapshot()['workspace']['tasks'][0]['notes'],'Browser changed this')
        self.assertEqual(json.loads(self.legacy_path.read_text())['tasks'],[])

    def test_http_browser_edits_use_context_and_legacy_store_stays_empty(self):
        from http.server import ThreadingHTTPServer
        from urllib.request import urlopen, Request
        from urllib.error import HTTPError
        self.migrate()
        server=ThreadingHTTPServer(('127.0.0.1',0),serve.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        url=f'http://127.0.0.1:{server.server_port}/api/workspace'
        try:
            with urlopen(url) as response: browser=json.load(response)
            self.assertEqual(browser['_owner'],'Firstmate')
            browser['tasks'][0]['status']='done'
            for project in browser['projects']: project['_pathOk']=True
            request=Request(url,data=json.dumps(browser).encode(),method='PUT',headers={'Content-Type':'application/json'})
            with urlopen(request) as response: self.assertTrue(json.load(response)['ok'])
            self.assertEqual(self.store.snapshot()['workspace']['tasks'][0]['status'],'done')
            payload,_=parse_context(self.store.path.read_text())
            self.assertEqual(len(payload['workspace']['projects']),1)
            self.assertEqual(json.loads(self.legacy_path.read_text())['tasks'],[])
            with self.assertRaises(HTTPError) as error: urlopen(request)
            self.assertEqual(error.exception.code,409)
            for method in ('GET','POST'):
                retired=Request(url.replace('/api/workspace','/api/dashboard'),method=method)
                with self.assertRaises(HTTPError) as error: urlopen(retired)
                self.assertEqual(error.exception.code,404)
            with urlopen(url.replace('/api/workspace','/api/todos')) as response:
                self.assertEqual(json.load(response)['tasks'],self.store.snapshot()['workspace']['tasks'])
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_missing_binding_never_reads_writes_or_recreates_legacy_store(self):
        self.migrate()
        snapshot=serve.read_workspace_snapshot()
        legacy=json.dumps({'projects':[],'tasks':[{'id':'legacy-only'}],'reminders':[]})
        self.legacy_path.write_text(legacy)
        (serve.DATA/'.firstmate-context.json').unlink()
        for action in (serve.read_workspace,serve.read_workspace_snapshot,serve.ensure_data,
                       lambda:serve.write_workspace(snapshot),
                       lambda:serve.update_workspace(snapshot,snapshot['_version'])):
            with self.assertRaises(serve.WorkspaceDataError): action()
        self.assertEqual(self.legacy_path.read_text(),legacy)

    def test_personal_record_crud_and_invalid_batch_preserve_unrelated_fields(self):
        self.migrate(); before=self.store.snapshot(); original=self.store.path.read_bytes()
        with self.assertRaises(ValueError):
            self.store.apply([
                {'op':'update','collection':'tasks','id':'t','fields':{'status':'done'}},
                {'op':'add','collection':'reminders','fields':{'title':'Invalid','due':'2026-02-30'}},
            ],before['version'],'now')
        self.assertEqual(self.store.path.read_bytes(),original)
        result=self.store.apply([
            {'op':'add','collection':'projects','fields':{'title':'Personal','path':'/tmp/personal-example'}},
            {'op':'add','collection':'tasks','fields':{'title':'New task'}},
            {'op':'add','collection':'reminders','fields':{'title':'New reminder','due':'2026-12-01'}},
        ],before['version'],'now')
        created=result['changes']
        result=self.store.apply([{'op':'update','collection':item['collection'],'id':item['id'],
                                 'fields':{'status':'done'}} for item in created],result['version'],'later')
        result=self.store.apply([{'op':'delete','collection':item['collection'],'id':item['id']} for item in created],
                                result['version'],'later')
        self.assertEqual(result['workspace'],before['workspace'])
        self.assertEqual(self.store.path.read_bytes(),original)

    def test_two_processes_share_the_same_lock_and_stale_version_fails(self):
        self.migrate(); version=self.store.snapshot()['version']
        code='''import sys,json
from firstmate_context import ContextStore,ContextConflict
s=ContextStore(sys.argv[1])
try:
 s.apply([{'op':'update','collection':'tasks','id':'t','fields':{'notes':sys.argv[3]}}],sys.argv[2],'now'); print('saved')
except ContextConflict: print('conflict')
'''
        processes=[subprocess.Popen(['python3','-c',code,str(self.home),version,str(i)],cwd=ROOT,stdout=subprocess.PIPE,text=True) for i in range(2)]
        self.assertEqual(sorted(p.communicate()[0].strip() for p in processes),['conflict','saved'])

    def test_failed_write_and_bad_records_never_replace_context(self):
        self.migrate(); snapshot=self.store.snapshot(); original=self.store.path.read_bytes()
        with patch('firstmate_context.os.replace',side_effect=OSError('disk failure')):
            with self.assertRaises(OSError): self.store.apply([{'op':'delete','collection':'tasks','id':'t'}],snapshot['version'],'now')
        self.assertEqual(self.store.path.read_bytes(),original)
        with self.assertRaises(ValueError): self.store.apply([{'op':'update','collection':'tasks','id':'t','fields':{'due':'2026-02-30'}}],snapshot['version'],'now')
        self.assertEqual(self.store.path.read_bytes(),original)
        self.store.path.write_text('corrupt')
        with self.assertRaises(serve.WorkspaceDataError): serve.read_workspace()

    def test_registered_projects_are_not_duplicated_and_metadata_is_editable(self):
        self.migrate(); snapshot=self.store.snapshot()
        result=self.store.apply([{'op':'update','collection':'projects','id':'fm:Extra','fields':{'status':'paused'}}],snapshot['version'],'now')
        self.assertEqual(len(result['workspace']['projects']),2)
        payload,_=parse_context(self.store.path.read_text())
        self.assertEqual(payload['project_links']['fm:Extra'],'Extra')
        with self.assertRaises(ValueError): self.store.apply([{'op':'delete','collection':'projects','id':'p'}],result['version'],'now')

    def voice_outbox(self):
        source = os.environ.get('MY_AGENDA_TEST_INBOX_ROOT')
        if not source:
            self.skipTest('Set MY_AGENDA_TEST_INBOX_ROOT for isolated inbox owner coverage')
        scripts = self.home / 'bin'
        scripts.mkdir(exist_ok=True)
        for name in ('fm-inbox.sh', 'fm-wake-lib.sh', 'fm-path-lib.sh'):
            (scripts / name).write_bytes((Path(source) / 'bin' / name).read_bytes())
        return serve.agenda_requests()

    def test_voice_handoff_waits_for_receiver_then_publishes_confirmed_outcome(self):
        self.migrate()
        before = self.store.snapshot()
        retained = {path: path.read_bytes() for path in (self.legacy_path, serve.INBOX, serve.ARCHIVE)}
        outbox = self.voice_outbox()
        transcript = '  确认完成 Task 这个待办。\n'
        with patch('serve.start_agenda_worker'):
            result = serve.append_inbox_and_process(transcript, identity='confirmed-task')
        self.assertEqual(result['request']['state'], 'delivery_pending')
        self.assertEqual(result['text'], transcript)
        self.assertEqual(self.store.snapshot(), before)
        outbox.tick()  # Actual inbox owner, entirely inside this temporary home.
        pending = outbox.snapshot()['requests'][0]
        self.assertEqual(pending['state'], 'pending')
        self.assertEqual(pending['transcript'], transcript)
        self.assertEqual(self.store.snapshot(), before)

        # Synthetic primary: existing tools confirm the requested personal-task deletion.
        applied = self.store.apply([{'op': 'delete', 'collection': 'tasks', 'id': 't'}],
                                   before['version'], 'now')
        self.assertEqual(applied['workspace']['tasks'], [])
        self.assertEqual(applied['workspace']['projects'], before['workspace']['projects'])
        self.assertEqual(applied['workspace']['reminders'], before['workspace']['reminders'])
        reply(outbox, 'confirmed-task', summary='已删除确认完成的待办；项目保留。')
        outbox.tick()
        self.assertEqual(outbox.snapshot()['requests'][0]['state'], 'applied')
        with patch('serve.start_agenda_worker'):
            replay = serve.append_inbox_and_process(transcript, identity='confirmed-task')
        self.assertEqual(replay['request']['state'], 'applied')
        outbox.tick()
        self.assertEqual(self.store.snapshot()['version'], applied['version'])
        self.assertEqual(len(outbox.records()), 1)
        for path, original in retained.items():
            self.assertEqual(path.read_bytes(), original)  # No legacy archive/reset side effect.
        self.assertFalse(hasattr(serve, 'run_personal_inbox_agent'))

    def test_voice_receiver_conflict_retains_request_without_rolling_back_dashboard_edit(self):
        self.migrate()
        outbox = self.voice_outbox()
        transcript = '确认完成 Task 这个待办。'
        original_note = serve.INBOX.read_bytes()
        with patch('serve.start_agenda_worker'):
            serve.append_inbox_and_process(transcript, identity='conflicting-task')
        outbox.tick()
        receiver = self.store.snapshot()
        manual = copy.deepcopy(receiver['workspace'])
        manual['tasks'][0]['notes'] = 'Concurrent dashboard change'
        _, manual_version = serve.update_workspace({'tasks': manual['tasks']}, receiver['version'])
        with self.assertRaises(ContextConflict):
            self.store.apply([{'op': 'delete', 'collection': 'tasks', 'id': 't'}], receiver['version'], 'now')
        outbox.tick()
        self.assertEqual(outbox.snapshot()['requests'][0]['state'], 'pending')
        current = self.store.snapshot()
        self.assertEqual(current['version'], manual_version)
        self.assertEqual(current['workspace']['tasks'][0]['notes'], 'Concurrent dashboard change')
        self.assertEqual(current['workspace']['tasks'][0]['status'], 'open')
        self.assertEqual(current['workspace']['projects'], receiver['workspace']['projects'])

        # Fresh read/reconsider: clarify instead of deleting a now-changed target.
        reply(outbox, 'conflicting-task', outcome='clarification', summary='待办刚被修改，仍要删除吗？')
        outbox.tick()
        outcome = outbox.snapshot()['requests'][0]
        self.assertEqual(outcome['state'], 'clarification')
        self.assertEqual(outcome['transcript'], transcript)
        outbox.retry('conflicting-task')
        outbox.tick()
        self.assertEqual(self.store.snapshot()['version'], manual_version)
        self.assertEqual(serve.INBOX.read_bytes(), original_note)
        self.assertEqual(len(outbox.records()), 1)

    def test_migration_failure_restores_source_and_configuration(self):
        source=self.legacy_path.read_bytes(); settings=(self.home/'.pi/settings.json').read_bytes()
        original=migration.atomic_write
        def fail(path,text):
            if Path(path)==self.legacy_path: raise OSError('failed cleanup')
            return original(path,text)
        with patch.object(migration,'atomic_write',side_effect=fail):
            with self.assertRaises(OSError): self.migrate()
        self.assertEqual(self.legacy_path.read_bytes(),source)
        self.assertEqual((self.home/'.pi/settings.json').read_bytes(),settings)
        self.assertFalse(self.store.path.exists()); self.assertFalse((serve.DATA/'.firstmate-context.json').exists())

    @unittest.skipUnless(os.environ.get('PI_PACKAGE_DIR'),'Set PI_PACKAGE_DIR for real Pi loading')
    def test_pi_normally_loads_context_and_tools_edit_without_dashboard(self):
        self.migrate()
        # Use a separate clean resource home, not the user's live Pi settings.
        script='''
import {pathToFileURL} from 'node:url';
const base=process.env.PI_PACKAGE_DIR;
const {DefaultResourceLoader}=await import(pathToFileURL(base+'/dist/core/resource-loader.js'));
const loader=new DefaultResourceLoader({cwd:process.env.FIXTURE_HOME,agentDir:process.env.FIXTURE_HOME+'/empty-agent-dir',noExtensions:true,noSkills:true,noPromptTemplates:true,noThemes:true});
await loader.reload({resolveProjectTrust:async()=>true});
const context=loader.getAppendSystemPrompt().join('\\n');
if(!context.includes('Legacy reminder') || !context.includes('My alias')) throw new Error('Personal records were not automatically loaded');
const {loadExtensions}=await import(pathToFileURL(base+'/dist/core/extensions/loader.js'));
const result=await loadExtensions([process.env.FIXTURE_EXTENSION],process.env.FIXTURE_HOME);
if(result.errors.length) throw new Error(JSON.stringify(result.errors));
const tools=result.extensions[0].tools;
const before=JSON.parse((await tools.get('personal_context_read').definition.execute('read',{})).content[0].text);
await tools.get('personal_context_update').definition.execute('write',{version:before.version,operations:JSON.stringify([{op:'update',collection:'tasks',id:'t',fields:{notes:'Pi changed own context'}}])});
const refresh=await result.extensions[0].handlers.get('before_agent_start')[0]({},{});
if(!refresh.message.content.includes('Pi changed own context')) throw new Error('Changed context was not automatically refreshed');
if(await result.extensions[0].handlers.get('before_agent_start')[0]({},{}) !== undefined) throw new Error('Unchanged context was redundantly injected');
console.log('normal context loading and local tools passed');
'''
        result=subprocess.run(['node','--input-type=module','-'],input=script,text=True,capture_output=True,
                              env={**os.environ,'FIXTURE_HOME':str(self.home),'FIXTURE_EXTENSION':str(self.root/'agent-workflow/integrations/personal-context/extension.ts')})
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.store.snapshot()['workspace']['tasks'][0]['notes'],'Pi changed own context')


if __name__=='__main__': unittest.main()
