#!/usr/bin/env python3
"""Agent CLI for the local Studio API. Decisions belong to the tailnet UI."""

import argparse
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from server import load_config


def request(base, route, method='GET', body=None):
    data = None if body is None else json.dumps(body).encode()
    req = Request(base.rstrip('/') + '/api/' + route, data=data, method=method,
                  headers={'Content-Type': 'application/json', 'X-Peak-Mind-Studio': '1'})
    try:
        with urlopen(req, timeout=40) as response:
            return json.load(response)
    except HTTPError as exc:
        try:
            detail = json.load(exc).get('error', exc.reason)
        except (ValueError, AttributeError):
            detail = exc.reason
        raise ValueError(f'HTTP {exc.code}: {detail}') from exc
    except URLError as exc:
        raise ValueError(f'Cannot reach Studio at {base}: {exc.reason}') from exc


def read_json(value):
    if value.lstrip().startswith('{'):
        return json.loads(value)
    return json.loads(Path(value).expanduser().read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', help='Config JSON path')
    parser.add_argument('--base-url', default=os.environ.get('PEAK_MIND_STUDIO_URL'))
    parser.add_argument('--collection', choices=('episodes', 'ideas'), default='episodes')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list')
    commands.add_parser('get').add_argument('id')
    for command in ('patch', 'put-review', 'set-status'):
        sub = commands.add_parser(command)
        sub.add_argument('id')
        sub.add_argument('value')
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        base = args.base_url or config.get('baseUrl') or f'http://127.0.0.1:{config["port"]}'
        if args.command == 'list':
            result = request(base, 'state')[args.collection]
        else:
            route = args.collection + '/' + quote(args.id, safe='')
            current = request(base, route)
            if args.command == 'get':
                result = current
            else:
                if args.command == 'patch':
                    fields = read_json(args.value)
                elif args.command == 'put-review':
                    if args.collection != 'episodes':
                        raise ValueError('put-review is only for episodes')
                    fields = {'review': read_json(args.value), 'status': 'review'}
                else:
                    fields = {'status': args.value}
                if not isinstance(fields, dict):
                    raise ValueError('Patch must be a JSON object')
                result = request(base, route, 'PATCH', {**fields, 'ifVersion': current['version']})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError) as exc:
        print(f'studioctl: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
