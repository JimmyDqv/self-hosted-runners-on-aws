import logging
import json
import os
import boto3

logger = logging.getLogger("terminate-hook")
logger.setLevel(logging.DEBUG)

LIFECYCLE_KEY = "LifecycleHookName"
ASG_KEY = "AutoScalingGroupName"
EC2_KEY = "EC2InstanceId"
SSM_DOCUMENT_KEY = "SSM_DOCUMENT_NAME"


def handler(event, context):
    logger.debug(json.dumps(event, indent=2))

    message = event['detail']
    if LIFECYCLE_KEY in message and ASG_KEY in message:
        logger.debug("Running SSM Command")
        instance_id = message[EC2_KEY]
        ssm_document = os.environ[SSM_DOCUMENT_KEY]
        success = runSsmCommand(ssm_document, instance_id)
    return {}


def runSsmCommand(ssm_document, instance_id):
    logger.debug(f"Run {ssm_document} on {instance_id}")
    ssm_client = boto3.client('ssm')
    try:
        instances = [str(instance_id)]
        response = ssm_client.send_command(DocumentName=ssm_document,
                                           InstanceIds=instances,
                                           Comment='Remove GitHub Runner',
                                           TimeoutSeconds=1200)
        logger.debug(response)
    except Exception as e:
        logger.error(e)
        return False
    return True
