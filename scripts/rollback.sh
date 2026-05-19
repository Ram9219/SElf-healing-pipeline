#!/bin/bash
# Self-healing rollback script

echo "  =============================================="
echo "  SELF-HEALING: INITIATING ROLLBACK"
echo "  =============================================="

# Stop current containers
echo " Stopping current deployment..."
docker-compose down

# Remove the failed image tag
echo "  Removing failed image..."
docker rmi ram9219/self-healing-app:latest 2>/dev/null || true

# Restart with previous version (if available)
echo " Restarting with previous stable version..."
docker-compose up -d

echo " =============================================="
echo " ROLLBACK COMPLETED SUCCESSFULLY"
echo " =============================================="