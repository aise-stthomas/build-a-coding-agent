#!/usr/bin/env bash
# Remove the function and the API that deploy.sh made.
set -uo pipefail
cd "$(dirname "$0")"
FN="${FUNCTION_NAME:-payments-mcp}"; API="${API_NAME:-payments-mcp}"
export AWS_DEFAULT_REGION=us-east-1 AWS_PAGER=""
ID="$(aws apigatewayv2 get-apis --query "Items[?Name=='${API}'].ApiId | [0]" --output text 2>/dev/null)"
if [ -n "$ID" ] && [ "$ID" != "None" ]; then aws apigatewayv2 delete-api --api-id "$ID" && echo "deleted the API $API"; else echo "no API $API"; fi
aws lambda delete-function --function-name "$FN" 2>/dev/null && echo "deleted the function $FN" || echo "no function $FN"
