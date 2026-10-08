#!/usr/bin/env python3
"""Migrate into Pi's normal Firstmate context without touching its running session.

Requires the dashboard to be stopped. Defaults to read-only preparation; --apply
backs up, verifies the new owner, binds the dashboard, then empties only migrated
arrays in the old JSON. Never runs Firstmate commands or signals its processes.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from firstmate_context import ContextStore, atomic_write, parse_context, render_context
spec=importlib.util.spec_from_file_location('prepare',Path(__file__).with_name('prepare-dashboard-migration.py'))
prepare=importlib.util.module_from_spec(spec); spec.loader.exec_module(prepare)


def require_dashboard_stopped():
    with socket.socket() as sock:
        sock.settimeout(1)
        if sock.connect_ex(('127.0.0.1',8765))==0:
            raise RuntimeError('Stop only the idle dashboard before migration; leave Firstmate running')


def migrate(root, stopped_check=require_dashboard_stopped):
    root=Path(root).resolve(); home=root/'agent-workflow/firstmate'
    stopped_check()
    if (Path.home()/'.pi/agent/APPEND_SYSTEM.md').exists():
        raise RuntimeError('A global append-system prompt exists; reconcile it before creating a project prompt')
    store=ContextStore(home)
    if store.path.exists() or (root/'data/.firstmate-context.json').exists():
        raise RuntimeError('Context or migration binding already exists; inspect rather than repeat migration')
    if not (root/'agent-workflow/integrations/personal-context/extension.ts').is_file():
        raise RuntimeError('Install the tested personal-context implementation first')
    backup=root/'agent-workflow/archives'/('personal-context-migration-'+str(time.time_ns()))
    plan=prepare.prepare(root,backup)
    source=root/'data/todos.json'; settings=home/'.pi/settings.json'
    exclude_name=subprocess.check_output(['git','-C',str(home),'rev-parse','--git-path','info/exclude'],text=True).strip()
    exclude=Path(exclude_name) if Path(exclude_name).is_absolute() else home/exclude_name
    before_exclude=exclude.read_bytes() if exclude.exists() else None
    (backup/'exclude-before').write_bytes(before_exclude or b'')
    original=source.read_bytes(); workspace=json.loads(original)
    before_settings=settings.read_bytes() if settings.exists() else None
    config=json.loads(before_settings) if before_settings else {}
    extensions=config.setdefault('extensions',[])
    if not isinstance(extensions,list): raise ValueError('Invalid Pi extensions setting')
    old='../../integrations/my-dashboard/extension.ts'
    new='../../integrations/personal-context/extension.ts'
    config['extensions']=[p for p in extensions if p!=old]
    if new not in config['extensions']: config['extensions'].append(new)
    payload={'schema':1,'workspace':{k:workspace[k] for k in ('projects','tasks','reminders')},
             'project_links':plan['project_links']}
    marker=root/'data/.firstmate-context.json'
    written=[]
    try:
        with store.locked():
            stopped_check()
            for name,expected in plan['source_hashes'].items():
                path=Path(name)
                actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
                if actual!=expected: raise RuntimeError(f'Source changed during migration: {path}')
            if (exclude.read_bytes() if exclude.exists() else None)!=before_exclude:
                raise RuntimeError('Local Git exclusions changed during preparation')
            text=render_context(payload)
            # Exclusive creation: never replace an existing Firstmate context.
            with store.path.open('x',encoding='utf-8') as stream:
                written.append(store.path)
                stream.write(text); stream.flush(); os.fsync(stream.fileno())
            store.path.chmod(0o600)
            verified,_=parse_context(store.path.read_text())
            if verified!=payload: raise RuntimeError('Destination verification failed')
            projected=store._snapshot_unlocked()['workspace']
            for kind in ('projects','tasks','reminders'):
                by_id={item['id']:item for item in projected[kind]}
                if any(by_id.get(item['id'])!=item for item in workspace[kind]):
                    raise RuntimeError('Projected records did not preserve every field')
            atomic_write(settings,json.dumps(config,indent=2)+'\n'); written.append(settings)
            ignored=(before_exclude or b'').decode()
            for entry in ('/.pi/APPEND_SYSTEM.md','/.pi/.personal-context.lock'):
                if entry not in ignored.splitlines(): ignored+='\n'+entry+'\n'
            atomic_write(exclude,ignored); written.append(exclude)
            atomic_write(marker,json.dumps({'schema':1,'home':'../agent-workflow/firstmate'})+'\n'); written.append(marker)
            # Only after the new owner and projected fields have been verified.
            if source.read_bytes()!=original: raise RuntimeError('Old dashboard source changed; refusing cleanup')
            if hashlib.sha256(store.registry.read_bytes()).hexdigest()!=plan['source_hashes'][str(store.registry)]:
                raise RuntimeError('Firstmate registry changed; refusing cleanup')
            remaining={**workspace,'projects':[],'tasks':[],'reminders':[]}
            atomic_write(source,json.dumps(remaining,ensure_ascii=False,indent=2)+'\n'); written.append(source)
            plan.update(status='migrated',destination=str(store.path),source_cleanup='only projects/tasks/reminders arrays emptied',
                        destination_sha256=hashlib.sha256(store.path.read_bytes()).hexdigest(),
                        projection_counts={k:len(projected[k]) for k in ('projects','tasks','reminders')},
                        firstmate_session_reloaded=False)
            atomic_write(backup/'manifest.json',json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    except Exception:
        # This migration runs with the dashboard stopped and context locked.
        # Never restore registry, captain preferences, backlog, or runtime state.
        if source in written: atomic_write(source,original.decode())
        if settings in written:
            if before_settings is None: settings.unlink()
            else: atomic_write(settings,before_settings.decode())
        if exclude in written:
            if before_exclude is None: exclude.unlink()
            else: atomic_write(exclude,before_exclude.decode())
        if marker in written: marker.unlink(missing_ok=True)
        if store.path in written: store.path.unlink(missing_ok=True)
        raise
    return {'backup':str(backup),'status':plan['status'],'counts':plan['counts'],
            'projection_counts':plan['projection_counts'],'project_links':plan['project_links'],
            'firstmate_reloaded':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--my-root',default=str(ROOT))
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if not args.apply: parser.error('Use prepare-dashboard-migration.py for a read-only bundle; --apply requires the dashboard stopped')
    print(json.dumps(migrate(args.my_root),ensure_ascii=False,indent=2))
