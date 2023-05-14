import json
import logging
import boto3
import os

# Load the exceptions for error handling
from botocore.exceptions import ClientError, ParamValidationError
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

logger = logging.getLogger()
logger.setLevel(logging.INFO)

metric_name = os.environ.get("METRIC_NAME")
dimension_name = os.environ.get("DIMENSION_NAME")
dimension_value = os.environ.get("DIMENSION_VALUE")
sns_topic_arn = os.getenv("SNS_TOPIC_ARN")
cloud_watch_name_space = os.environ.get("CLOUD_WATCH_NAME_SPACE")
dynamodb_table = os.environ.get("DYNAMODB_TABLE_NAME")
dynamodb_client = boto3.client(
    "dynamodb", region_name=os.environ.get("AWS_REGION"))

cloud_watch_client = boto3.client(
    "cloudwatch", region_name=os.environ.get("AWS_REGION"))

sns_client = boto3.client('sns', region_name=os.getenv('AWS_REGION'))


def update_send_status(key_value):
    try:
        logger.info(f"update_send_status :: key_value = {key_value}")
        response = dynamodb_client.update_item(
                   ExpressionAttributeNames={
                    '#SS': 'sendStatus'
                    },
                    ExpressionAttributeValues={
                        ':s':{
                            'S':'Successful'
                        }
                    },
                    Key={
                        'sequenceNo':{
                            'S': key_value
                        }
                    },
                    ReturnValues='ALL_NEW',
                    TableName=dynamodb_table,
                    UpdateExpression='SET #SS = :s',
            )
        
        
        logger.info(f"response :: {json.dumps(response)}")

        return response
    # An error occurred
    except ParamValidationError as e:
        logger.error(f"Parameter validation error: {e}")
        dict_return = dict(
            StatusCode=400, message=f"Parameter validation error: {e}")
    except ClientError as e:
        logger.error(f"Client error: {e}")
        dict_return = dict(
            StatusCode=400, message=f"Parameter validation error: {e}")
    return dict_return


def send_sns_message(topic_arn, message):

    logger.info(f"message = {message}")

    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject='Disa - Notification Message',
        )
        logger.info(
            f'send_sns_message :: Message published to the SNS Topic {topic_arn}')

        dict_return = dict(
            StatusCode=response["ResponseMetadata"]["HTTPStatusCode"], RequestId=response["ResponseMetadata"]["RequestId"], message="success"
        )
    # An error occurred
    except ParamValidationError as e:
        logger.error(f"send_sns_message :: Parameter validation error: {e}")
        dict_return = dict(
            StatusCode=400, RequestId=None,message=f"Parameter validation error: {e}")
    except ClientError as e:
        logger.error(f"send_sns_message :: Client error: {e}")
        dict_return = dict(
            StatusCode=400,RequestId=None, message=f"Parameter validation error: {e}")
    return dict_return


def put_metric_data(metric_value):
    try:
        metric_data = []
        metric_data.append(dict(MetricName=metric_name,
                                Dimensions=[
                                    dict(Name=dimension_name, Value=dimension_value)],
                                StorageResolution=1,
                                Unit='Count',
                                Value=metric_value
                                ))
        logger.info(f"metric_data = {json.dumps(metric_data)}")
        response = cloud_watch_client.put_metric_data(
            Namespace=cloud_watch_name_space,
            MetricData=metric_data
        )

        logger.info(f"put_metric_data :: metric_data = {response}")

        dict_return = dict(
            statusCode=response["ResponseMetadata"]["HTTPStatusCode"], message=json.dumps(
                response)
        )

    # An error occurred
    except ParamValidationError as e:
        logger.error(f"put_metric_data :: Parameter validation error: {e}")
        dict_return = dict(
            StatusCode=response["ResponseMetadata"]["HTTPStatusCode"], message=f"Parameter validation error: {e}")
    except ClientError as e:
        dict_return = dict(
            StatusCode=response["ResponseMetadata"]["HTTPStatusCode"], message=f"Parameter validation error: {e}")
    logger.info(f"put_metric_data :: dict_return = {json.dumps(dict_return)}")
    return dict_return


def handler(event, context):
    try:
        logger.info(f"handler :: event = {json.dumps(event)}")
        sns_message = event["Payload"]["message"]
        sequence_no = event["Payload"]["keys"]["sequenceNo"]
        logger.info(f"sns_message = {sns_message} - sequence_no = {sequence_no}")
        response = send_sns_message(sns_topic_arn, sns_message)
        logger.info(f"handler :: response = {json.dumps(response)}")
        send_sns_status_code = response["StatusCode"]
        request_id = response["RequestId"]
        logger.info(f"handler :: response = {json.dumps(response)}")
        logger.info(f"handler :: send_sns_status_code = {send_sns_status_code}")

        response = put_metric_data(send_sns_status_code)
        put_metric_data_status_code = json.loads(response['message'])[
            'ResponseMetadata']['HTTPStatusCode']
        logger.info(
            f"handler :: put_metric_data_status_code = {put_metric_data_status_code}")

        update_table_status_code = 0
        if send_sns_status_code == 200:
            response = update_send_status(sequence_no)
            update_table_status_code = response["ResponseMetadata"]["HTTPStatusCode"]

        if send_sns_status_code == 200 and put_metric_data_status_code == 200 and update_table_status_code == 200:
            dict_return = dict(StatusCode=send_sns_status_code,
                                RequestId=request_id,
                                SendStatus="Success",
                                keys=event["Payload"]["keys"],
                                message=event["Payload"]["message"]
                                )
        else:
            dict_return = dict(StatusCode=(send_sns_status_code + put_metric_data_status_code + update_table_status_code),
                                RequestId=None,
                                SendStatus="Failure",
                                keys=event["Payload"]["keys"],
                                message=event["Payload"]["message"]
                                )
    # An error occurred
    except ParamValidationError as e:
        logger.error(f"handler :: Parameter validation error: {e}")
        dict_return = dict(
            StatusCode=response["ResponseMetadata"]["HTTPStatusCode"], message=f"Parameter validation error: {e}")
    except ClientError as e:
        dict_return = dict(
            StatusCode=response["ResponseMetadata"]["HTTPStatusCode"], message=f"Parameter validation error: {e}")
    logger.info(f"handler :: dict_return = {json.dumps(dict_return)}")
    return dict_return
