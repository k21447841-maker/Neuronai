#!/usr/bin/env bash

echo "Searching for files with old Gemini model..."

# Find all files with the old model name and replace it with the new one
grep -rl "gemini-2.5-flash" app/ | xargs sed -i 's/gemini-2.5-flash/gemini-3.8-flash/g'

echo "✅ Gemini model updated successfully!"
