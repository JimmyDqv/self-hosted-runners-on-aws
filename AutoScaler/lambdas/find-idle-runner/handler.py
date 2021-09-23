import logging
import json
import os
import boto3
import requests
from datetime import date, datetime

logger = logging.getLogger("list-queued-runs")
logger.setLevel(logging.DEBUG)


def handler(event, context):
    logger.debug(event)

    idle_runner = findIdleRunner()

    return idle_runner


def findIdleRunner():
    token = getGitHubSecret()
    url = f"https://api.github.com/repos/{os.environ['REPO_OWNER']}/{os.environ['REPO_NAME']}/actions/runners"
    header = {'Authorization': 'token {}'.format(token)}
    response = requests.get(url, headers=header)
    jsonData = response.json()

    runners = []
    for runner in jsonData['runners']:
        if runner['status'] == 'online' and runner['busy'] == False:
            # Convert to Instane ID.
            runners.append(runner['name'].split("my-runners-")[1])

    if len(runners) == 0:
        return None
    if len(runners) == 1:
        return runners[0]

    return getOldestInstance(runners)


def getOldestInstance(instance_ids):
    client = boto3.client('ec2')
    response = client.describe_instances(
        InstanceIds=instance_ids,
        DryRun=False
    )

    oldest_instance = None

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if not oldest_instance:
                oldest_instance = instance
            elif instance['LaunchTime'] > oldest_instance['LaunchTime']:
                oldest_instance = instance

    if oldest_instance:
        return oldest_instance['InstanceId']

    return None


def getGitHubSecret():
    client = boto3.client('ssm')
    response = client.get_parameter(
        Name=os.environ["GITHUB_SECRET"],
        WithDecryption=True
    )
    return response["Parameter"]["Value"]
