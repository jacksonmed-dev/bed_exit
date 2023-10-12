from logger import logger
import os
import time
import boto3
import json
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dotenv import load_dotenv

load_dotenv()
class AwsClient:
    def __init__(self):
        self.session = boto3.Session(
            aws_access_key_id=os.environ["ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["ACCESS_KEY_SECRET"],
        )
        self.kinesis_client = self.get_auth_client("aws_client")
        self.cloudwatchlogs_client = self.get_auth_client("logs")

    def signed_request_v2(self, endpoint, dataObj, method='POST'):
        sigv4 = SigV4Auth(self.session.get_credentials(), "execute-api", "us-west-2")
        data = json.dumps(dataObj)
        headers = {"Content-Type": "application/x-amz-json-1.1", "x-api-key": os.environ["API_KEY"]}
        request = AWSRequest(
            method=method,
            url=endpoint,
            data=data,
            headers=headers,
        )
        # request.context["payload_signing_enabled"] = False
        sigv4.add_auth(request)

        prepped = request.prepare()

        if method == 'POST':
            response = requests.post(
                prepped.url,
                headers=prepped.headers,
                data=data,
            )
            logger.info(response.text)
        if method == 'PATCH':
            response = requests.patch(
                prepped.url,
                headers=prepped.headers,
                data=data,
            )
            logger.info(f"AWS backend call response: {response.text}")

    # See options for authenticating here: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html#credentials
    def get_auth_client(self, service_name):
        return self.session.client(
            service_name,
            region_name=os.environ["AWS_REGION"],
        )

    def record_data_bytes(self, counter):
        data = {
            "id": counter,
            "name": f"Record # {counter}",
            "test": "test value"
        }
        return json.dumps(data).encode("utf-8")

    def generate_record(self, counter, sequence_ordering=None):
        record = {
            "Data": self.record_data_bytes(counter),
            "PartitionKey": "Beta",
        }

        if sequence_ordering is not None:
            record["SequenceNumberForOrdering"] = sequence_ordering

        return record

    def put_record(self, record):
        record_result = self.kinesis_client.put_record(
            StreamName=os.environ["STREAM_NAME"],
            Data=record,
            PartitionKey=os.environ["PARTITION_KEY"],
            # SequenceNumberForOrdering=record.get(
            #     "SequenceNumberForOrdering",
            #      None,
            # ),
            # StreamARN=os.environ["STREAM_ARN"]
        )
        logger.info(f"Wrote record successfully")

    def put_records(self, records):
        logger.info("############# KINESIS #############")
        logger.info("sending records to aws_client")
        records_result = self.kinesis_client.put_records(
            Records=records,
            StreamName=os.environ["STREAM_NAME"],
            # StreamARN=os.environ["STREAM_ARN"]
        )
        self.write_cloudwatch_log(
            f"Sensor {os.environ['SENSOR_SSID']}: Data successfully sent to aws_client")
        logger.info(f"Wrote all records successfully")
        logger.info("############ END KINESIS ###########")

    def write_cloudwatch_log(self, message):
        now_ns = time.time_ns()
        now_ms = int(now_ns / 1000000)

        self.cloudwatchlogs_client.put_log_events(
            logGroupName=os.environ["AWS_LOG_GROUP"],
            logStreamName=os.environ["AWS_LOG_STREAM"],
            logEvents=[
                {
                    "timestamp": now_ms,
                    "message": message,
                },
            ],
        )
