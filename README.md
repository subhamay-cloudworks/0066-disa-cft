# Project Disa: Step Function Demo using DynamoDB, Lambda,SNS and CloudWatch Alarm

A user who wants to sends a message to a SNS Topic inserts the same into a DynamoDB table. A stp function reads the message and sends it to a SNS Topic with exception handling. The enrire stack is created using AWS CloudFormation

## Description

This sample project demonstrates the capability of a step function to send a message to a SNS Topic with exception handling. A user creates an item in a DynamoDB table. The DynamoDB stream enabled on the table with subscription filter to only fire a Lambda function for INSERT only. The Lambda fucntion reads the stream evant and submits a state machine workflow. The state machine invokes a processing lambada to sends the message to a SNS Topic. If the send is successful, it updates the status of the item as Sucecssful, else Failure. Also, a CloudWatch alarm is used to track the SNS send status. If it fails the alarm  status goes in "In Alarm" state. Once the service comes back to Ok state, the step fucntion again starts sening the message successfully.

An EventBridge schedule is configured to trigger a retry lambda which will use a Global Secondary Index to query the DynamoBD table for the failed messages and tries to resend the same to the SNS Topic again.

![Project Disa - Design Diagram](https://subhamay-projects-repository-us-east-1.s3.amazonaws.com/0066-disa/disa-architecture-diagram.png)

![Project Disa - Services Used](https://subhamay-projects-repository-us-east-1.s3.amazonaws.com/0066-disa/disa-services-used.png)

## Getting Started

### Dependencies

* Create a Customer Managed KMS Key in the region where you want to create the stack..
* Modify the KMS Key Policy to let the IAM user encrypt / decrypt using any resource using the created KMS Key.

### Installing

* Clone the repository.
* Create a S3 bucket and make it public.
* Create the folders - 0066-disa/cft/nested-stacks/, 0066-disa/cft/state-machine/, 0066-disa/code/python
* Upload the following YAML templates to 0066-disa/cft/nested-stacks/
    * cw-custom-metric-alarm-stack.yaml	
    * dynamodb-stack.yaml
    * iam-role-stack.yaml
    * lambda-function-stack.yaml
    * sns-stack.yaml
* Upload the following YAML templates to  0066-disa/cft/
    * disa-root-stack.yaml
* Zip and Upload the follwing Python files to 0066-disa/code/python/
    * disa_init_process.zip 
    * disa_process.zip
    * disa_retry.zip
* Upload the Step fucntion ASL to 0066-disa/cft/state-machine/
    * state-machine.json
* Create the entire using by using the root stack template disa-root-stack.yaml passing the necessary parameters.

### Executing program

* Create an item in the DynamoDB table with attribute as "message" (note the case, keep the attribute exactly as mentioned.) an email is sent to subscriber to the SNS Topic and the DynamoDB item status will get updated to Successful.
* For negative use case , update the Lambda environment variable SNS_TOPIC_ARN to any non-existent SNS Topic Arn and see the DynamoDB item status getting updated to Failure.
* The EventBridge scheduler will run a retry lambda to retry sending the failed messages by querying the DynamoDB table using a Global Secondary Index.

## Help

Post message in my blog (https://blog.subhamay.com)


## Authors

Contributors names and contact info

Subhamay Bhattacharyya  - [subhamay.aws@gmail.com]

## Version History


* 0.1
    * Initial Release

## License

This project is licensed under Subhamay Bhattacharyya. All Rights Reserved.



