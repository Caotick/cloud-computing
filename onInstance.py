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
        if(message.get('Messages') == None) :
            return [{}]
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

s = boto3.Session(aws_access_key_id='ASIAQCOJS3VZX76PZQUC', aws_secret_access_key='X5kHjUnchausHXqXi1I1xGaOHJTTU9xuAfZfBlFZ',
aws_session_token='FwoGZXIvYXdzENz//////////wEaDPoeEjeicA+J5ms/OCLEAaQ99jYjzSsmhV6L1CQc2m3aFO35DD/6OqRCffnSinXqahqAJYHXRLdFsuldE4Ecy1yu5E7k81qMKhx0DHEfMeZpImUMnUCZewQ0S1nFySC1tq2l5JYZaitJoFZaV51P13zFQZKh3fzwNVWBtgvVrAIldWpve+8FOrqfZcE4W0yrvveSTGt2QFe7U4uzxo0ofCHbZMgGdX25k2lYF3LApPCHOXUS8VZXANW8wCWxzo3fh8HoO5kHPuJ/6utIUPBMVRdWzB4o8cqT7wUyLcEHEcdwoVX32mOCfFaFprBfu910yZzbcnKB8tsMmaj0zUVjkp4Wg7jnGHzwIw==',
region_name='us-east-1')
sqs = s.client('sqs')
block = "COMSM0010cloud"
block_bytes = bytes(block, 'utf-8')

queue_url = None
while(queue_url == None) :
    queue_url = get_queue('CloudComputing')

message_received = []
while(len(message_received) == 0) :
    message_received = receive_message(queue_url)
    if(message_received[0].get('MessageAttributes') == None) :
        message_received = []
        time.sleep(30)
    else :
        try :
            sqs.delete_message(QueueUrl = queue_url, ReceiptHandle = message_received[0]['ReceiptHandle'])
        except ClientError as e :
            logging.error(e)
            message_received = []
    time.sleep(5)
message_attributes = message_received[0]['MessageAttributes']
minNum = int(message_attributes['min']['StringValue'])
maxNum = int(message_attributes['max']['StringValue'])
dif = int(message_attributes['dif']['StringValue'])

goldenNonce = goldenNonce(minNum, maxNum, block_bytes, dif)
if(goldenNonce != -1) :
    message_sent = 0
    while(message_sent == 0) :
        message_sent = send_message(queue_url, goldenNonce)
