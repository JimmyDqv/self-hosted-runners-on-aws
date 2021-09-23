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

    scaling_action = checkCoolDownPassed()

    return scaling_action


def checkCoolDownPassed():
    cooldown = getSetting("cooldown")
    if cooldown:
        last_activity = getLastScalingActivityTime()
        time_now = int(round(time.time()))

        if (time_now - int(last_activity)) < int(cooldown):
            logger.debug("Still Cooling down.....!")
            return "BREAK"

    return "CARRY_ON"


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
