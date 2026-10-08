#!/usr/bin/env python3
"""Read or edit Firstmate's local personal context without a dashboard server."""
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from firstmate_context import ContextStore


def main():
    store=ContextStore(ROOT/'agent-workflow/firstmate')
    action=sys.argv[1] if len(sys.argv)>1 else 'read'
    if action=='read': result=store.snapshot()
    elif action=='apply':
        payload=json.loads(sys.argv[2] if len(sys.argv)>2 else sys.stdin.read())
        result=store.apply(payload['operations'],payload['version'],datetime.now().astimezone().isoformat(timespec='seconds'))
    else: raise ValueError('Expected read or apply')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(str(exc),file=sys.stderr)
        sys.exit(1)
