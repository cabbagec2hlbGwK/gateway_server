import boto3 
import os
import json 
import time
from utils.manageQueue import SqsProcucer
from utils.manageDatabase import DcDatabase

WAIT_INTERVAL = 1


def get_secret(secret_name):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager'
    )
    
    try:
        print("trying value")
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        print("ther was a error :"+ str(e))

    secret = get_secret_value_response['SecretString']
    print("the is "+ str(secret_name))
    return secret


def getUpdate(dbConnector, producer):
    data = dbConnector.getApprovedMessage()
    for value in data:
        messageId = value[0]
        timeStamp = value[1]
        objKey = value[2]
        try:
            producer.send_message(json.dumps({"messageId":messageId,"s3Key":objKey, "time":str(timeStamp)}))
            dbConnector.tagMessageSent(messageId)
            print("created")
            print(value)
        except Exception as e:
            print(e)




def main():
    url = os.getenv("SENDSQSURL","")
    pro = SqsProcucer(url)
    secretName = os.getenv("secret_name")
    rdsEndpoint = os.getenv("rds_endpoint")
    tableN = os.getenv("tableName")
    databaseName = os.getenv("DATABASENAME")
    rdsSec = json.loads(get_secret(secretName))
    db = DcDatabase(secret=rdsSec, endpoint=rdsEndpoint, dbName=databaseName,firebaseConnector=None, dbTableName=tableN)
    while True:
        time.sleep(2)
        getUpdate(db, pro)
        db.connection.commit()
    


if __name__=="__main__":
    main()
