#!/bin/bash
# Push to GitHub script

echo "Pushing Dayflow to GitHub..."

# Check if remote exists
if git remote | grep -q 'origin'; then
    echo "Remote 'origin' already exists"
else
    echo "Adding remote origin..."
    git remote add origin https://github.com/malathon/dayflow.git
fi

# Push to main branch
echo "Pushing to main branch..."
git push -u origin main

echo "Done! Your repository should now be available at:"
echo "https://github.com/malathon/dayflow"
echo ""
echo "Next steps:"
echo "1. Check GitHub Actions tab for test results"
echo "2. Update repository description and topics"
echo "3. Consider creating a v0.1.0 release"
