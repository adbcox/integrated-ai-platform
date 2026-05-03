#!/usr/bin/env bash
# Resolve qnap:// URI to local mount path. D-17-37 substrate.
#
# Usage:
#   scripts/artifact-resolve.sh qnap://download/manual/roadmap-artifacts/phase-17/D-17-35/source/foo.pdf
#
# Prints local path on stdout. Exit non-zero if scheme unknown or file missing.

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <qnap-uri>" >&2
    exit 64
fi

URI="$1"

case "$URI" in
    qnap://download/*)
        REST="${URI#qnap://download/}"
        LOCAL="/Users/admin/mnt/qnap-downloads/$REST"
        ;;
    *)
        echo "ERROR: unsupported scheme: $URI" >&2
        echo "       Only qnap://download/* supported in v1." >&2
        exit 65
        ;;
esac

if [ ! -e "$LOCAL" ]; then
    echo "ERROR: resolved path missing: $LOCAL" >&2
    exit 66
fi

echo "$LOCAL"
