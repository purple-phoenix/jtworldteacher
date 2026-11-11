#!/usr/bin/env python3
"""API integration tests with private temp files and a fake T3 boundary."""

from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

STUDIO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('studio_server', STUDIO / 'server.py')
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


def review():
    return {'t3ThreadId': 'fake-thread', 'title': 'Test episode', 'titleAlternates': ['Alternate'],
            'conciseDescription': 'Short copy', 'spotifyDescription': 'Longer copy', 'length': '1:00:00',
            'confidence': 'HIGH', 'start': {'at': '1:00', 'cutLine': 'Before', 'firstLine': 'Hello'},
            'end': {'at': '1:01:00', 'lastLine': 'Goodbye', 'cutLine': 'After'}, 'flags': ['Check a claim'],
            'covers': [{'id': 'v1', 'label': 'First', 'media': 'kits/one.jpg'},
                       {'id': 'v2', 'label': 'Second', 'media': 'kits/two.jpg'}],
            'defaultCover': 'v1', 'clips': [{'id': 'opening', 'label': 'Open', 'media': 'kits/open.m4a'}]}


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='studio-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.media = self.root / 'media'
        self.media.mkdir()
        (self.media / 'sample.m4a').write_bytes(b'0123456789')
        self.record = self.root / 'argv.json'
        fake = self.root / 'fake-t3'
        fake.write_text(f'#!{sys.executable}\nimport json,sys\nfrom pathlib import Path\nPath({str(self.record)!r}).write_text(json.dumps(sys.argv[1:]))\n')
        fake.chmod(0o700)
        self.config_path = self.root / 'config.json'
        self.config_path.write_text(json.dumps({'dataDir': str(self.root / 'data'), 'port': 0,
                                               'mediaRoots': {'kits': str(self.media)}, 't3Bin': str(fake),
                                               'approvers': ['owner@example.invalid']}))
        self.config = server.load_config(self.config_path)
        self.httpd = server.make_server(self.config)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.base = f'http://127.0.0.1:{self.httpd.server_port}'
        self.route = '/api/episodes/2026-01-07'
        self.person = {'Tailscale-User-Login': 'owner@example.invalid', 'Tailscale-User-Name': 'Test Person'}

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)

    def call(self, route=None, method='GET', body=None, headers=None, guard=True, raw=False):
        request_headers = {'Content-Type': 'application/json'}
        if guard:
            request_headers['X-Peak-Mind-Studio'] = '1'
        request_headers.update(headers or {})
        data = None if body is None else json.dumps(body).encode()
        req = Request(self.base + (route or self.route), method=method, data=data, headers=request_headers)
        try:
            response = urlopen(req, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            payload = response.read()
            result = payload if raw or not payload else json.loads(payload)
            return response.status, result, response.headers

    def create(self, fields=None):
        code, doc, _ = self.call(method='PUT', body=fields or {'title': 'Test', 'status': 'planning'})
        self.assertEqual(code, 201, doc)
        return doc

    def awaiting(self):
        return self.create({'status': 'review', 'review': review()})

    def history(self, version):
        return self.root / 'data/.history/episodes/2026-01-07' / f'{version}.json'

    def cli(self, *args):
        return subprocess.run([sys.executable, str(STUDIO / 'studioctl.py'), '--config', str(self.config_path),
                               '--base-url', self.base, *args], capture_output=True, text=True, timeout=5)

    def test_crud_versions_history_and_recreate(self):
        first = self.create()
        self.assertEqual(first['version'], 1)
        self.assertIn('updatedAt', first)
        code, second, _ = self.call(method='PATCH', body={'title': 'Changed', 'ifVersion': 1})
        self.assertEqual((code, second['version'], second['status']), (200, 2, 'planning'))
        self.assertEqual(json.loads(self.history(1).read_text()), first)
        code, third, _ = self.call(method='PUT', body={'title': 'Replacement'}, headers={'If-Match': '"2"'})
        self.assertEqual((code, third['version']), (200, 3))
        self.assertNotIn('status', third)
        self.assertEqual(json.loads(self.history(2).read_text()), second)
        self.assertEqual(self.call(method='DELETE', body={'ifVersion': 3})[0], 200)
        self.assertEqual(self.call()[0], 404)
        self.assertEqual(json.loads(self.history(3).read_text()), third)
        self.assertEqual(self.create()['version'], 4)
        self.assertEqual(self.call(method='PATCH', body={'ifVersion': 1, 'title': 'Stale'})[0], 409)

    def test_missing_and_stale_versions_never_overwrite(self):
        self.create()
        for method in ('PUT', 'PATCH', 'DELETE'):
            for version in (None, 0, 2, True):
                body = {'title': 'Stale'}
                if version is not None:
                    body['ifVersion'] = version
                code, payload, _ = self.call(method=method, body=body)
                self.assertEqual(code, 409, payload)
                self.assertEqual(payload['currentVersion'], 1)
        self.assertEqual(self.call()[1]['title'], 'Test')

    def test_concurrent_writes_only_one_wins(self):
        self.create()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda x: self.call(method='PATCH', body={'title': str(x), 'ifVersion': 1}), [1, 2]))
        self.assertEqual(sorted(r[0] for r in results), [200, 409])
        self.assertEqual(self.call()[1]['version'], 2)

    def test_ideas_and_state_etag(self):
        route = '/api/ideas/new-topic'
        self.assertEqual(self.call(route, 'PUT', {'text': 'Idea'})[0], 201)
        code, state, headers = self.call('/api/state')
        self.assertEqual(code, 200)
        self.assertEqual(state['ideas'][0]['text'], 'Idea')
        self.assertEqual(self.call('/api/state', headers={'If-None-Match': headers['ETag']})[0], 304)
        self.call(route, 'PATCH', {'used': True, 'ifVersion': 1})
        self.assertNotEqual(self.call('/api/state')[1]['revision'], state['revision'])
        self.assertEqual(self.call(route, 'DELETE', {'ifVersion': 2})[0], 200)

    def test_strict_ids_and_invalid_bodies(self):
        for route in ('/api/episodes/2026-02-30', '/api/episodes/2026-01-07-0', '/api/ideas/UPPER',
                      '/api/ideas/..', '/api/ideas/a%2Fb', '/api/ideas/' + 'a' * 81):
            self.assertIn(self.call(route, 'PUT', {'title': 'Invalid'})[0], (400, 404))
        self.assertEqual(self.call(method='PUT', body=[])[0], 400)
        self.assertEqual(self.call(method='PUT', body={'status': 'arbitrary'})[0], 400)

    def test_import_skips_existing_and_preserves_source(self):
        exports = self.root / 'exports'
        (exports / 'episodes').mkdir(parents=True)
        (exports / 'ideas').mkdir()
        episode = exports / 'episodes/2026-01-07.json'
        original = json.dumps({'title': 'Imported', 'version': 50})
        episode.write_text(original)
        (exports / 'ideas/topic.json').write_text('{"text":"A thought"}')
        result = self.httpd.store.import_dir(exports)
        self.assertEqual(len(result), 2)
        self.assertEqual(self.call()[1]['version'], 1)
        episode.write_text('{"title":"Should be skipped"}')
        self.assertTrue(all(x.startswith('Skipped') for x in self.httpd.store.import_dir(exports)))
        self.assertEqual(self.call()[1]['title'], 'Imported')
        self.assertEqual(episode.read_text(), '{"title":"Should be skipped"}')
        self.assertFalse(self.history(1).exists())

    def test_import_command_and_config_env(self):
        exports = self.root / 'export-cli/episodes'
        exports.mkdir(parents=True)
        (exports / '2026-01-07.json').write_text('{"title":"CLI import"}')
        command = [sys.executable, str(STUDIO / 'server.py'), 'import', str(exports.parent)]
        result = subprocess.run(command, env={**os.environ, 'PEAK_MIND_STUDIO_CONFIG': str(self.config_path)},
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Imported episodes/2026-01-07', result.stdout)
        self.assertEqual(self.call()[1]['version'], 1)

    def test_media_range_mime_and_escape(self):
        route = '/media/kits/sample.m4a'
        code, data, headers = self.call(route, raw=True)
        self.assertEqual((code, data, headers['Content-Type']), (200, b'0123456789', 'audio/mp4'))
        for requested, expected, content_range in [('bytes=2-5', b'2345', 'bytes 2-5/10'),
                                                   ('bytes=8-', b'89', 'bytes 8-9/10'),
                                                   ('bytes=-3', b'789', 'bytes 7-9/10'),
                                                   ('bytes=8-99', b'89', 'bytes 8-9/10')]:
            code, data, headers = self.call(route, headers={'Range': requested}, raw=True)
            self.assertEqual((code, data, headers['Content-Range']), (206, expected, content_range))
            self.assertEqual(int(headers['Content-Length']), len(expected))
        for value in ('bytes=20-', 'bytes=3-1', 'bytes=0-1,3-4', 'bytes=-0'):
            self.assertEqual(self.call(route, headers={'Range': value})[0], 416)
        outside = self.root / 'private.txt'
        outside.write_text('secret')
        (self.media / 'escaped.txt').symlink_to(outside)
        (self.media / 'escaped-dir').symlink_to(self.root, target_is_directory=True)
        for path in ('../private.txt', '%2e%2e/private.txt', 'escaped.txt', 'escaped-dir/private.txt'):
            self.assertEqual(self.call('/media/kits/' + path)[0], 404)
        self.assertEqual(self.call('/media/missing/file')[0], 404)

    def test_csrf_and_content_type_required_for_every_mutation(self):
        self.create()
        for method in ('PUT', 'PATCH', 'DELETE', 'POST'):
            self.assertEqual(self.call(method=method, body={'ifVersion': 1}, guard=False)[0], 403)
            self.assertEqual(self.call(method=method, body={}, headers={'Content-Type': 'text/plain'})[0], 415)

    def test_me_and_edit_roles(self):
        self.assertEqual(self.call('/api/me')[1], {'login': None, 'name': 'Local agent', 'canEdit': True,
                                                  'canApprove': False, 'local': True})
        self.assertTrue(self.call('/api/me', headers=self.person)[1]['canApprove'])
        outsider = {'Tailscale-User-Login': 'outsider@example.invalid'}
        self.assertFalse(self.call('/api/me', headers=outsider)[1]['canEdit'])
        self.assertEqual(self.call(method='PUT', body={'title': 'Forbidden'}, headers=outsider)[0], 403)
        self.create()
        for method in ('PATCH', 'PUT', 'DELETE'):
            self.assertEqual(self.call(method=method, body={'ifVersion': 1}, headers=outsider)[0], 403)

    def test_local_and_non_approver_cannot_make_decisions(self):
        self.awaiting()
        for identity in ({}, {'Tailscale-User-Login': 'outsider@example.invalid'}):
            for action in ('approve', 'request-changes'):
                code, _, _ = self.call(self.route + '/' + action, 'POST',
                                       {'cover': 'v1', 'note': 'Please fix', 'ifVersion': 1}, identity)
                self.assertEqual(code, 403)
        self.assertFalse(self.record.exists())
        self.assertEqual(self.call(method='PATCH', body={'approval': {'delivered': True}, 'ifVersion': 1})[0], 403)
        self.assertEqual(self.call(method='PATCH', body={'status': 'approved', 'ifVersion': 1})[0], 403)

    def test_explicit_editors_may_edit_but_not_approve(self):
        self.httpd.store.config['editors'] = ['editor@example.invalid']
        identity = {'Tailscale-User-Login': 'editor@example.invalid'}
        self.assertEqual(self.call(method='PUT', body={'review': review()}, headers=identity)[0], 201)
        self.assertEqual(self.call(self.route + '/approve', 'POST', {'cover': 'v1', 'ifVersion': 1}, identity)[0], 403)
        me = self.call('/api/me', headers=self.person)[1]
        self.assertFalse(me['canEdit'])
        self.assertTrue(me['canApprove'])

    def test_approve_exact_message_and_fake_t3_argv(self):
        self.awaiting()
        code, doc, _ = self.call(self.route + '/approve', 'POST', {'cover': 'v2', 'note': 'Looks good', 'ifVersion': 1}, self.person)
        self.assertEqual(code, 200, doc)
        approval = doc['approval']
        self.assertEqual((doc['status'], approval['decision'], approval['cover'], approval['delivered']),
                         ('approved', 'approved', 'v2', True))
        message = (f"approved v2\n\nSent from Peak Mind Studio by Test Person (owner@example.invalid) at {approval['at']} "
                   'for episode 2026-01-07: Test episode.\nNote: Looks good')
        self.assertEqual(json.loads(self.record.read_text()), ['thread', 'send', 'fake-thread', message])
        self.assertEqual(json.loads(self.history(1).read_text())['status'], 'review')
        self.assertFalse(json.loads(self.history(2).read_text())['approval']['delivered'])
        self.assertEqual(self.call(self.route + '/approve', 'POST', {'cover': 'v1', 'ifVersion': doc['version']}, self.person)[0], 409)

    def test_approve_without_note_and_review_replacement_clears_approval(self):
        self.awaiting()
        doc = self.call(self.route + '/approve', 'POST', {'cover': 'v1', 'ifVersion': 1}, self.person)[1]
        self.assertNotIn('\nNote:', json.loads(self.record.read_text())[-1])
        replacement = review()
        replacement['title'] = 'New review'
        code, current, _ = self.call(method='PATCH', body={'review': replacement, 'ifVersion': doc['version']})
        self.assertEqual((code, current['status']), (200, 'review'))
        self.assertNotIn('approval', current)

    def test_decision_validation_and_version_conflicts(self):
        self.awaiting()
        for body, expected in [({'cover': 'v1'}, 409), ({'cover': 'bad', 'ifVersion': 1}, 400),
                               ({'cover': 'v1', 'note': 5, 'ifVersion': 1}, 400)]:
            self.assertEqual(self.call(self.route + '/approve', 'POST', body, self.person)[0], expected)
        for note in ('', '   '):
            self.assertEqual(self.call(self.route + '/request-changes', 'POST', {'note': note, 'ifVersion': 1}, self.person)[0], 400)
        self.assertFalse(self.record.exists())

    def test_delivery_failure_rolls_back_and_can_retry(self):
        self.awaiting()
        self.httpd.store.config['t3Bin'] = str(self.root / 'missing-t3')
        code, error, _ = self.call(self.route + '/approve', 'POST', {'cover': 'v1', 'ifVersion': 1}, self.person)
        self.assertEqual(code, 502)
        doc = error['episode']
        self.assertEqual(doc['status'], 'review')
        self.assertFalse(doc['approval']['delivered'])
        self.assertIn('deliveryError', doc['approval'])
        self.assertEqual(self.call()[1], doc)
        self.httpd.store.config['t3Bin'] = str(self.root / 'fake-t3')
        self.assertEqual(self.call(self.route + '/approve', 'POST', {'cover': 'v1', 'ifVersion': doc['version']}, self.person)[0], 200)

    def test_restart_recovers_an_unconfirmed_decision(self):
        doc = self.awaiting()
        with self.httpd.store.locked():
            self.httpd.store.save('episodes', '2026-01-07', {**doc, 'status': 'approved',
                'approval': {'decision': 'approved', 'delivered': False}}, doc)
        self.httpd.store.recover_pending()
        current = self.call()[1]
        self.assertEqual(current['status'], 'review')
        self.assertFalse(current['approval']['delivered'])
        self.assertIn('Check T3', current['approval']['deliveryError'])
        self.assertEqual(json.loads(self.history(2).read_text())['status'], 'approved')

    def test_nonzero_and_timeout_delivery(self):
        self.awaiting()
        for failure in (subprocess.CompletedProcess([], 7), subprocess.TimeoutExpired('t3', 30)):
            current = self.call()[1]
            kwargs = {'side_effect': failure} if isinstance(failure, Exception) else {'return_value': failure}
            with patch.object(server.subprocess, 'run', **kwargs) as run:
                code, error, _ = self.call(self.route + '/approve', 'POST', {'cover': 'v1', 'ifVersion': current['version']}, self.person)
                self.assertEqual(code, 502)
                self.assertFalse(error['episode']['approval']['delivered'])
                self.assertEqual(run.call_args.kwargs['timeout'], 30)

    def test_request_changes_exact_message_and_failure(self):
        self.awaiting()
        code, doc, _ = self.call(self.route + '/request-changes', 'POST', {'note': 'Fix opening', 'ifVersion': 1}, self.person)
        self.assertEqual((code, doc['status'], doc['approval']['decision'], doc['approval']['delivered']), (200, 'review', 'changes', True))
        expected = (f"changes requested\n\nFix opening\n\nSent from Peak Mind Studio by Test Person (owner@example.invalid) "
                    f"at {doc['approval']['at']} for episode 2026-01-07: Test episode.")
        self.assertEqual(json.loads(self.record.read_text())[-1], expected)
        self.httpd.store.config['t3Bin'] = '/nonexistent/fake-t3'
        code, error, _ = self.call(self.route + '/request-changes', 'POST', {'note': 'Again', 'ifVersion': doc['version']}, self.person)
        self.assertEqual((code, error['episode']['status']), (502, 'review'))

    def test_review_schema_rejects_missing_thread_bad_media_and_duplicate_covers(self):
        variants = []
        for key in ('t3ThreadId', 'start', 'confidence', 'defaultCover'):
            candidate = review()
            del candidate[key]
            variants.append(candidate)
        candidate = review()
        candidate['covers'][0]['media'] = 'kits/../private.jpg'
        variants.append(candidate)
        candidate = review()
        candidate['covers'][1]['id'] = 'v1'
        variants.append(candidate)
        for candidate in variants:
            self.assertEqual(self.call(method='PUT', body={'review': candidate})[0], 400)
        self.assertEqual(self.call()[0], 404)

    def test_studioctl_live_put_review_status_patch_list_and_errors(self):
        self.create()
        path = self.root / 'review.json'
        path.write_text(json.dumps(review()))
        result = self.cli('put-review', '2026-01-07', str(path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'review')
        result = self.cli('set-status', '2026-01-07', 'published')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['version'], 3)
        self.assertEqual(self.cli('patch', '2026-01-07', '{"title":"CLI title"}').returncode, 0)
        self.assertEqual(json.loads(self.cli('get', '2026-01-07').stdout)['title'], 'CLI title')
        self.assertEqual(len(json.loads(self.cli('list').stdout)), 1)
        error = self.cli('get', '2026-01-14')
        self.assertNotEqual(error.returncode, 0)
        self.assertIn('HTTP 404', error.stderr)
        error = self.cli('set-status', '2026-01-07', 'approved')
        self.assertNotEqual(error.returncode, 0)
        self.assertIn('HTTP 403', error.stderr)

    def test_static_is_local_and_csp_disallows_external_requests(self):
        code, html, headers = self.call('/', raw=True)
        self.assertEqual(code, 200)
        self.assertIn(b'/app.js', html)
        self.assertNotIn(b'https://', html)
        self.assertIn("default-src 'self'", headers['Content-Security-Policy'])
        self.assertEqual(self.call('/../server.py')[0], 404)


if __name__ == '__main__':
    unittest.main()
