import json
import logging
import boto3
import os

# Load the exceptions for error handling
from botocore.exceptions import ClientError, ParamValidationError
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sfn_client = boto3.client(
    'stepfunctions', region_name=os.environ.get('AWS_REGION'))
state_machine_arn = os.environ.get("STEP_FUNCTION_ARN")


def dynamodb_obj_to_python_obj(dynamodb_obj: dict) -> dict:
    deserializer = TypeDeserializer()
    return {
        k: deserializer.deserialize(v)
        for k, v in dynamodb_obj.items()
    }


def handler(event, context):

    try:
        logger.info(f"event :: {json.dumps(event)}")

        for record in event["Records"]:
            keys = dynamodb_obj_to_python_obj(
                record["dynamodb"].get("Keys"))
            logger.info(f"handler :: Keys : {json.dumps(keys)}")

            new_image = dynamodb_obj_to_python_obj(
                record["dynamodb"].get("NewImage")
            )
            sf_input = dict(Payload=dict(
                keys=keys,
                message=f"{new_image.get('message')}"
            )
            )

            logger.info(f"handler :: sf_input = {json.dumps(sf_input)}")
            response = sfn_client.start_execution(stateMachineArn=state_machine_arn,
                                                  input=json.dumps(
                                                      sf_input)
                                                  )

            logger.info(f"handler :: response = {response}")
            sf_status_code = response["ResponseMetadata"]["HTTPStatusCode"]
            request_id = response["ResponseMetadata"]["RequestId"]
            execution_arn = response["executionArn"]

            if sf_status_code == 200:
                return_dict = dict(statusCode=200,
                                   executionArn=execution_arn,
                                   RequestId=request_id
                                   )
            else:
                return_dict = dict(statusCode=sf_status_code,
                                   executionArn=execution_arn,
                                   RequestId=request_id
                                   )

    # An error occurred
    except ParamValidationError as e:
        logger.error(f"handler :: Parameter validation error: {e}")
        return_dict = dict(StatusCode=response["ResponseMetadata"]["HTTPStatusCode"],
                           errorMessage=f"Parameter validation error: {e}")
    except ClientError as e:
        logger.error(f"handler :: Client error: {e}")
        return_dict = dict(
            StatusCode=response["ResponseMetadata"]["HTTPStatusCode"], errorMessage=f"Client error:: {e}")

    return return_dict
