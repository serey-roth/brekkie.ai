#!/bin/bash

# Deployment script with staging first
set -e

echo "🚀 Starting deployment process..."

# Check if we're in the right directory
if [ ! -f "fly.toml" ]; then
    echo "❌ Error: fly.toml not found. Are you in the project root?"
    exit 1
fi

# Step 1: Deploy to staging
echo "📋 Step 1: Deploying to staging..."
fly deploy --config fly.staging.toml

# Step 2: Wait for staging to be healthy
echo "⏳ Step 2: Waiting for staging to be healthy..."
sleep 30

# Step 3: Test staging (you can add more tests here)
echo "🧪 Step 3: Testing staging deployment..."
curl -f https://brekkie-ai-staging.fly.dev/api/health || {
    echo "❌ Staging health check failed!"
    exit 1
}

echo "✅ Staging deployment successful!"

# Step 4: Ask for confirmation before production
read -p "🤔 Deploy to production? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Step 4: Deploying to production..."
    fly deploy --strategy rolling
    
    echo "✅ Production deployment complete!"
    echo "🌐 Production URL: https://brekkie-ai.fly.dev"
    echo "🧪 Staging URL: https://brekkie-ai-staging.fly.dev"
else
    echo "⏹️  Deployment cancelled. Staging is available at: https://brekkie-ai-staging.fly.dev"
fi 