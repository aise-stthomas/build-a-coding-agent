#!/usr/bin/env bash
# Deploy the payments server as a function behind a URL (Streamable HTTP), in the AWS Academy
# Learner Lab. Prints the URL; put it in servers.toml, or run with PAYMENTS_URL=<url>.
#
# Assumes: the AWS CLI with a live Learner Lab session in ~/.aws/credentials, us-east-1, the
# pre-created LabRole. Creates one function and one HTTP API. teardown.sh removes both.
set -euo pipefail
cd "$(dirname "$0")"
FN="${FUNCTION_NAME:-payments-mcp}"; API="${API_NAME:-payments-mcp}"
export AWS_DEFAULT_REGION=us-east-1 AWS_PAGER=""

ACCOUNT="$(aws sts get-caller-identity --query Account --output text 2>/dev/null)" \
  || { echo "aws sts get-caller-identity failed: start a Learner Lab session and paste fresh credentials"; exit 1; }
ROLE="arn:aws:iam::${ACCOUNT}:role/LabRole"

echo "building the package..."
mkdir -p build && ( rm -f build/payments.zip; zip -qr build/payments.zip src data/desk -x '*__pycache__*' )

if aws lambda get-function --function-name "$FN" >/dev/null 2>&1; then
  aws lambda update-function-code --function-name "$FN" --zip-file fileb://build/payments.zip >/dev/null
else
  aws lambda create-function --function-name "$FN" --runtime python3.12 --role "$ROLE" \
    --handler src.function.handler.handler --zip-file fileb://build/payments.zip --timeout 15 --memory-size 256 >/dev/null
fi
aws lambda wait function-updated --function-name "$FN"
ARN="$(aws lambda get-function --function-name "$FN" --query Configuration.FunctionArn --output text)"

ID="$(aws apigatewayv2 get-apis --query "Items[?Name=='${API}'].ApiId | [0]" --output text)"
if [ -z "$ID" ] || [ "$ID" = "None" ]; then
  ID="$(aws apigatewayv2 create-api --name "$API" --protocol-type HTTP --target "$ARN" --query ApiId --output text)"
  aws lambda add-permission --function-name "$FN" --statement-id apigw --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:${ACCOUNT}:${ID}/*" >/dev/null
fi
URL="https://${ID}.execute-api.us-east-1.amazonaws.com/mcp"
echo "payments server: $URL"
echo "try it:  PAYMENTS_URL=$URL uv run main_2_servers.py"
