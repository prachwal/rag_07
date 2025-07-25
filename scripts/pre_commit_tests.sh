#!/bin/bash
# pre_commit_tests.sh - Pre-commit validation script
# Must pass before any commit is allowed

set -e

echo "🚦 Pre-commit Validation"
echo "======================="

# Check if we're in git repository
if [ ! -d .git ]; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Run complete test suite
echo "Running complete test suite..."
./scripts/test_all.sh

# Check git status
echo ""
echo "📋 Git Status Check"
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Changes detected:"
    git status --short
else
    echo "✅ Working directory clean"
fi

echo ""
echo "🎉 Pre-commit validation passed!"
echo "✅ Code is ready for commit"
