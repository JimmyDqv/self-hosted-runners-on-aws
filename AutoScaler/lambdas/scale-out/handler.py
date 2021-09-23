import logging
import json
import os
import boto3
import time

logger = logging.getLogger("scale-out")
logger.setLevel(logging.DEBUG)


def handler(event, context):
    logger.debug(event)

    if isASGscaledOutToMaxNodes():
        logger.debug("Already running with max number of runners, ignoring!")
    else:
        current_node_count = getNodeCount()
        setNodeCount(current_node_count + 1)

    setLastActivityTimeStamp()


def isASGscaledOutToMaxNodes():
    client = boto3.client('autoscaling')
    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            os.environ["ASG"],
        ]
    )

    return response["AutoScalingGroups"][0]["DesiredCapacity"] >= response["AutoScalingGroups"][0]["MaxSize"]


def getNodeCount():
    client = boto3.client('autoscaling')
    response = client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[
            os.environ["ASG"],
        ]
    )

    return response["AutoScalingGroups"][0]["DesiredCapacity"]


def setNodeCount(node_count):
    client = boto3.client('autoscaling')
    response = client.set_desired_capacity(
        AutoScalingGroupName=os.environ["ASG"],
        DesiredCapacity=node_count,
        HonorCooldown=True
    )
    logger.debug(response)


def setLastActivityTimeStamp():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["SETTINGS_TABLE"])
    table.put_item(Item={
        "PK": "activity_scaling",
        "SK": "scale_out",
        "timestamp": int(round(time.time()))
    })
