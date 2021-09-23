import logging
import json
import os
import boto3
import requests
import time

logger = logging.getLogger("check-scaling")
logger.setLevel(logging.DEBUG)


def handler(event, context):
    logger.debug(event)

    scaling_action = getScalingActionNeeded(event)

    return scaling_action


def getScalingActionNeeded(event):
    # Implement the logic you like around scale in/out!
    cooldown = getSetting("cooldown")
    if cooldown:
        last_activity = getLastScalingActivityTime()
        time_now = int(round(time.time()))

        if (time_now - int(last_activity)) < int(cooldown):
            logger.debug("Cooling down.....!")
            return "no_op"

    if isASGscaledOutToMaxNodes():
        return "no_op"

    queued_count = getQueuedWorkFlowsCount(event)
    worker_node_count = getNumberOfWorkerNodes(event)

    logger.debug(f"Queued Workflows: {queued_count}")
    logger.debug(f"Runner Count: {worker_node_count}")
    if queued_count < worker_node_count:
        logger.debug("Scale Down!")
        if isASGscaledInToMinNodes():
            logger.debug("Already at minimum....")
            return "no_op"
        return "scale_in"

    # Adapt after need, each runner handle 5 builds.
    if queued_count > worker_node_count * 5:
        logger.debug("Scale Up!")
        return "scale_out"

    return "no_op"


def getLastScalingActivityTime():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["SETTINGS_TABLE"])
    response = table.get_item(Key={"PK": "activity_scaling"})
    return response["Item"]["timestamp"]


def getSetting(setting):
    dynamodb = boto3.client('dynamodb')

    response = dynamodb.query(
        TableName=os.environ["SETTINGS_TABLE"],
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={
            ':pk': {'S': f"settings_{setting}"}
        }
    )

    if len(response['Items']) > 0:
        return response["Item"]["value"]

    return None


def getNumberOfWorkerNodes(event):
    return event['AutoScaling']['RunnerCount']


def getQueuedWorkFlowsCount(event):
    return event['AutoScaling']['QueuedRunsCount']


def getGitHubSecret():
    client = boto3.client('ssm')
    response = client.get_parameter(
        Name=os.environ["GITHUB_SECRET"],
        WithDecryption=True
    )
    return response["Parameter"]["Value"]


def isASGscaledOutToMaxNodes():
    client = boto3.client('autoscaling')
    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            os.environ["ASG"],
        ]
    )

    return response["AutoScalingGroups"][0]["DesiredCapacity"] >= response["AutoScalingGroups"][0]["MaxSize"]


def isASGscaledInToMinNodes():
    client = boto3.client('autoscaling')
    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            os.environ["ASG"],
        ]
    )

    return response["AutoScalingGroups"][0]["DesiredCapacity"] <= response["AutoScalingGroups"][0]["MinSize"]
