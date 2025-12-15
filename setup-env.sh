#!/bin/bash
# Setup script for environment variables

echo "Setting up environment variables..."

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Prompt for API keys
echo ""
echo "Enter your Grok API keys (comma-separated if multiple):"
read -p "GROK_API_KEYS: " grok_keys

# Set default backend URL
backend_url="http://localhost:8000"
read -p "Backend URL [$backend_url]: " input_backend
backend_url=${input_backend:-$backend_url}

# Create .env file
cat > .env << EOF
# Grok API Keys (comma-separated if multiple)
GROK_API_KEYS=$grok_keys

# Backend URL
BACKEND_URL=$backend_url
EOF

echo ""
echo "✅ .env file created successfully!"
echo ""
echo "You can now run: docker-compose up -d"
