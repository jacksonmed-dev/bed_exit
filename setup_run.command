#!/usr/bin/env bash

while getopts a: flag
do
    case "${flag}" in
        a) streamarn=${OPTARG};;
    esac
done

s3Bucket="${s3bucketname:=poa-deployments}"

source ./venv/bin/activate

pip3 install -r requirements.txt

python3 ./test_write.py \
  -r us-west-2 \
  -sa $streamarn \
  -sn sensor-data-stream-staging \
  -m false
