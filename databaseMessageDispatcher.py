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


def getUpdate(dbConnector):
    data = dbConnector.getApprovedMessage()
    for value in data:
        print(value)




def main():
    secretName = os.getenv("secret_name")
    rdsEndpoint = os.getenv("rds_endpoint")
    tableN = os.getenv("tableName")
    rdsSec = json.loads(get_secret(secretName))
    db = DcDatabase(secret=rdsSec, endpoint=rdsEndpoint, dbName="test1",firebaseConnector=None, dbTableName=tableN)
    


if __name__=="__main__":
    main()
