#!/usr/bin/env python3
"""Local, dependency-free Peak Mind Studio API and static server."""

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
from urllib.parse import unquote, urlsplit

CONFIG_PATH = '~/.config/peak-mind-studio/config.json'
STATUSES = {'planning', 'recorded', 'editing', 'review', 'approved', 'published'}
STATIC = Path(__file__).resolve().parent / 'static'


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def load_config(path=None):
    config = {'dataDir': '~/peak-mind-studio/data', 'port': 5480, 't3Bin': 't3',
              'approvers': [], 'mediaRoots': {'kits': '~/Downloads/peak-mind-spotify'},
              'appDir': '~/peak-mind-studio/app',
              'launchAgent': '~/Library/LaunchAgents/com.peakmind.studio.plist',
              'logFile': '~/Library/Logs/peak-mind-studio.log', 'pythonBin': 'python3'}
    source = Path(path or os.environ.get('PEAK_MIND_STUDIO_CONFIG', CONFIG_PATH)).expanduser()
    if source.exists():
        values = json.loads(source.read_text())
        if not isinstance(values, dict):
            raise ValueError('Config must be a JSON object')
        config.update(values)
    config.setdefault('editors', config['approvers'])
    for key in ('approvers', 'editors'):
        if not isinstance(config[key], list) or not all(isinstance(x, str) for x in config[key]):
            raise ValueError(f'{key} must be a list of logins')
    if not isinstance(config['port'], int) or not 0 <= config['port'] <= 65535:
        raise ValueError('port must be an integer from 0 to 65535')
    if not isinstance(config['mediaRoots'], dict):
        raise ValueError('mediaRoots must be an object')
    for key in ('dataDir', 'appDir', 'launchAgent', 'logFile'):
        config[key] = str(Path(config[key]).expanduser().resolve())
    config['t3Bin'] = os.path.expanduser(config['t3Bin'])
    config['mediaRoots'] = {key: Path(value).expanduser().resolve()
                            for key, value in config['mediaRoots'].items()}
    config['configPath'] = str(source.resolve())
    return config


class APIError(Exception):
    def __init__(self, status, message, **details):
        self.status = status
        self.body = {'error': message, **details}
        super().__init__(message)


def validate_id(collection, doc_id):
    if collection not in ('episodes', 'ideas'):
        raise APIError(404, 'Unknown collection')
    pattern = r'\d{4}-\d{2}-\d{2}(?:-[1-9]\d*)?' if collection == 'episodes' else r'[a-z0-9]+(?:-[a-z0-9]+)*'
    if not re.fullmatch(pattern, doc_id) or len(doc_id) > 80:
        raise APIError(400, 'Invalid document id')
    if collection == 'episodes':
        try:
            dt.date.fromisoformat(doc_id[:10])
        except ValueError as exc:
            raise APIError(400, 'Invalid episode date') from exc


def validate_review(review):
    if not isinstance(review, dict):
        raise APIError(400, 'review must be an object')
    for key in ('t3ThreadId', 'title', 'conciseDescription', 'spotifyDescription', 'length'):
        if not isinstance(review.get(key), str) or not review[key].strip():
            raise APIError(400, f'review.{key} must be a nonempty string')
    if review['t3ThreadId'].startswith('-') or '\n' in review['t3ThreadId']:
        raise APIError(400, 'Invalid publishing thread id')
    if review.get('confidence') not in ('HIGH', 'LOW'):
        raise APIError(400, 'review.confidence must be HIGH or LOW')
    for key in ('titleAlternates', 'flags'):
        if not isinstance(review.get(key), list) or not all(isinstance(x, str) for x in review[key]):
            raise APIError(400, f'review.{key} must be a list of strings')
    for key, fields in (('start', ('at', 'cutLine', 'firstLine')), ('end', ('at', 'lastLine', 'cutLine'))):
        if not isinstance(review.get(key), dict) or not all(isinstance(review[key].get(f), str) for f in fields):
            raise APIError(400, f'review.{key} must include ' + ', '.join(fields))
    for key in ('covers', 'clips'):
        items = review.get(key)
        if not isinstance(items, list) or (key == 'covers' and not items):
            raise APIError(400, f'review.{key} must be a list' + (' with a cover' if key == 'covers' else ''))
        seen = set()
        for item in items:
            if not isinstance(item, dict) or not all(isinstance(item.get(f), str) and item[f] for f in ('id', 'label', 'media')):
                raise APIError(400, f'Invalid review.{key} item')
            if not re.fullmatch(r'[a-zA-Z0-9_-]+', item['id']) or item['id'] in seen:
                raise APIError(400, f'Invalid or duplicate review.{key} id')
            seen.add(item['id'])
            media = item['media']
            if '/' not in media or media.startswith('/') or any(x in ('', '.', '..') for x in media.split('/')) or '\\' in media:
                raise APIError(400, 'Media must be root/relative-path')
    if review.get('defaultCover') not in {c['id'] for c in review['covers']}:
        raise APIError(400, 'defaultCover must identify a cover')


