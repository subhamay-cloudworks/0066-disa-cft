import json
import logging
import boto3
import os

# Load the exceptions for error handling
from botocore.exceptions import ClientError, ParamValidationError
from boto3.dynamodb.conditions import Key

dynamodb_table_name = os.environ.get("DYNAMODB_TABLE_NAME")
sns_topic_arn = os.getenv("SNS_TOPIC_ARN")
state_machine_arn = os.environ.get("STEP_FUNCTION_ARN")

dynamodb_resource = boto3.resource('dynamodb', region_name=os.environ.get("AWS_REGION"))
dynamodb_table = dynamodb_resource.Table(dynamodb_table_name)
sns_client = boto3.client('sns', region_name=os.getenv('AWS_REGION'))
sfn_client = boto3.client('stepfunctions', region_name=os.environ.get('AWS_REGION'))


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_failed_records(index_name):
    try:
        response = dynamodb_table.query(
                                        IndexName=index_name,
                                        KeyConditionExpression=Key('sendStatus').eq('Failure'),
        )
        return_dict = response
    except ParamValidationError as e:
        logger.error(f"Parameter validation error: {e}")
        return_dict = dict(StatusCode=300,message=f"Parameter validation error: {e}")
    except ClientError as e:
        logger.error(f"Client error: {e}")
        return_dict = dict(StatusCode=300,message=f"Client error: {e}")
        
    return return_dict
    
def handler(event, context):
    logger.info(f"event :: {json.dumps(event)}")
    logger.info(f"sns_topic_arn = {sns_topic_arn}")

    try:
        response = sns_client.get_topic_attributes(TopicArn=sns_topic_arn)
        # logger.info(f"handler :: sns_attributes response = {json.dumps(response)}")
        
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            logger.info(f"SNS Topic exists.")
            response = get_failed_records("GSI-sendStatus")
            logger.info(f"handler :: get_failed_records response = {json.dumps(response.get('Items'))}")
            return_dict = []
            for item in response.get('Items'):
                sf_input = dict(Payload=dict(
                                            keys=dict(sequenceNo=item.get("sequenceNo")),
                                            message=item.get("message")
                                            )
                                )
                logger.info(f"Payload = {json.dumps(sf_input)}")
                
                logger.info(f"handler :: sf_input = {json.dumps(sf_input)}")
                response = sfn_client.start_execution(stateMachineArn=state_machine_arn,
                                                     input=json.dumps(sf_input)
                                                     )
                logger.info(f"handler :: response = {response}")
                sf_status_code = response["ResponseMetadata"]["HTTPStatusCode"]
                request_id = response["ResponseMetadata"]["RequestId"]
                execution_arn = response["executionArn"]
                


                if sf_status_code == 200:
                    return_dict.append(dict(StatusCode=200,
                                            executionArn=execution_arn,
                                            RequestId=request_id
                                            )
                                       )
                else:
                    return_dict.append(dict(StatusCode=sf_status_code,
                                            executionArn=None,
                                            RequestId=None
                                            )
                                      )

    # An error occurred
    except ParamValidationError as e:
        logger.error(f"Parameter validation error: {e}")
        return_dict = dict(StatusCode=300,message=f"Parameter validation error: {e}")
    except ClientError as e:
        logger.error(f"Client error: {e}")
        return_dict = dict(StatusCode=300,message=f"Client error: {e}")
    return return_dict