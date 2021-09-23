import logging
import json
import boto3
import os
import hashlib
import hmac

logger = logging.getLogger("httpapi-auth")
logger.setLevel(logging.DEBUG)


def handler(event, context):
    logger.debug(json.dumps(event, indent=2))

    is_authorized = checkHeaders(event['headers'])

    state = {
        "isAuthorized": is_authorized,
        "context": {
        }
    }

    logger.debug(state)

    return state


def checkHeaders(headers):
    if not headers['user-agent'].startswith('GitHub-Hookshot'):
        return False

    if 'x-hub-signature' not in headers:
        return False

    return True


def validateSignature(event):
    client = boto3.client('ssm')
    response = client.get_parameter(
        Name=os.environ["GITHUB_SECRET"],
        WithDecryption=True
    )
    github_secret = response["Parameter"]["Value"]

    github_signature = event['identitySource'][0].split("=")[1]

    signature = hmac.new(
        github_secret, event["body"], hashlib.sha1).hexdigest()
    return github_signature == signature
