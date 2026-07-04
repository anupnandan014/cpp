#!/bin/bash
# Usage: paste your AWS Academy credentials block into a file called
# new_creds.txt in this scripts folder, then run this script.
# The file should look exactly like:
# [default]
# aws_access_key_id=...
# aws_secret_access_key=...
# aws_session_token=...

CREDS_FILE="$(dirname "$0")/new_creds.txt"

if [ ! -f "$CREDS_FILE" ]; then
    echo "ERROR: $CREDS_FILE not found."
    echo "Create it and paste your AWS Academy credentials block into it first."
    exit 1
fi

mkdir -p ~/.aws
cp "$CREDS_FILE" ~/.aws/credentials
echo "AWS credentials updated from $CREDS_FILE"

# Clear any stale environment variable overrides
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN

echo "Testing credentials..."
aws sts get-caller-identity
