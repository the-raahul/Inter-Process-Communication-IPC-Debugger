#!/bin/bash
echo "Checking repository size..."
echo "Current directory size:"
du -sh .

echo -e "\nChecking for large files (>100MB):"
find . -type f -size +100M -exec ls -lh {} \;

echo -e "\nChecking for Python cache files:"
find . -type d -name "__pycache__" -exec ls -lh {} \;
