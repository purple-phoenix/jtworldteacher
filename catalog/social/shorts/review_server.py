"""Read-only, byte-range static server for tailnet video review.

python3 review_server.py /Users/mtmccarthy/peak-mind-shorts 5490
Bind only to loopback. Expose separately using Tailscale Serve, never Funnel.
"""
import functools
import http.server
import os
import re
import sys


class ReviewHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        self.remaining = None
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            return super().send_head()
        f = open(path, "rb")
        size = os.fstat(f.fileno()).st_size
        header = self.headers.get("Range")
        start, end = 0, size - 1
        if header:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", header)
            if not match or not any(match.groups()):
                f.close()
                self.send_error(416)
                return None
            a, b = match.groups()
            if a:
                start = int(a)
                end = min(int(b), size - 1) if b else size - 1
            else:
                start = max(0, size - int(b))
            if start > end or start >= size:
                f.close()
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.end_headers()
                return None
        self.send_response(206 if header else 200)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        if header:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        f.seek(start)
        self.remaining = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        if self.remaining is None:
            return super().copyfile(source, outputfile)
        try:
            while self.remaining:
                data = source.read(min(65536, self.remaining))
                if not data:
                    break
                outputfile.write(data)
                self.remaining -= len(data)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == "__main__":
    handler = functools.partial(ReviewHandler, directory=os.path.abspath(sys.argv[1]))
    http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[2])), handler).serve_forever()
