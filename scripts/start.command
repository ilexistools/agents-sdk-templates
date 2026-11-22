#!/usr/bin/env bash
# macOS: double-click in Finder to start the catalog dashboard.
exec "$(dirname "$0")/catalog.sh" start "$@"
