from hashlib import sha256
import logging
import boto3
from botocore.exceptions import ClientError
import time

def hashCompute(block, num) :
    m1 = sha256()
    m2 = sha256()
    m1.update(block)
    m1.update(bytes(num))
    m2.update(bytes(m1.hexdigest()))
    return int(m2.hexdigest(), 16)

def goldenNonce(start, end, block_bytes, dif) :
    i = start
    while(i <= end) :
        if(hashCompute(block_bytes, i) >> (256 - dif) == 0) :
            return i
        i += 1
    return -1

def get_queue(queue_name) :
    try :
        queue = sqs.get_queue_url(QueueName = queue_name)
    except ClientError as e :
        logging.error(e)
        return None
    return queue['QueueUrl']

def receive_message(queue_url) :
    try :
        message = sqs.receive_message(QueueUrl = queue_url, MessageAttributeNames = ['min', 'max', 'dif'], MaxNumberOfMessages = 1)
    except ClientError as e :
        logging.error(e)
        return None
    return message['Messages']

def send_message(queue_url, goldenNonce) :
    try :
        sqs.send_message(QueueUrl = queue_url, MessageAttributes = {'goldenNonce' : {'DataType' : 'Number', 'StringValue' : str(goldenNonce)}})
    except ClientError as e :
        logging.error(e)
        return 0
    return 1    

s = boto3.Session(aws_access_key_id='ASIAQCOJS3VZ5MGUPRW6', aws_secret_access_key='zHvIY7WctUZUqkM9Kt0UAGzmJYqxpWzLRC9yAhhN',
aws_session_token='FwoGZXIvYXdzEMr//////////wEaDG4Q3QxKSdFb6NM+tiLEAZgreLN9jL4VhhVFt1XCc12nyVBEeSo3pDyrYUwhsMeRd7jlRfRRGaXGOLivAyw5t1wmOWprXLB3j5bn47BP6Zc2IsbnN+boZnBiv2ntD9JFC5gZUv5heJtdILC6nAoiYDbzUztSWzmEUqA8HulYfkvlNyMccbuwQ2sNKMW+P+xApFV62/SF/AkuuaNJN9x0C3NkBBSMSSPdHQmCUncfs7lXj0MBDORMw7ZLQV3o3zTESZWFfap+++K/v3wThG8/NCufi/Mond6P7wUyLaXnCZOHsAel30u22duhY+tOGkZUH3SaLqLJbhOxPSOIkekx2cutsCREoC42nA==')
sqs = s.client('sqs')
block = "COMSM0010cloud"
block_bytes = bytes(block)

queue_url = None
while(queue_url == None) :
    queue_url = get_queue('CloudComputing')

message_received = []
while(len(message_received) == 0) :
    time.sleep(5)
    message_received = receive_message(queue_url)
message_attributes = message_received[0]['MessageAttributes']
minNum = int(message_attributes['min']['StringValue'])
maxNum = int(message_attributes['max']['StringValue'])
dif = int(message_attributes['dif']['StringValue'])

goldenNonce = goldenNonce(minNum, maxNum, block_bytes, dif)
if(goldenNonce != -1) :
    message_sent = 0
    while(message_sent == 0) :
        message_sent = send_message(queue_url, goldenNonce)
