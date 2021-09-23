import logging
import json
import os
import boto3
import requests

logger = logging.getLogger("list-queued-runs")
logger.setLevel(logging.DEBUG)


def handler(event, context):
    logger.debug(event)

    queued_runs = getQueuedWorkFlowsCount()

    return queued_runs


def getQueuedWorkFlowsCount():
    token = getGitHubSecret()
    url = f"https://api.github.com/repos/{os.environ['REPO_OWNER']}/{os.environ['REPO_NAME']}/actions/runs?status=queued"
    header = {'Authorization': 'token {}'.format(token)}
    response = requests.get(url, headers=header)
    jsonData = response.json()
    return jsonData["total_count"]


def getGitHubSecret():
    client = boto3.client('ssm')
    response = client.get_parameter(
        Name=os.environ["GITHUB_SECRET"],
        WithDecryption=True
    )
    return response["Parameter"]["Value"]
