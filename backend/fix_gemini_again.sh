#!/usr/bin/env bash
echo "Updating Gemini model to 3.1-pro-preview..."

# Purane models ko naye se replace karo
grep -rl "gemini-2.5-flash" app/ | xargs sed -i 's/gemini-2.5-flash/gemini-3.1-pro-preview/g'
grep -rl "gemini-2.5-pro" app/ | xargs sed -i 's/gemini-2.5-pro/gemini-3.1-pro-preview/g'
grep -rl "gemini-3.8-flash" app/ | xargs sed -i 's/gemini-3.8-flash/gemini-3.1-pro-preview/g'

echo "✅ Model updated to gemini-3.1-pro-preview!"
