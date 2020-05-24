#!/bin/bash
set -e

mkdir actions-runner && cd actions-runner
curl -O -L https://github.com/actions/runner/releases/download/v2.169.1/actions-runner-linux-x64-2.169.1.tar.gz
tar xzf ./actions-runner-linux-x64-2.169.1.tar.gz

PAT=<super secret GitHub PAT>

# Get Token
token=$(curl -s -XPOST \
    -H "authorization: token ${PAT}" \
    https://api.github.com/repos/<GitHub User>/<GitHUb Repo>/actions/runners/registration-token |\
    jq -r .token)

./config.sh --url <GitHub repo Url> --token $token --name "aws-runner-$(hostname)" --work _work
./run.sh
