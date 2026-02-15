#!/bin/bash
# Daily Cost & MTD Summary Script
# Generates a report for Today + Month-to-Date

SESSIONS_DIR="$HOME/.openclaw/agents"
YEAR_MONTH=$(date +%Y-%m)
TODAY=$(date +%Y-%m-%d)

# Extract all relevant JSON lines for the current month
# We use a temporary file to avoid pipe issues
TMP_LOGS=$(mktemp)
find "$SESSIONS_DIR" -name "*.jsonl" -print0 | xargs -0 grep -a "\"timestamp\":\"$YEAR_MONTH" > "$TMP_LOGS"

# Use Python for robust JSON parsing and summation
python3 -c "
import sys, json, datetime

today_str = '$TODAY'
month_str = '$YEAR_MONTH'

total_cost_today = 0.0
total_cost_mtd = 0.0
providers = {}
models = {}

with open('$TMP_LOGS', 'r') as f:
    for line in f:
        try:
            # grep matches might include filename prefix if not careful, but json.loads might fail
            # we look for the first {
            idx = line.find('{')
            if idx == -1: continue
            json_str = line[idx:]
            
            data = json.loads(json_str)
            
            # Extract usage
            usage = data.get('message', {}).get('usage', {})
            if not usage: continue
            
            cost = float(usage.get('cost', {}).get('total', 0) or 0)
            if cost == 0: continue
            
            ts = data.get('timestamp', '')
            model = data.get('message', {}).get('model', 'unknown')
            
            # Provider inference
            if '/' in model:
                provider = model.split('/')[0]
            else:
                provider = 'other'
            
            # MTD Sum
            if ts.startswith(month_str):
                total_cost_mtd += cost
                
                # Provider Breakdown (MTD)
                providers[provider] = providers.get(provider, 0.0) + cost
                
                # Model Breakdown (MTD)
                models[model] = models.get(model, 0.0) + cost

            # Today Sum
            if ts.startswith(today_str):
                total_cost_today += cost

        except Exception as e:
            continue

# Formatting Report
print(f\"💰 **Daily Cost Report: {today_str}**\")
print(f\"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\")
print(f\"**Today:** \${total_cost_today:.2f}\")
print(f\"**Month-to-Date:** \${total_cost_mtd:.2f}\")

print(f\"\\n📊 **Provider Breakdown (MTD):**\")
sorted_providers = sorted(providers.items(), key=lambda x: x[1], reverse=True)
if not sorted_providers:
    print(\"(No cost data)\")
for p, c in sorted_providers:
    print(f\"• {p}: \${c:.2f}\")

print(f\"\\n📉 **Top Models (MTD):**\")
sorted_models = sorted(models.items(), key=lambda x: x[1], reverse=True)[:10]
if not sorted_models:
    print(\"(No cost data)\")
for m, c in sorted_models:
    print(f\"• {m}: \${c:.2f}\")
"

rm "$TMP_LOGS"
