import random
import string
import requests
from datetime import datetime, timedelta
import json
import boto3
import requests
import base64
import os
import pymysql  
import time
import firebase_admin
from botocore.exceptions import ClientError 
from firebase_admin import credentials, auth
from pymysql.err import OperationalError, ProgrammingError

def add_30_minutes_to_unix():
    current_timestamp = time.time()
    new_timestamp = current_timestamp + (30 * 60)
    return str(new_timestamp)

class FirebaseConnector:
    def close(self):
        pass
    def __init__(self, firebaseConfig):
        try:
            self.firebaseConnection = firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(json.loads(firebaseConfig))
            self.firebaseConnection = firebase_admin.initialize_app(cred)
    
    def userVerification(self, id_token):
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
            user = auth.get_user(user_id)
            if user_id == 'expected_user_id':
                print("User is the correct user.")
            else:
                pass
            return user
        except Exception as e:
            print(f"Error verifying user: {e}")
            return False
        
        
    
    

class DcDatabase:
    def __init__(self, secret, endpoint, dbName,firebaseConnector, port=3306, timeout=5, dbTableName = "approval_state_dev"):
        self.endpoint = endpoint
        self.secret = secret
        self.dbName = dbName 
        self.port = port
        self.timeout = timeout
        self.tableName = dbTableName
        self.firebaseConnector = firebaseConnector
        try:
            self.connection = self.DbConnect()
        except OperationalError as e:
            error_code = e.args[0]
            if error_code == 1049:
                print("the database was not found creating it and trying again")
                if self.CreateDB(self.dbName):
                    self.connection = self.DbConnect()
            print(e)
                
       
       
    def DbConnect(self):
        connection = pymysql.connect(
            host=self.endpoint,
            user=self.secret["username"],
            password=self.secret["password"], 
            db=self.dbName,  
            port=self.port,
            connect_timeout=self.timeout
            )
        print("Connection successful")
        return connection
        
    def CreateDB(self, dbName):
        connection = pymysql.connect(
            host=self.endpoint,
            user=self.secret["username"],
            password=self.secret["password"], 
            port=self.port,
            connect_timeout=self.timeout
        )
        print("Connection successful")
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE {dbName}")
                print(f"Database {dbName} created successfully.")
                connection.commit()
        except pymysql.MySQLError as e:
            print(f"Failed to create database: {str(e)}")
            connection.close()
            return False
        connection.close()
        return True
    def close(self):
        self.connection.close()
        
    def getActiveEmailApprovals(self,uid):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT pii, messageId, sender, reciver, timeStamp FROM {self.tableName} WHERE approvalState = 'active' AND hasMessageBeenSent = false AND userUid = '{uid}';")
        rows = cursor.fetchall()
        print(f"The lenth of the table is {len(rows)}")
        records = []
        for row in rows:
            pii = json.loads(row[0])
            data = {
                'piiType': pii.get("piiTypes","null"),
                'messageId':row[1],
                'message': pii.get("message","null"),
                'expiryTime': add_30_minutes_to_unix(),
                'piiSender': row[2],
                'piiReciver': row[3],
                'timeStamp': str(row[4])
            }
            print(data)
            records.append(data)
        cursor.close()
        return {"notifications":records}
                
            
    def dbIfExist(self):
        cursor = self.connection.cursor()
        cursor.execute(f"SHOW DATABASES LIKE '{self.dbName}'")
        
        result = cursor.fetchone()
        if not result:
            print(f"Database {self.dbName} does not exist. Creating database.")
            cursor.execute(f"CREATE DATABASE {self.dbName}")
            self.connection.commit()
        else:
            print(f"Database {self.dbName} already exists.")
        
        cursor.close()
        
            
        
#essage(json.dumps({"messageId":str(uuid.uuid4()),"pii":json.dumps(jres), "s3Key":objKey,"timeStamp":time.time()}))

    
def get_secret(secret_name):
    region_name = os.getenv("region")
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
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


def lambda_handler(event, context):
    secretName = os.getenv("secret_name")
    rdsEndpoint = os.getenv("rds_endpoint")
    configName = os.getenv("firebase_config")
    tableN = os.getenv("tableName")
    rdsSec = json.loads(get_secret(secretName))
    firebaseConfig = get_secret(configName)
    firebaseCred = json.loads(firebaseConfig)
    fb = FirebaseConnector(firebaseCred.get("config"))
    db = DcDatabase(secret=rdsSec, endpoint=rdsEndpoint, dbName="test1",firebaseConnector=fb, dbTableName=tableN)
    
    required_headers = ['userName', 'ID_TOKEN', 'device_time']
    headers = event.get('headers', {})
    print(f"{json.dumps(event)} {context}")
    missing_headers = [header for header in required_headers if header not in headers]
    if missing_headers:
        response = {
            'message': f"Missing required headers: {', '.join(missing_headers)}"
        }
        return {
            'statusCode': 400,
            'body': json.dumps(response),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    
    # If all headers are present, proceed with processing
    user_name = headers.get('userName')
    id_token = base64.b64decode(headers.get('ID_TOKEN').strip())
    device_time = headers.get('device_time')
    user = fb.userVerification(id_token)
    if user == False:
        print("this user is not verifies")
        response = {
            'message': "The token is not valid"
        }
        return {
            'statusCode': 401,
            'body': json.dumps(response),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    else:
        print("the user is "+ str(user.uid))
        notifications = db.getActiveEmailApprovals(user.uid)
        return {
            'statusCode': 200,
            'body':json.dumps({'notifications':notifications}),
            'headers': {
            'Content-Type': 'application/json'
            }
        }
        
        
    

