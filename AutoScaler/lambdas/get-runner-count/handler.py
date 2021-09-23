import logging
import json
import os
import boto3
import requests

logger = logging.getLogger("get-runner-count")
logger.setLevel(logging.DEBUG)


def handler(event, context):
    logger.debug(event)
    total_count = getRepoRunnerCount()

    return total_count


def getRepoRunnerCount():
    token = getGitHubSecret()
    url = f"https://api.github.com/repos/{os.environ['REPO_OWNER']}/{os.environ['REPO_NAME']}/actions/runners"
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
