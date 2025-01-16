import json
import os
import argparse
import requests
from utils.manageQueue import SqsConsumer
from utils.manageQueue import SqsProcucer


DLP_POLICY = json.load(open("pollicy.json","r"))
blacklist_sender, blacklist_receiver = DLP_POLICY['user']['blackList'].get('senderList', []), DLP_POLICY['user']['blackList'].get('receiverList', [])
whitelist_sender, whitelist_receiver = DLP_POLICY['user']['whiteList'].get('senderList', []), DLP_POLICY['user']['whiteList'].get('receiverList', [])
pii_not_present_default = DLP_POLICY['message']['messageType']['piiNotPresent'].get('default')
user_is_registered_default = DLP_POLICY['message']['userType']['userIsRegistered'].get('default')
user_not_registered_default = DLP_POLICY['message']['userType']['userNotRegistered'].get('default')
pii_list = DLP_POLICY.get('pii', [])

def mask_text(text):
    if not text:
        return ''
    length = len(text)
    if length <= 2:  # If text is too short, return it as is
        return text

    visible_length = max(1, length // 10)  # At least 1 character visible at the start and end
    if length <= 2 * visible_length:  # If the text is too short for effective masking
        return text

    start_visible = text[:visible_length]
    end_visible = text[-visible_length:]
    masked_part = '*' * (length - 2 * visible_length)
    return start_visible + masked_part + end_visible

def process_dictionary(input_dict):
    result = {
        'message': '',
        'pii': list(set(input_dict.values()))  # Extract unique values
    }
    combined_keys = ''
    for key, value in input_dict.items():
        combined_keys+=f" {value}: {mask_text(key)},"
    result['message']=combined_keys
    return result

def getUser(piiInformation, endpoint):
    endpoint = endpoint
    user = requests.post(url=endpoint, json=piiInformation)
    userJson = json.loads(user.content)
    return userJson.get('user',"Null")
def sendMessage(messageId, s3Key, timeStamp,sqs):
    procucer = SqsProcucer(url)
    procucer.send_message(json.dumps({"messageId":str(uuid.uuid4()),"s3Key":objKey, "time":str(time.time)}))
    print("created")

def main():
    parser = argparse.ArgumentParser(description="worker handels the task of processing the information from the queue and associate a user to it")
    parser.add_argument("--identity_endpoint", required=True) 
    args = parser.parse_args()
    piiQueue = os.getenv("OWNERIDENTY","https://sqs.us-east-2.amazonaws.com/767397688321/OwnerIdentification.fifo")
    pendinfApproval = os.getenv("APPROVALSQSURL","https://sqs.us-east-2.amazonaws.com/767397688321/approval_list.fifo")
    sendSqs = os.getenv("SENDSQSURL","")

    consumer = SqsConsumer(piiQueue)

    @consumer.process
    def handel_event(message):
        try:
            messaageID = message["messageId"]
            s3Key = message["s3Key"]
            piiFound = json.loads(message["pii"])
            timeStamp = message["timeStamp"]
            endUsers = json.loads(message["endUsers"])
            user = getUser(piiFound, args.identity_endpoint)
            print(user)
            print("-----------------")
            if user.get("email") == "null" and user_not_registered_default == "approve":
                sendMessage(messaageID, s3Key, timeStamp, sendSqs)
            producer = SqsProcucer(pendinfApproval)
            res = producer.send_message(json.dumps({"messageId":messaageID, "s3Key": s3Key, "endUser":json.dumps(endUsers), "pii":process_dictionary(piiFound),"user":user, "timeStamp":timeStamp}))
        except Exception as e:
            print(e)


    consumer.consume_messages()


if __name__=="__main__":
    main()
