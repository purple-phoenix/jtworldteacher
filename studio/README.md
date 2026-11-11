# Peak Mind Studio

A small self-hosted production desk for JT and Matt's Wednesday podcast. Prep, scripts, checklist, clip ideas, topic ideas, the on-air prompter, and weekly publishing decisions live in local JSON files. It replaces Claude artifacts for Peak Mind documents. Python 3.13 or newer, standard library only. No pip, npm, build step, remote fonts, analytics, or third-party page requests.

## Configuration

Read `~/.config/peak-mind-studio/config.json`, or set `PEAK_MIND_STUDIO_CONFIG` to another file. Both Python entry points also accept `--config PATH` before their subcommand. A missing file uses defaults, including empty people lists, so nobody can approve until configured.

```json
{
  "dataDir": "~/peak-mind-studio/data",
  "port": 5480,
  "t3Bin": "t3",
  "approvers": ["person@example.invalid"],
  "editors": ["person@example.invalid"],
  "mediaRoots": {"kits": "~/Downloads/peak-mind-spotify"},
  "appDir": "~/peak-mind-studio/app",
  "launchAgent": "~/Library/LaunchAgents/com.peakmind.studio.plist",
  "logFile": "~/Library/Logs/peak-mind-studio.log",
  "pythonBin": "python3",
  "path": "~/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
}
```

Use the exact Tailscale login for each person. `editors` defaults to `approvers` when omitted. `mediaRoots` maps names to read-only folders. The server expands `~` in file paths and resolves symlinks. `t3Bin` can be a binary on PATH or an absolute executable path, never a command with shell arguments. Optional `baseUrl` sets the CLI API URL; `--base-url` or `PEAK_MIND_STUDIO_URL` takes precedence. The server always binds to `127.0.0.1`, regardless of config. `port: 0` is useful for tests.

`appDir`, `launchAgent`, `logFile`, `pythonBin`, and optional `path` configure the installer. The default PATH includes the current user's `.local/bin` and `/opt/homebrew/bin`. When specifying `path`, write absolute directories (the example's initial `~` is expanded by the installer). Keep app and data paths separate. An update reloads the launch agent so changed configuration paths take effect.

## Run, import, and install

Run directly from the checkout:

```sh
python3 studio/server.py import /absolute/path/to/export
python3 studio/server.py serve
```

Import reads `episodes/*.json` and `ideas/*.json`. Filenames supply the ids. New documents start at version 1; an existing document is reported and skipped. No source files are modified. Imports strip approval records, which cannot count as a new human decision. Keep exports and all real data outside this public repository.

For a persistent macOS service, explicitly run:

```sh
studio/install.sh
```

The installer copies only code and static assets into the configured app directory. It creates the configured launchd plist, enables RunAtLoad and KeepAlive, and bootstraps or restarts `com.peakmind.studio`. It never copies, resets, or deletes the data directory. Logs default to `~/Library/Logs/peak-mind-studio.log`. Choose a Python 3.13 or newer interpreter with `pythonBin` if `python3` points to Apple's older Python.

Then, separately, configure Tailscale Serve:

```sh
tailscale serve --bg --https=5480 http://127.0.0.1:5480
```

Open `https://<machine>.<tailnet>.ts.net:5480/` from a phone or Mac on the tailnet. Never expose it through Funnel, a public reverse proxy, or a non-loopback bind. When moving to the Mac mini, copy the private data and media directories separately, update config paths and people lists, then install there. Stop the old service before using the new copy as the source of truth.

## Data, versions, and backups

```text
<dataDir>/episodes/YYYY-MM-DD.json
<dataDir>/ideas/short-slug.json
<dataDir>/.history/episodes/YYYY-MM-DD/1.json
<dataDir>/.history/ideas/short-slug/1.json
<dataDir>/.lock
```

Each document includes `id`, integer `version`, and UTC `updatedAt`. Writes use a private temp file, flush and fsync it, then rename it atomically. Before replacement or deletion, the complete old document is copied into `.history`. Deleted ids can be recreated, but versions keep increasing so stale clients cannot overwrite them. A filesystem lock also serializes imports against the server. Approval delivery holds this lock, for at most the 30 second subprocess timeout. Other API requests can wait during that period.

Back up the entire data directory, including `.history`, plus the config and media roots. Stop the service for a consistent file-level backup or restore. History is recovery material, not a tamper-proof audit log. Copy a historical document to private scratch, inspect it, then restore fields through a version-pinned PATCH. Do not restore an old approval as authority to publish. Nothing here backs up media automatically.

The page polls every four seconds, with conditional ETags. Polling pauses while hidden, editing, reading on air, or playing a review clip. An open form keeps its original document version. Concurrent writes return a conflict and preserve typed text. Copy any unsaved text before cancelling and reloading to review the current version.

## HTTP API

All routes are same-origin. JSON responses include errors as `{ "error": "..." }`. Every mutation requires both `Content-Type: application/json` and `X-Peak-Mind-Studio: 1`, including DELETE. There is no CORS permission for external origins.

| Route | Behavior |
| --- | --- |
| `GET /api/me` | `login`, `name`, `canEdit`, `canApprove`, `local` |
| `GET /api/state` | `{revision, episodes, ideas}`, revision ETag, 304 on matching `If-None-Match` |
| `GET /api/episodes/<id>` | Document and version ETag |
| `PUT /api/episodes/<id>` | Create or replace |
| `PATCH /api/episodes/<id>` | Merge top-level fields |
| `DELETE /api/episodes/<id>` | Archive previous version, delete current document |
| `/api/ideas/<id>` | Same CRUD methods as episodes |
| `POST /api/episodes/<id>/approve` | `{cover, note?, ifVersion}`, human approval and T3 delivery |
| `POST /api/episodes/<id>/request-changes` | `{note, ifVersion}`, required note and T3 delivery |
| `GET /media/<root>/<relative-path>` | Read-only media, single byte ranges, M4A as `audio/mp4` |

