#!/bin/bash

# replace_optional_typing.sh
# Usage: bash replace_optional_typing.sh [path-to-repo]
# Default path is current directory

TARGET_DIR="${1:-.}"

echo "🔍 Searching Python files in: $TARGET_DIR"
echo "🛠 Replacing Optional[...] with new union syntax (xxx | None)"

find "$TARGET_DIR" -type f -name "*.py" | while read -r file; do
  sed -E -i.bak \
    's/Optional\[([a-zA-Z0-9_\.]+)\]/\1 | None/g' "$file"

  # Optional: remove backup files after confirming change
  rm "${file}.bak"
done

echo "✅ Replacement complete.