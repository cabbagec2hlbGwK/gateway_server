import json
import os
import argparse
import requests
from utils.manageQueue import SqsConsumer
from utils.manageQueue import SqsProcucer

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

        #producer.send_message(json.dumps({"messageId":str(uuid.uuid4()),"pii":json.dumps(jres), "s3Key":objKey,"timeStamp":time.time()}))
    @consumer.process
    def handel_event(message):
        try:
            messaageID = message["messageId"]
            s3Key = message["s3Key"]
            piiFound = json.loads(message["pii"])
            timeStamp = message["timeStamp"]
            endUsers = json.loads(message["endUser"])
            user = getUser(piiFound, args.identity_endpoint)
            if not user:
                sendMessage(messaageID, s3Key, timeStamp, sendSqs)
            producer = SqsProcucer(pendinfApproval)
            res = producer.send_message(json.dumps({"messageId":messaageID, "s3Key": s3Key, "endUser":json.dumps(endUsers), "pii":piiFound,"user":user, "timeStamp":timeStamp}))
            print(pendinfApproval)
        except Exception as e:
            print(e)


    consumer.consume_messages()


if __name__=="__main__":
    main()
