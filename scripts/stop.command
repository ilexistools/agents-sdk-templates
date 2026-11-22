#!/usr/bin/env bash
# macOS: double-click in Finder to stop the catalog dashboard.
exec "$(dirname "$0")/catalog.sh" stop "$@"
