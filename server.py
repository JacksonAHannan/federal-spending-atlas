"""Serve the same static files published to GitHub Pages."""
import argparse
import http.server
import pathlib
from functools import partial
if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    root=pathlib.Path(__file__).resolve().parent/'dist'
    handler=partial(http.server.SimpleHTTPRequestHandler,directory=str(root))
    print(f'Federal Spending Atlas: http://localhost:{args.port}',flush=True)
    http.server.ThreadingHTTPServer(('127.0.0.1',args.port),handler).serve_forever()
