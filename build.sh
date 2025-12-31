#!/bin/bash

# Build script for TailAdmin integration
echo "Building TailAdmin CSS..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js to build CSS."
    echo "You can install it from: https://nodejs.org/"
    exit 1
fi

# Check if npm dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Build CSS
echo "Compiling Tailwind CSS..."
npm run build-css

echo "✅ TailAdmin CSS build complete!"
echo "📁 Output: static/css/tailwind.min.css"
echo ""
echo "For development with auto-rebuild:"
echo "npm run watch-css"