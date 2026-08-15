from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def main() -> int:
    parser=argparse.ArgumentParser(description='Arranca el backend independiente de Míster 93/94.')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--reload',action='store_true')
    args=parser.parse_args()
    cmd=[sys.executable,'-m','uvicorn','backend.app.football9394.webapp:app','--host',args.host,'--port',str(args.port)]
    if args.reload: cmd.append('--reload')
    print('Míster 93/94 API:',f'http://{args.host}:{args.port}/api/football9394/health')
    return subprocess.call(cmd,cwd=ROOT)

if __name__=='__main__': raise SystemExit(main())
