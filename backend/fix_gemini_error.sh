#!/usr/bin/env bash
echo "Fixing Gemini model in backend..."

# Purane model ko naye model se replace karo
grep -rl "gemini-2.5-flash" app/ | xargs sed -i 's/gemini-2.5-flash/gemini-3.8-flash/g'

# Agar purana model kabhi "gemini-pro" tha toh usko bhi update karo
grep -rl "gemini-pro" app/ | xargs sed -i 's/gemini-pro/gemini-3.8-flash/g'

echo "✅ Gemini model successfully updated!"