Existing-document PUT, PATCH, DELETE and decisions require `ifVersion` in the body or the numeric version in `If-Match` (quoted or unquoted). Missing or stale versions return 409 with `currentVersion`. Creates need no version. Episode ids are real calendar dates in `YYYY-MM-DD` or `YYYY-MM-DD-N` form. Idea ids are short lowercase alphanumeric slugs with optional internal hyphens, at most 80 characters. Media paths must resolve inside their configured root, including symlinks. Missing or escaped media returns 404. Unsatisfiable or multiple ranges return 416.

Statuses: `planning`, `recorded`, `editing`, `review` (Awaiting approval), `approved` (Approved, publishing), `published`. Ordinary writes cannot create approval records or transition into approved. Writing a review validates its schema, sets review status and clears old approval. Existing decisions are retained across ordinary edits. The publishing agent must compare the approved content to the current review before acting.

## Weekly review and approval safety

Local requests without a Tailscale identity may read and edit, but can never approve or request changes. Tailnet requests may edit only if `Tailscale-User-Login` is in `editors`. Only logins in `approvers` may use the decision actions. `Tailscale-User-Name` supplies the display name. Approvers need not also be editors when an explicit editors list is configured.

This trusts Tailscale Serve to set the identity headers and is a simple local trust boundary. A local process could forge those headers, edit the files, or invoke T3 itself. The publishing agent must independently re-check the recorded decision, version/current review and chosen cover, and verify that the matching decision actually arrived as a T3 message. A JSON approval record alone is insufficient. The app does not publish audio, upload to Spotify, or deploy the site.

Approving requires review status, a valid structured review with publishing thread id, a cover from that review, and the current version. The page confirms the title and chosen cover before sending. The server records the person, time, note and cover before invoking `[t3Bin, "thread", "send", t3ThreadId, message]` without a shell, with a 30 second timeout. Approval first sets approved status with delivery false. On success it marks delivery true. On failure it keeps review status, records delivery false and a delivery error, and returns 502 with the saved episode. Request changes keeps review status and requires a note.

Approval message format:

```text
approved <cover>

Sent from Peak Mind Studio by <name> (<login>) at <ISO time> for episode <id>: <title>.
Note: <optional note>
```

The Note line is omitted when empty. Change requests send `changes requested`, a blank line, the note, another blank line, then the same provenance sentence. A crash between sending and saving the success record, or a timeout after T3 accepted the message, can leave delivery uncertain. Check the publishing thread before retrying. Delivery is not exactly-once. On restart, an approved decision without delivery confirmation returns to review with an error asking you to check T3 before retrying.

## Weekly agent CLI

The CLI is a local editor, with no approval command. It reads the current version and pins each write to it; conflicts and all HTTP errors exit nonzero. JSON inputs can be a file path or an inline object.

```sh
python3 studio/studioctl.py list
python3 studio/studioctl.py get YYYY-MM-DD
python3 studio/studioctl.py patch YYYY-MM-DD '{"status":"editing"}'
python3 studio/studioctl.py put-review YYYY-MM-DD /private/scratch/review.json
python3 studio/studioctl.py set-status YYYY-MM-DD published
python3 studio/studioctl.py --collection ideas list
```

Create a planning episode in the UI (or PUT it through the API) before `put-review`. The weekly run writes a transcript-grounded review, then waits for Matt to decide in Studio. It checks the matching T3 message and recorded approval before continuing its existing publishing process. It sets published only after publication succeeds. Integration into a scheduled weekly prompt is a separate operational step.

Review JSON schema (synthetic example, not show data):

```json
{
  "t3ThreadId": "publishing-thread-id",
  "t3ThreadLink": "t3://optional-thread-link",
  "title": "Example episode",
  "titleAlternates": ["Another title"],
  "conciseDescription": "A short, transcript-grounded description.",
  "spotifyDescription": "Longer transcript-grounded copy.",
  "length": "1:02:30",
  "confidence": "HIGH",
  "confidenceNote": "Optional explanation",
  "start": {"at": "2:10", "cutLine": "Pre-show line", "firstLine": "Program opener"},
  "end": {"at": "1:04:40", "lastLine": "Program close", "cutLine": "After-show line"},
  "flags": [],
  "covers": [
    {"id": "v1", "label": "Option one", "media": "kits/example/cover-one.jpg"},
    {"id": "v2", "label": "Option two", "media": "kits/example/cover-two.jpg"}
  ],
  "defaultCover": "v1",
  "clips": [
    {"id": "open", "label": "Opening", "media": "kits/example/open.m4a"},
    {"id": "close", "label": "Ending", "media": "kits/example/close.m4a"}
  ]
}
```

Length and cut timestamps are display strings; confidence is `HIGH` or `LOW`. Cover and clip ids are unique within their list and use letters, numbers, underscores or hyphens. `media` is a root name and relative path, never a remote URL. `defaultCover` must exist. A review requires at least one cover; it supports any number of covers and clips, normally two of each. An imported episode with review status but no structured review shows a waiting message until the weekly run writes one. Import does not guess cut points or publishing thread ids from prose.

## Verification

```sh
python3 -m unittest discover -s studio/tests -v
python3 -m unittest discover -s catalog/scripts/tests -v
```

Tests start a loopback server on an ephemeral port with temp data, config, media, and a fake T3 executable. They never contact T3, modify the private Studio directory, install services, or change Tailscale.
