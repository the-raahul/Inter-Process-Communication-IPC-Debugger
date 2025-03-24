#!/bin/bash
echo "Cleaning up Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo "Cleaning up OS specific files..."
find . -type f -name ".DS_Store" -delete
find . -type f -name "Thumbs.db" -delete

echo "Cleaning up IDE specific files..."
find . -type d -name ".idea" -exec rm -rf {} +
find . -type d -name ".vscode" -exec rm -rf {} +

echo "Cleanup complete!"
