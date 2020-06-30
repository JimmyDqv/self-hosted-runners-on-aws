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
    debug_print(json.dumps(event, indent=2))

    message = event['detail']
    if LIFECYCLE_KEY in message and ASG_KEY in message:
        life_cycle_hook = message[LIFECYCLE_KEY]
        auto_scaling_group = message[ASG_KEY]
        instance_id = message[EC2_KEY]
        ssm_document = os.environ[SSM_DOCUMENT_KEY]
        success = run_ssm_command(ssm_document, instance_id)
        result = 'CONTINUE'
        if not success:
            result = 'ABANDON'
        notify_lifecycle(life_cycle_hook, auto_scaling_group,
                         instance_id, result)
    return {}


def debug_print(message):
    logger.debug(message)


def run_ssm_command(ssm_document, instance_id):
    ssm_client = boto3.client('ssm')
    try:
        instances = [str(instance_id)]
        debug_print("DocumentName {}".format(ssm_document))
        debug_print("InstanceIds {}".format(instances))
        response = ssm_client.send_command(DocumentName=ssm_document,
                                           InstanceIds=instances,
                                           Comment='Remove GitHub Runner',
                                           TimeoutSeconds=1200)
        debug_print(response)
    except Exception as e:
        debug_print(e)
        return False
    return True


def notify_lifecycle(life_cycle_hook, auto_scaling_group, instance_id, result):
    asg_client = boto3.client('autoscaling')
    try:
        asg_client.complete_lifecycle_action(
            LifecycleHookName=life_cycle_hook,
            AutoScalingGroupName=auto_scaling_group,
            LifecycleActionResult=result,
            InstanceId=instance_id
        )
    except Exception as e:
        logger.error(
            "Lifecycle hook notified could not be executed: %s", str(e))
        raise e
