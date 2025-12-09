#!/bin/bash
#
# FX Smart Routing - GitHub Integration Script
# 
# This script prepares the FX Smart Routing Engine for integration
# with the existing FX-MS repository: https://github.com/joshmo01/FX-MS
#
# Author: Fintaar.ai
# Version: 1.0.0
#

set -e

echo "=========================================="
echo "🚀 FX Smart Routing - GitHub Integration"
echo "=========================================="

# Configuration
REPO_URL="https://github.com/joshmo01/FX-MS.git"
BRANCH_NAME="feature/smart-routing-multi-rail"
SOURCE_DIR="$(pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n${YELLOW}Step 1: Pre-flight checks${NC}"
echo "----------------------------------------------"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed${NC}"
    exit 1
fi
echo "✅ Git is available"

# Check required files exist
required_files=(
    "app/services/smart_routing_engine.py"
    "app/services/multi_rail_engine.py"
    "app/services/universal_conversion_engine.py"
    "app/services/cbdc_stable_bridge.py"
    "app/api/routing_api.py"
    "app/api/multi_rail_api.py"
    "app/api/bridge_api.py"
    "config/routing_config.json"
    "config/digital_currencies.json"
    "config/digital_rails.json"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [[ -f "$SOURCE_DIR/$file" ]]; then
        echo "✅ Found: $file"
    else
        echo -e "${RED}❌ Missing: $file${NC}"
        exit 1
    fi
done

echo -e "\n${YELLOW}Step 2: Preparing for integration${NC}"
echo "----------------------------------------------"

# Create integration directory structure
INTEGRATION_DIR="/tmp/fx-ms-integration"
rm -rf "$INTEGRATION_DIR"
mkdir -p "$INTEGRATION_DIR"

echo "📁 Created integration directory: $INTEGRATION_DIR"

# Clone the repository
echo -e "\n${YELLOW}Step 3: Cloning FX-MS repository${NC}"
echo "----------------------------------------------"
echo "Repository: $REPO_URL"

cd "$INTEGRATION_DIR"
git clone "$REPO_URL" fx-ms
cd fx-ms

echo "✅ Repository cloned"

# Create feature branch
echo -e "\n${YELLOW}Step 4: Creating feature branch${NC}"
echo "----------------------------------------------"
git checkout -b "$BRANCH_NAME"
echo "✅ Created branch: $BRANCH_NAME"

# Copy Smart Routing files
echo -e "\n${YELLOW}Step 5: Copying Smart Routing files${NC}"
echo "----------------------------------------------"

# Create directories if they don't exist
mkdir -p app/services
mkdir -p app/api
mkdir -p app/models
mkdir -p app/static
mkdir -p config
mkdir -p tests

# Copy service files
echo "📋 Copying services..."
cp "$SOURCE_DIR/app/services/smart_routing_engine.py" app/services/
cp "$SOURCE_DIR/app/services/multi_rail_engine.py" app/services/
cp "$SOURCE_DIR/app/services/universal_conversion_engine.py" app/services/
cp "$SOURCE_DIR/app/services/cbdc_stable_bridge.py" app/services/

# Copy API files
echo "📋 Copying API routers..."
cp "$SOURCE_DIR/app/api/routing_api.py" app/api/
cp "$SOURCE_DIR/app/api/multi_rail_api.py" app/api/
cp "$SOURCE_DIR/app/api/bridge_api.py" app/api/

# Copy model files
echo "📋 Copying models..."
cp "$SOURCE_DIR/app/models/"*.py app/models/ 2>/dev/null || echo "No model files to copy"

# Copy config files
echo "📋 Copying configurations..."
cp "$SOURCE_DIR/config/"*.json config/

# Copy static files
echo "📋 Copying static files..."
cp "$SOURCE_DIR/app/static/"*.jsx app/static/ 2>/dev/null || echo "No static files to copy"

# Copy test files
echo "📋 Copying tests..."
cp "$SOURCE_DIR/tests/"*.py tests/

# Copy documentation
echo "📋 Copying documentation..."
cp "$SOURCE_DIR/README.md" SMART_ROUTING_README.md

echo "✅ All files copied"

# Update main.py to include new routers
echo -e "\n${YELLOW}Step 6: Updating main.py${NC}"
echo "----------------------------------------------"

# Check if main.py exists
if [[ -f "app/main.py" ]]; then
    # Add router imports if not already present
    if ! grep -q "routing_api" app/main.py; then
        cat >> app/main.py << 'EOF'

# Smart Routing APIs (added by integration script)
from app.api.routing_api import router as routing_router
from app.api.multi_rail_api import router as multi_rail_router
from app.api.bridge_api import router as bridge_router

app.include_router(routing_router)
app.include_router(multi_rail_router)
app.include_router(bridge_router)
EOF
        echo "✅ Updated main.py with new routers"
    else
        echo "ℹ️  Routers already configured in main.py"
    fi
else
    echo "⚠️  main.py not found - you'll need to manually add routers"
fi

# Update requirements.txt
echo -e "\n${YELLOW}Step 7: Updating requirements.txt${NC}"
echo "----------------------------------------------"

if [[ -f "requirements.txt" ]]; then
    # Add new dependencies if not present
    DEPS=("pydantic>=2.0" "aiohttp>=3.8" "httpx>=0.24")
    for dep in "${DEPS[@]}"; do
        base_dep=$(echo "$dep" | cut -d'>' -f1 | cut -d'=' -f1)
        if ! grep -qi "$base_dep" requirements.txt; then
            echo "$dep" >> requirements.txt
            echo "  Added: $dep"
        fi
    done
    echo "✅ Updated requirements.txt"
else
    echo "⚠️  requirements.txt not found"
fi

# Stage files for commit
echo -e "\n${YELLOW}Step 8: Staging files for commit${NC}"
echo "----------------------------------------------"
git add -A
git status --short

# Create commit
echo -e "\n${YELLOW}Step 9: Creating commit${NC}"
echo "----------------------------------------------"

git commit -m "feat: Add FX Smart Routing with Multi-Rail Support

This commit adds comprehensive FX routing capabilities:

## Features
- Smart FX routing engine with 4 optimization objectives
- Multi-rail routing (Fiat + CBDC + Stablecoin)
- CBDC support: e-INR, e-CNY, e-HKD, e-THB, e-AED, e-SGD
- Stablecoin support: USDC, USDT, EURC, PYUSD, XSGD
- mBridge cross-border CBDC integration
- Customer tier pricing (Platinum → Retail)
- Treasury position management

## New Endpoints
- POST /api/v1/fx/routing/recommend
- POST /api/v1/fx/multi-rail/route
- POST /api/v1/fx/bridge/route
- GET /api/v1/fx/bridge/cbdc-to-stable/{cbdc}/{stablecoin}
- GET /api/v1/fx/bridge/stable-to-cbdc/{stablecoin}/{cbdc}

## Configuration
- 7 FX providers configured
- 5 customer tiers with volume discounts
- 6 CBDCs with pilot status
- 5 stablecoins across multiple networks
- 5 on/off ramp providers

Author: Fintaar.ai"

echo "✅ Commit created"

# Show instructions for pushing
echo -e "\n${GREEN}=========================================="
echo "✅ Integration Complete!"
echo "==========================================${NC}"
echo ""
echo "📍 Integration directory: $INTEGRATION_DIR/fx-ms"
echo "📍 Branch: $BRANCH_NAME"
echo ""
echo "Next steps:"
echo "  1. cd $INTEGRATION_DIR/fx-ms"
echo "  2. Review changes: git diff main"
echo "  3. Push to GitHub: git push origin $BRANCH_NAME"
echo "  4. Create Pull Request on GitHub"
echo ""
echo "Or run these commands:"
echo "  cd $INTEGRATION_DIR/fx-ms && git push -u origin $BRANCH_NAME"
echo ""
