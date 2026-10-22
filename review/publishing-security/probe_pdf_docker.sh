#!/bin/sh
# Builds the production image and runs hostile PDFs through real Poppler with the container's busybox ulimits.
#   sh review/publishing-security/probe_pdf_docker.sh   (from the repository root)
set -e
here=$(cd "$(dirname "$0")" && pwd)
docker build -q -f portal/Dockerfile -t margen-upload-review:local . >/dev/null
docker run --rm --entrypoint sh margen-upload-review:local -c 'sh -c "ulimit -t 60; ulimit -f 131072; ulimit -n 64; ulimit -v 1048576; ulimit -a" | grep -E "file size|cpu time|virtual|open files"'
for case in image image80 text text80; do
  docker run --rm --memory=2g --cpus=2 -v "$here":/probe:ro --entrypoint python margen-upload-review:local -I /probe/pdf_inputs.py "$case"
done
# Same expected-behaviour tests inside the image (HTTP tests skip: no httpx there).
docker run --rm -e MARGEN_ROOT=/app -v "$here":/probe:ro -w /tmp --entrypoint python margen-upload-review:local -I /probe/test_upload_security.py 2>&1 | grep -E '\.\.\. |^Ran|^OK|^FAILED' || true
