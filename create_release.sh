#!/bin/bash

# Create GitHub release for v0.1.0

echo "Creating GitHub release for v0.1.0..."

# First, authenticate if needed
if ! gh auth status >/dev/null 2>&1; then
    echo "Please authenticate with GitHub first:"
    gh auth login
fi

# Create the release
gh release create v0.1.0 \
    --title "Dayflow v0.1.0 - First Official Release" \
    --notes-file RELEASE_NOTES_0.1.0.md \
    --verify-tag \
    dist/dayflow-0.1.0-py3-none-any.whl \
    dist/dayflow-0.1.0.tar.gz

echo "Release created successfully!"
echo "View at: https://github.com/MALathon/dayflow/releases/tag/v0.1.0"