def atomic_json(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(doc, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Store:
    def __init__(self, config):
        self.config = config
        self.root = Path(config['dataDir'])
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.mutex = threading.RLock()

    @contextlib.contextmanager
    def locked(self):
        # Also serializes the import command against a running server.
        with self.mutex, (self.root / '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def path(self, collection, doc_id):
        validate_id(collection, doc_id)
        return self.root / collection / (doc_id + '.json')

    def get(self, collection, doc_id):
        path = self.path(collection, doc_id)
        if not path.exists():
            raise APIError(404, 'Document not found')
        return json.loads(path.read_text())

    def state(self):
        state = {key: [json.loads(p.read_text()) for p in sorted((self.root / key).glob('*.json'))]
                 for key in ('episodes', 'ideas')}
        revision = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
        return {'revision': revision, **state}

    def save(self, collection, doc_id, body, old=None, delete=False):
        path = self.path(collection, doc_id)
        history = self.root / '.history' / collection / doc_id
        if old:
            previous = history / f"{old['version']}.json"
            if previous.exists():
                if json.loads(previous.read_text()) != old:
                    raise APIError(500, 'History collision, refusing to overwrite')
            else:
                atomic_json(previous, old)
        if delete:
            path.unlink()
            return {'deleted': doc_id}
        versions = [int(p.stem) for p in history.glob('*.json')]
        version = max([old['version'] if old else 0, *versions]) + 1
        doc = {**body, 'id': doc_id, 'version': version, 'updatedAt': now()}
        atomic_json(path, doc)
        return doc

    def recover_pending(self):
        # A stopped process may have sent the message but not confirmed delivery.
        with self.locked():
            for path in sorted((self.root / 'episodes').glob('*.json')):
                doc = self.get('episodes', path.stem)
                approval = doc.get('approval')
                if doc.get('status') == 'approved' and approval and not approval.get('delivered'):
                    approval = {**approval, 'deliveryError': 'Server restarted before delivery confirmation. Check T3 before retrying.'}
                    self.save('episodes', path.stem, {**doc, 'status': 'review', 'approval': approval}, doc)

    def import_dir(self, directory):
        result = []
        for collection in ('episodes', 'ideas'):
            for path in sorted((Path(directory).expanduser() / collection).glob('*.json')):
                with self.locked():
                    doc_id = path.stem
                    target = self.path(collection, doc_id)
                    if target.exists():
                        result.append(f'Skipped {collection}/{doc_id}: already exists')
                        continue
                    doc = json.loads(path.read_text())
                    if not isinstance(doc, dict):
                        raise ValueError(f'{path.name}: expected a JSON object')
                    # Exported prep is data, never executable markup. Imports cannot grant approval.
                    doc.pop('approval', None)
                    if doc.get('status') == 'approved':
                        doc['status'] = 'review'
                    self.save(collection, doc_id, doc)
                    result.append(f'Imported {collection}/{doc_id}')
        return result


class StudioHandler(BaseHTTPRequestHandler):
    server_version = 'PeakMindStudio/1'

    @property
    def store(self):
        return self.server.store

    def log_message(self, fmt, *args):
        # Do not log document contents, identities, or query strings.
        pass

    def identity(self):
        login = self.headers.get('Tailscale-User-Login', '').strip()
        name = unquote(self.headers.get('Tailscale-User-Name', login)).strip()
        local = not login
        return {'login': login or None, 'name': name or ('Local agent' if local else login),
                'canEdit': local or login in self.store.config['editors'],
                'canApprove': bool(login) and login in self.store.config['approvers'], 'local': local}

    def respond(self, status, body=None, headers=None):
        data = b'' if body is None else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if data:
            self.wfile.write(data)

    def body(self):
        if self.headers.get('X-Peak-Mind-Studio') != '1':
            raise APIError(403, 'X-Peak-Mind-Studio: 1 is required')
        if self.headers.get_content_type() != 'application/json':
            raise APIError(415, 'Content-Type: application/json is required')
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 <= size <= 8 * 1024 * 1024:
                raise APIError(413, 'Request body too large')
            data = json.loads(self.rfile.read(size) or b'{}', parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            if not isinstance(data, dict):
                raise ValueError('Expected object')
            return data
        except (ValueError, UnicodeError) as exc:
            raise APIError(400, 'Body must be a JSON object') from exc

    def check_version(self, body, old):
        value = body.get('ifVersion', self.headers.get('If-Match', '').strip('"'))
        if isinstance(value, bool) or str(value) != str(old['version']):
            raise APIError(409, 'Version conflict. Reload before saving.', currentVersion=old['version'])

    def do_GET(self):
        self.dispatch()

    def do_PUT(self):
        self.dispatch()

    def do_PATCH(self):
        self.dispatch()

    def do_DELETE(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch()

    def dispatch(self):
        try:
            path = unquote(urlsplit(self.path).path)
            if self.command == 'GET' and not path.startswith('/api/'):
                self.serve_file(path)
                return
            body = self.body() if self.command != 'GET' else None
            with self.store.locked():
                self.api(path, body)
        except APIError as exc:
            self.respond(exc.status, exc.body)
        except (OSError, ValueError, TypeError):
            self.respond(500, {'error': 'Storage or configuration error. Check the local files and logs.'})

    def api(self, path, body):
        method = self.command
        if method == 'GET' and path == '/api/me':
            return self.respond(200, self.identity())
        if method == 'GET' and path == '/api/state':
            state = self.store.state()
            etag = '"' + state['revision'] + '"'
            if self.headers.get('If-None-Match') == etag:
                return self.respond(304, headers={'ETag': etag})
            return self.respond(200, state, {'ETag': etag})
        match = re.fullmatch(r'/api/(episodes|ideas)/([^/]+)(?:/(approve|request-changes))?', path)
        if not match:
            raise APIError(404, 'Unknown API route')
        collection, doc_id, action = match.groups()
        validate_id(collection, doc_id)
        try:
            old = self.store.get(collection, doc_id)
        except APIError as exc:
            if exc.status != 404 or method != 'PUT' or action:
                raise
            old = None
        if method == 'GET' and not action:
            return self.respond(200, old, {'ETag': f'"{old["version"]}"'})
        if action:
            if method != 'POST' or collection != 'episodes':
                raise APIError(405, 'Method not allowed')
            return self.decision(doc_id, old, action, body)
        if method not in ('PUT', 'PATCH', 'DELETE'):
            raise APIError(405, 'Method not allowed')
        if not self.identity()['canEdit']:
            raise APIError(403, 'This identity cannot edit')
        if old:
            self.check_version(body, old)
        if method == 'DELETE':
            return self.respond(200, self.store.save(collection, doc_id, {}, old, delete=True))
        fields = {k: v for k, v in body.items() if k not in ('ifVersion', 'id', 'version', 'updatedAt')}
        if 'approval' in fields:
            raise APIError(403, 'Approval records can only be written by a decision action')
        doc = {**(old if method == 'PATCH' else {}), **fields}
        if collection == 'episodes':
            if not isinstance(doc.get('status', 'planning'), str) or doc.get('status', 'planning') not in STATUSES:
                raise APIError(400, 'Invalid episode status')
            if fields.get('status') == 'approved' and (not old or old.get('status') != 'approved'):
                raise APIError(403, 'Use the human approval action to approve')
            if 'review' in fields:
                validate_review(fields['review'])
                doc['status'] = 'review'
                doc.pop('approval', None)
            elif old and old.get('approval'):
                # Keep the decision as an audit trail even across PUT replacements.
                doc['approval'] = old['approval']
        return self.respond(200 if old else 201, self.store.save(collection, doc_id, doc, old))

    def decision(self, doc_id, old, action, body):
        person = self.identity()
        if not person['canApprove']:
            raise APIError(403, 'Approval and change requests require a configured tailnet approver')
        self.check_version(body, old)
        review = old.get('review')
        if old.get('status') != 'review' or not review:
            raise APIError(409, 'Episode is not awaiting review')
        validate_review(review)
        note = body.get('note', '')
        if not isinstance(note, str) or len(note) > 10000:
            raise APIError(400, 'note must be text, at most 10000 characters')
        note = note.strip()
        if action == 'request-changes' and not note:
            raise APIError(400, 'A change request requires a note')
        cover = body.get('cover')
        if action == 'approve' and (not isinstance(cover, str) or cover not in {c['id'] for c in review['covers']}):
            raise APIError(400, 'Choose a cover from this review')
        at = now()
        approval = {'decision': 'approved' if action == 'approve' else 'changes',
                    'note': note, 'by': person['login'], 'name': person['name'], 'at': at, 'delivered': False}
        if action == 'approve':
            approval['cover'] = cover
        provenance = (f"Sent from Peak Mind Studio by {person['name']} ({person['login']}) "
                      f"at {at} for episode {doc_id}: {review['title']}.")
        if action == 'approve':
            message = f'approved {cover}\n\n{provenance}' + (f'\nNote: {note}' if note else '')
        else:
            message = f'changes requested\n\n{note}\n\n{provenance}'
        # Persist the decision before sending, while retaining delivered false until confirmation.
        pending = self.store.save('episodes', doc_id, {**old, 'approval': approval,
                                  'status': 'approved' if action == 'approve' else 'review'}, old)
        try:
            result = subprocess.run([self.store.config['t3Bin'], 'thread', 'send', review['t3ThreadId'], message],
                                    capture_output=True, text=True, timeout=30, check=False)
            if result.returncode:
                raise RuntimeError(f'T3 exited with status {result.returncode}')
        except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
            approval = {**approval, 'deliveryError': str(exc)}
            doc = self.store.save('episodes', doc_id, {**pending, 'approval': approval, 'status': 'review'}, pending)
            return self.respond(502, {'error': 'Decision saved but delivery failed. Retry here or reply in T3.', 'episode': doc})
        approval = {**approval, 'delivered': True}
        doc = self.store.save('episodes', doc_id, {**pending, 'approval': approval,
                              'status': 'approved' if action == 'approve' else 'review'}, pending)
        return self.respond(200, doc)

    def serve_file(self, route):
        if route.startswith('/media/'):
            bits = route[len('/media/'):].split('/', 1)
            if len(bits) != 2 or bits[0] not in self.store.config['mediaRoots']:
                raise APIError(404, 'Unknown media root')
            root = self.store.config['mediaRoots'][bits[0]]
            relative = bits[1]
        else:
            root, relative = STATIC, ('index.html' if route == '/' else route.lstrip('/'))
        if '\x00' in relative or '\\' in relative:
            raise APIError(403, 'Invalid path')
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise APIError(404, 'File not found')
        with target.open('rb') as stream:
            size = os.fstat(stream.fileno()).st_size
            start, end, status = 0, size - 1, 200
            requested = self.headers.get('Range')
            if requested:
                match = re.fullmatch(r'bytes=(\d*)-(\d*)', requested)
                if not match or not any(match.groups()) or size == 0:
                    return self.respond(416, headers={'Content-Range': f'bytes */{size}'})
                a, b = match.groups()
                start = int(a) if a else max(0, size - int(b))
                end = min(size - 1, int(b)) if a and b else size - 1
                if start >= size or end < start:
                    return self.respond(416, headers={'Content-Range': f'bytes */{size}'})
                status = 206
            self.send_response(status)
            mime = 'audio/mp4' if target.suffix.lower() == '.m4a' else mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(end - start + 1))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            # Even HTML files in media roots cannot run scripts or make third-party requests.
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; media-src 'self'; connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
            if status == 206:
                self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.end_headers()
            stream.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                block = stream.read(min(65536, remaining))
                if not block:
                    break
                self.wfile.write(block)
                remaining -= len(block)


def make_server(config):
    server = ThreadingHTTPServer(('127.0.0.1', config['port']), StudioHandler)
    server.daemon_threads = True
    server.store = Store(config)
    server.store.recover_pending()
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', help='Config JSON path (or PEAK_MIND_STUDIO_CONFIG)')
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('serve')
    sub.add_parser('import').add_argument('directory')
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.command == 'import':
            for line in Store(config).import_dir(args.directory):
                print(line)
        else:
            server = make_server(config)
            print(f'Peak Mind Studio: http://127.0.0.1:{server.server_port}', flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
    except (OSError, ValueError, APIError) as exc:
        parser.exit(1, f'Studio: {exc}\n')


if __name__ == '__main__':
    main()
