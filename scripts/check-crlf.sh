#!/bin/sh
# Fail if any tracked file has CRLF (or mixed) line endings in the working tree.
# Replaces the third-party erclu/check-crlf GitHub Action so CI does not depend
# on an external action (and its EOL base image).
set -eu

# `git ls-files --eol` reports the working-tree end-of-line style in the "w/"
# field, e.g. "i/lf    w/crlf  attr/    path/to/file". Flag crlf and mixed.
offenders=$(git ls-files --eol | grep -E 'w/(crlf|mixed)' || true)

if [ -n "$offenders" ]; then
    echo "Error: the following files contain CRLF line endings:" >&2
    echo "$offenders" | sed -E 's/^.*[[:space:]]attr\/[^[:space:]]*[[:space:]]+/  /' >&2
    exit 1
fi

echo "No CRLF line endings found."
