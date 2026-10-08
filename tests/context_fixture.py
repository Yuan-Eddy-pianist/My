"""Temporary Firstmate-owned context used by persistence and voice tests."""
import json
from firstmate_context import ContextStore,render_context


def create_context(root, workspace):
    home=root/'agent-workflow/firstmate'
    (home/'.pi').mkdir(parents=True)
    (home/'data').mkdir()
    (home/'data/projects.md').write_text('')
    data=root/'data'; data.mkdir(exist_ok=True)
    (data/'.firstmate-context.json').write_text(json.dumps({'schema':1,'home':'../agent-workflow/firstmate'}))
    store=ContextStore(home)
    store.path.write_text(render_context({'schema':1,'workspace':workspace,'project_links':{}}))
    return store
