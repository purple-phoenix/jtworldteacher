"""Hermetic shell regressions. No downloads, models, or media tools are used."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
# Allows the same tests to be run against a pristine base checkout.
SOURCE = Path(os.environ.get('INTAKE_SCRIPTS_SOURCE', SCRIPTS))


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.catalog = self.root / 'catalog'
        self.scripts = self.catalog / 'scripts'
        self.audio = self.catalog / 'spaces/audio'
        self.transcripts = self.catalog / 'spaces/transcripts'
        self.posts = self.catalog / 'posts'
        self.episodes = self.root / 'site/src/content/episodes'
        self.bin = self.root / 'bin'
        for folder in (self.scripts, self.audio, self.transcripts, self.posts,
                       self.episodes, self.bin):
            folder.mkdir(parents=True)
        for name in ('transcribe-pending.sh', 'generate-episode-pages.sh', 'parallel-pipeline.sh'):
            text = (SOURCE / name).read_text()
            # Base script has no tool-path hook. Only adapt that hard-coded PATH
            # in scratch copies so base regressions exercise identity, not tools.
            text = text.replace('PATH=/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin',
                                'PATH="$EPISODE_TOOL_PATH"')
            (self.scripts / name).write_text(text)
        self.env = dict(os.environ, HOME=str(self.root),
                        PATH=f'{self.bin}:' + os.environ['PATH'],
                        EPISODE_TOOL_PATH=f'{self.bin}:' + os.environ['PATH'],
                        FIXTURE_ROOT=str(self.root), MODE='good')
        model = self.root / '.whisper-models/ggml-large-v3-turbo.bin'
        model.parent.mkdir()
        model.write_text('fake model')
        self.env['WHISPER_MODEL'] = str(model)
        self.command('ffprobe', 'echo 120.0')
        self.command('ffmpeg', '''echo ffmpeg >> "$FIXTURE_ROOT/attempts"
[[ "$MODE" != ffmpeg-fail ]] || exit 3
[[ "$MODE" != ffmpeg-empty ]] || exit 0
for output; do :; done
printf wav > "$output"''')
        self.command('whisper-cli', '''echo whisper >> "$FIXTURE_ROOT/attempts"
while (( $# )); do
  if [[ "$1" == -of ]]; then shift; output="$1"; fi
  shift
done
[[ "$MODE" != whisper-fail ]] || { echo partial > "$output.txt"; exit 4; }
[[ "$MODE" != whisper-empty ]] || exit 0
echo transcript > "$output.txt"
[[ "$MODE" != whisper-txt-only ]] || exit 0
echo WEBVTT > "$output.vtt"
[[ "$MODE" != whisper-empty-vtt ]] || : > "$output.vtt"''')
        self.command('sleep', '''count=0
[[ ! -f "$FIXTURE_ROOT/passes" ]] || read -r count < "$FIXTURE_ROOT/passes"
count=$((count+1))
echo "$count" > "$FIXTURE_ROOT/passes"
if (( count >= 3 )); then touch "$FIXTURE_ROOT/catalog/spaces/audio/.stop-transcriber"; fi''')
        self.command('download-space.sh', 'exit 0', directory=self.scripts)

    def command(self, name, body, directory=None):
        target = (directory or self.bin) / name
        target.write_text('#!/usr/bin/env bash\nset -eu\n' + body + '\n')
        target.chmod(0o755)

    def episode(self, slug, identity):
        (self.episodes / f'{slug}.md').write_text(f'---\nspaceId: "{identity}"\n---\nHandwritten\n')

    def input(self, slug='2026-01-01-first', identity='first'):
        audio = self.audio / f'{slug}.m4a'
        audio.write_text('fake audio')
        os.utime(audio, (1000000000, 1000000000))
        (self.posts / f'{slug}-space.md').write_text(
            f'---\nspace_title: "Test"\nspace_id: "{identity}"\nspace_url: "https://x.com/i/spaces/{identity}"\n---\n')
        return slug

    def run_script(self, name, *args):
        return subprocess.run(['bash', str(self.scripts / name), *map(str, args)],
                              env=self.env, capture_output=True, text=True, timeout=10)

    def attempts(self, name):
        log = self.root / 'attempts'
        return log.read_text().splitlines().count(name) if log.exists() else 0

    def test_two_spaces_same_day(self):
        self.input()
        self.input('2026-01-01-second', 'second')
        result = self.run_script('generate-episode-pages.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(list(self.episodes.glob('*.md'))), 2)

    def test_renamed_page_matched_by_space_id(self):
        self.input()
        self.episode('2025-12-31-cleaner-name', 'first')
        result = self.run_script('generate-episode-pages.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(list(self.episodes.glob('*.md'))), 1)

    def test_exact_filename_preserved(self):
        slug = self.input()
        self.episode(slug, 'legacy')
        before = (self.episodes / f'{slug}.md').read_bytes()
        result = self.run_script('generate-episode-pages.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.episodes / f'{slug}.md').read_bytes(), before)

    def test_empty_audio_directory(self):
        result = self.run_script('generate-episode-pages.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('created: 0', result.stdout)

    def assert_failure(self, mode, step, watch=False):
        slug = self.input()
        self.env['MODE'] = mode
        result = self.run_script('transcribe-pending.sh', *(['--watch'] if watch else []))
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn('Transcription failures (1):', output)
        self.assertIn(f'{slug}: {step}', output)
        self.assertNotIn(f'[{slug}] done', output)
        self.assertEqual(self.attempts('ffmpeg'), 1)
        self.assertEqual(self.attempts('whisper'), 0 if mode.startswith('ffmpeg') else 1)
        self.assertFalse(list(self.audio.glob('*.wav')))
        if watch:
            self.assertEqual((self.root / 'passes').read_text().strip(), '3')
            self.assertFalse((self.audio / '.stop-transcriber').exists())

    def test_conversion_failure(self):
        self.assert_failure('ffmpeg-fail', 'ffmpeg conversion')

    def test_conversion_empty_output(self):
        self.assert_failure('ffmpeg-empty', 'ffmpeg output')

    def test_whisper_failure(self):
        self.assert_failure('whisper-fail', 'whisper-cli transcription')

    def test_whisper_success_without_output(self):
        self.assert_failure('whisper-empty', 'whisper-cli output')

    def test_whisper_txt_only(self):
        self.assert_failure('whisper-txt-only', 'whisper-cli output')

    def test_whisper_empty_vtt(self):
        self.assert_failure('whisper-empty-vtt', 'whisper-cli output')

    def test_watch_remembers_failure_including_final_pass(self):
        self.assert_failure('whisper-empty', 'whisper-cli output', watch=True)

    def test_watch_keeps_processing_other_files(self):
        bad = self.input()
        good = self.input('2026-01-01-second', 'second')
        self.command('whisper-cli', '''echo whisper >> "$FIXTURE_ROOT/attempts"
while (( $# )); do
  if [[ "$1" == -of ]]; then shift; output="$1"; fi
  shift
done
[[ "$output" != *first ]] || exit 1
echo transcript > "$output.txt"
echo WEBVTT > "$output.vtt"''')
        result = self.run_script('transcribe-pending.sh', '--watch')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'{bad}: whisper-cli transcription', result.stderr)
        self.assertIn(f'[{good}] done', result.stdout)
        self.assertEqual(self.attempts('whisper'), 2)

    def test_final_pass_transcribes_fresh_audio(self):
        slug = self.input()
        os.utime(self.audio / f'{slug}.m4a', None)
        # Deterministic readiness: regular passes always see a recent file.
        self.command('find', 'echo "$1"')
        result = self.run_script('transcribe-pending.sh', '--watch')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('still being written', result.stdout)
        self.assertEqual(self.attempts('whisper'), 1)
        self.assertTrue((self.transcripts / f'{slug}.vtt').stat().st_size)

    def test_single_pass_reports_fresh_audio_as_unfinished(self):
        slug = self.input()
        os.utime(self.audio / f'{slug}.m4a', None)
        self.command('find', 'echo "$1"')
        result = self.run_script('transcribe-pending.sh')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f'{slug}: file readiness', result.stderr)
        self.assertEqual(self.attempts('ffmpeg'), 0)

    def test_all_good_and_repeat_is_noop(self):
        self.input()
        for _ in range(2):
            result = self.run_script('transcribe-pending.sh')
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.attempts('whisper'), 1)

    def test_incomplete_existing_transcript_retried(self):
        slug = self.input()
        (self.transcripts / f'{slug}.txt').write_text('partial')
        result = self.run_script('transcribe-pending.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.attempts('whisper'), 1)
        self.assertTrue((self.transcripts / f'{slug}.vtt').stat().st_size)

    def pipeline(self):
        self.input()
        queue = self.root / 'queue.txt'
        queue.write_text('fake-url\n')
        return self.run_script('parallel-pipeline.sh', queue)

    def test_pipeline_reports_transcription_failure(self):
        self.env['MODE'] = 'whisper-empty'
        result = self.pipeline()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('=== pipeline complete', result.stdout)
        self.assertEqual(self.attempts('whisper'), 1)

    def test_pipeline_all_good(self):
        result = self.pipeline()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('=== pipeline complete', result.stdout)

    def test_pipeline_download_failure_stops_watcher(self):
        self.command('download-space.sh', 'exit 2', directory=self.scripts)
        result = self.pipeline()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('=== pipeline complete', result.stdout)
        self.assertFalse((self.audio / '.stop-transcriber').exists())


if __name__ == '__main__':
    unittest.main()
