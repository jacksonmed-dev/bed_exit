import os
import boto3
import json

import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dotenv import load_dotenv

load_dotenv()


class KinesisClient:

    def __init__(self):
        self.session = boto3.Session(
            aws_access_key_id=os.environ["ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["ACCESS_KEY_SECRET"],
        )
        self.kinesis_client = self.get_auth_client("kinesis")

    def signed_request_v2(self, endpoint, dataObj):
        sigv4 = SigV4Auth(self.session.get_credentials(), "execute-api", "us-west-2")
        data = json.dumps(dataObj)
        headers = {"Content-Type": "application/x-amz-json-1.1"}
        request = AWSRequest(
            method="POST",
            url=endpoint,
            data=data,
            headers=headers,
        )
        # request.context["payload_signing_enabled"] = False
        sigv4.add_auth(request)

        prepped = request.prepare()

        response = requests.post(
            prepped.url,
            headers=prepped.headers,
            data=data,
        )
        print(response.text)

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
        print(f"Wrote record successfully")

    def put_records(self, records):
        print("############# KINESIS #############")
        print("sending records to kinesis")
        records_result = self.kinesis_client.put_records(
            Records=records,
            StreamName=os.environ["STREAM_NAME"],
            # StreamARN=os.environ["STREAM_ARN"]
        )

        print(f"Wrote all records successfully")
        print("############ END KINESIS ###########")

