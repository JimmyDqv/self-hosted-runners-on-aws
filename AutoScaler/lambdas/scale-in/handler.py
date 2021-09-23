import logging
import json
import os
import boto3
import time

logger = logging.getLogger("scale-in")
logger.setLevel(logging.DEBUG)


def handler(event, context):
    logger.debug(event)

    instance_id = event['AutoScaling']['Runner']
    logger.debug(instance_id)

    if instance_id:
        command_id = runSSMDocument(instance_id)
        logger.debug(f"Document Run: {command_id}")
        if waitForSSMDocumentToFinish(command_id, 90):
            detach_instance(instance_id)
            terminateInstance(instance_id)
        else:
            logger.debug(
                "Timeout or SSM Document failed! There is risc for a loose worker")

        setLastActivityTimeStamp()


def runSSMDocument(instance_id):
    client = boto3.client('ssm')
    response = client.send_command(
        InstanceIds=[
            instance_id,
        ],
        DocumentName=os.environ["REMOVE_DOCUMENT_NAME"],
        TimeoutSeconds=60,
        Comment='Removing GitHub Runner',
    )
    logger.debug(response)
    return response['Command']['CommandId']


def waitForSSMDocumentToFinish(commandId, timeout):
    client = boto3.client('ssm')
    response = client.list_command_invocations(
        CommandId=commandId,
        Details=True
    )

    status = response['CommandInvocations'][0]['Status']
    count = 0
    while status == 'InProgress' or status == 'Pending' or status == 'Delayed':
        if count > (timeout * 2):
            return False

        time.sleep(0.5)
        count = count + 1
        response = client.list_command_invocations(
            CommandId=commandId,
            Details=True
        )
        status = response['CommandInvocations'][0]['Status']

    return True


def detach_instance(instance_id):
    client = boto3.client('autoscaling')
    response = client.detach_instances(
        InstanceIds=[
            instance_id,
        ],
        AutoScalingGroupName=os.environ["ASG"],
        ShouldDecrementDesiredCapacity=True
    )
    logger.debug(response)


def terminateInstance(instance_id):
    client = boto3.client('ec2')
    response = client.terminate_instances(
        InstanceIds=[
            instance_id,
        ],
        DryRun=False
    )
    logger.debug(response)


def setLastActivityTimeStamp():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["SETTINGS_TABLE"])
    table.put_item(Item={
        "PK": "activity_scaling",
        "SK": "scale_in",
        "timestamp": int(round(time.time()))
    })
