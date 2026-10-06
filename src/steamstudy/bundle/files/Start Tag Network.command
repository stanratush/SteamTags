#!/bin/sh
# Start the Tag Network app from this App Bundle (macOS: double-click). Keeps the window open on error.
cd "$(dirname "$0")" || exit 1
python3 start_tag_network.py "$@"
status=$?
if [ "$status" -ne 0 ]; then
  echo
  printf "Press Enter to close this window. "
  read -r _
fi
exit "$status"
