import logging
import boto3
from botocore.exceptions import ClientError
import time

def create_ec2_instances(image_id, instance_type, keypair_name, n_instances, user_data) :
    try:
        response = ec2.run_instances(ImageId = image_id, InstanceType = instance_type,
                                            KeyName = keypair_name, MinCount = 1, MaxCount = n_instances, UserData = user_data)
    except ClientError as e :
        logging.error(e)
        return None
    return response['Instances']

def terminate_ec2_instances(instance_ids) :
    try:
        states = ec2.terminate_instances(InstanceIds = instance_ids)
    except ClientError as e :
        logging.error(e)
        return None
    return states['TerminatingInstances']

def create_queue(queue_name) :    
    try :
        queue = sqs.create_queue(QueueName = queue_name, Attributes = {'MessageRetentionPeriod' : '300'})
    except ClientError as e :
        logging.error(e)
        return None
    return queue['QueueUrl']

def delete_queue(queue_url) :
    try :
        sqs.delete_queue(QueueUrl = queue_url)
    except ClientError as e :
        logging.error(e)
        return 0
    return 1

def send_message(queue_url, body, min, max, dif) :
    try :
        sqs.send_message(QueueUrl = queue_url, MessageBody = body,
        MessageAttributes = {'min' : {'DataType' : 'Number', 'StringValue' : str(min)}, 'max' : {'DataType' : 'Number', 'StringValue' : str(max)}, 'dif' : {'DataType' : 'Number', 'StringValue' : str(dif)}})
    except ClientError as e:
        logging.error(e)
        return 0
    return 1

def receive_message(queue_url) :
    try :
        message = sqs.receive_message(QueueUrl = queue_url, MessageAttributeNames = ['goldenNonce'])
        if (message.get('Messages') == None) :
            return [{}]
    except ClientError as e :
        logging.error(e)
        return None
    return message['Messages']

n_instances = 0
while (n_instances <= 0 or n_instances > 15) :
    n_instances = input("How many instances do you want to run ?")
dif = 0
while dif <= 0 :
    dif = input("What is the difficulty-level ?")
aws_public = raw_input("Enter your aws access key id : ")
aws_private = raw_input("Enter your aws secret access key : ")

minNum = 0
maxNum = 2**32 - 1
step = maxNum // n_instances

ec2 = boto3.client('ec2')
sqs = boto3.client('sqs')
key = ec2.describe_key_pairs()['KeyPairs'][0]

user_data = """#!/bin/bash
cd /home/ec2-user/venv
source /home/ec2-user/venv/python3/bin/activate
git clone https://github.com/Caotick/cloud-computing.git
cd cloud-computing
echo """ + aws_private + """ | cat > inputfile
echo """ + aws_public + """ | cat - inputfile
aws configure < inputfile
python onInstance.py
"""
print(user_data)

ec2_instances = None
while (ec2_instances == None) :
    ec2_instances = create_ec2_instances('ami-0bdf86140e03cdfbc', 't2.micro', key['KeyName'], n_instances, user_data)

instances_id = []
for instance in ec2_instances :
    instances_id.append(instance['InstanceId'])

queue_url = None
while (queue_url == None) :
    queue_url = create_queue('CloudComputing')

for i in range(n_instances - 1) :
    message_sent = 0
    while(message_sent == 0) :
        message_sent = send_message(queue_url, str(i + 1), step * i, step * (i + 1) - 1, dif)
message_sent = 0
while(message_sent == 0) :
    message_sent = send_message(queue_url, str(n_instances), step * (n_instances - 1), maxNum, dif)

time.sleep(60)

message_received = []
goldenNonce = 0
n_fail = 0
while(len(message_received) == 0 and n_fail < n_instances) :
    message_received = receive_message(queue_url)
    if (message_received[0].get('MessageAttributes') == None) :
        message_received = []
        time.sleep(10)
    else :
        sqs.delete_message(QueueUrl = queue_url, ReceiptHandle = message_received[0]['ReceiptHandle'])
        goldenNonce = int(message_received[0]['MessageAttributes']['goldenNonce']['StringValue'])
    if(goldenNonce == -1) :
        goldenNonce = 0
        n_fail = n_fail + 1
    time.sleep(5)
if(n_fail == n_instances) :
    print('No golden nonce are available for the difficulty ' + str(dif))
else :
    print('Here is a golden nonce for the difficulty ' + str(dif) + ' : ' + str(goldenNonce))

queue_delete_complete = 0
while(queue_delete_complete == 0) :
    queue_delete_complete = delete_queue(queue_url)

while (len(instances_id) != 0) :
    ec2_instances_terminated = terminate_ec2_instances(instances_id)
    for instance in ec2_instances_terminated :
        instances_id.remove(instance['InstanceId'])
