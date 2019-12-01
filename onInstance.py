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
        sqs.send_message(QueueUrl = queue_url, MessageBody = 'Send goldenNonce',
                         MessageAttributes = {'goldenNonce' : {'DataType' : 'Number', 'StringValue' : str(goldenNonce)}})
    except ClientError as e :
        logging.error(e)
        return 0
    return 1    

s = boto3.Session(aws_access_key_id='ASIAQCOJS3VZ3QWX6WPN', aws_secret_access_key='cCIfdEl1SUaKUgMYmuZxek0HlgMpBGAzYFXGVNGW',
aws_session_token='FwoGZXIvYXdzEM3//////////wEaDKEPDP1JRwSej0abTiLEATOa1k0w9VwfitA2dOB2xd/jw6iVR8q1388V17Od0+QnR8qIMg3/qyPsSa2HwJHMn2dhl1Y9+SbkSe/Rj3nz7928JWd+n4omK9H1i+flpzeFoQykBWEZknkKifAYVFigBqrkyfAKK6Fq4TG1wkoQ3dGEJaSoR/zQhowYU7tpbXLH4F1xn6rtBnhFV1df87RcQgjk6gwN3PJfztvMMlXf42Hb4AI7WYPD5AafaerQ2Tc0b3TQk1KRiUBAERihIDMLYe1hH44o4biQ7wUyLQoVDcE/y0gM6HmubpPsOi6b8sKr+5LBZ5loQ7pl/4iqeMqeX6j+WyngHdyJGg==')
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
