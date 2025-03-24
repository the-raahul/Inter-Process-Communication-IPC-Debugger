#!/bin/bash
echo "Starting verification..."

# Check essential files exist
echo "Checking required files..."
if [ ! -f "main.py" ]; then
    echo "❌ Missing: main.py"
else
    echo "✅ Found: main.py"
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Missing: requirements.txt"
else
    echo "✅ Found: requirements.txt"
fi

if [ ! -f "README.md" ]; then
    echo "❌ Missing: README.md"
else
    echo "✅ Found: README.md"
fi

if [ ! -f "LICENSE" ]; then
    echo "❌ Missing: LICENSE"
else
    echo "✅ Found: LICENSE"
fi

if [ ! -f "CHANGELOG.md" ]; then
    echo "❌ Missing: CHANGELOG.md"
else
    echo "✅ Found: CHANGELOG.md"
fi

if [ ! -f ".gitignore" ]; then
    echo "❌ Missing: .gitignore"
else
    echo "✅ Found: .gitignore"
fi

# Check directory structure
echo -e "\nChecking required directories..."
if [ ! -d "ipc_debugger" ]; then
    echo "❌ Missing: ipc_debugger directory"
else
    echo "✅ Found: ipc_debugger directory"
fi

echo -e "\nVerification complete!"
