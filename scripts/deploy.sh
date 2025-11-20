#!/bin/bash
#
# Deployment script for Ventus fan controller
#
# Usage: ./scripts/deploy.sh [target_host]
#
# Example: ./scripts/deploy.sh root@bananapi

set -e

TARGET_HOST="${1:-root@bananapi}"
DEPLOY_PATH="/opt/ventus"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==================================="
echo "Ventus Deployment Script"
echo "==================================="
echo "Target: $TARGET_HOST"
echo "Deploy path: $DEPLOY_PATH"
echo "Project dir: $PROJECT_DIR"
echo ""

# Create tarball
echo "[1/4] Creating deployment tarball..."
cd "$PROJECT_DIR"
tar czf /tmp/ventus-deploy.tar.gz \
    ventus/ \
    requirements.txt \
    setup.py \
    config/ \
    examples/ \
    tests/ \
    README.md \
    CHANGELOG.md \
    LICENSE

echo "[2/4] Copying to target..."
scp /tmp/ventus-deploy.tar.gz "$TARGET_HOST:/tmp/"

echo "[3/4] Extracting on target..."
ssh "$TARGET_HOST" "mkdir -p $DEPLOY_PATH && cd $DEPLOY_PATH && tar xzf /tmp/ventus-deploy.tar.gz"

echo "[4/4] Installing dependencies..."
ssh "$TARGET_HOST" "cd $DEPLOY_PATH && pip3 install --break-system-packages -r requirements.txt"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "To start on target:"
echo "  ssh $TARGET_HOST"
echo "  cd $DEPLOY_PATH"
echo "  python3 -m ventus.server  # (if gRPC enabled)"
echo ""
