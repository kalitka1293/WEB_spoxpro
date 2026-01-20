#!/bin/bash
set -e

# Navigate to the project root
cd "$(dirname "$0")/.."

echo "Generating Swagger documentation..."

# If swag is not installed locally, you can use go run
go install github.com/swaggo/swag/cmd/swag@latest

# Run swag init to generate swagger docs
swag init -g cmd/main.go -o docs

echo "Swagger documentation generated successfully!"
echo "You can access the documentation at: http://localhost:8080/swagger/index.html when the server is running."