import json
import boto3
import requests
import os
import pymysql  
import time
import firebase_admin
from firebase_admin import credentials, auth
from pymysql.err import OperationalError, ProgrammingError

class FirebaseConnector:
    def close(self):
        pass
    def __init__(self, firebaseConfig):
        try:
            self.firebaseConnection = firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(json.loads(firebaseConfig))
            self.firebaseConnection = firebase_admin.initialize_app(cred)
        
        
    def getUserUid(self, userInformation):
        email = userInformation.get("email","Null")
        phone = userInformation.get("phone","Null")
        if email != "Null":
            userUid = self.getUserByEmail(email)
            if userUid:
                return userUid.uid
        if phone != "Null":
            userUid = self.getUserByPhone(phone)
            if userUid:
                return userUid.uid
        else:
            return None
        
        
    def getUserByEmail(self,email):
        try:
            user = auth.get_user_by_email(email)
            return user
        except firebase_admin.auth.UserNotFoundError:
            print(f"User with email {email} not found.")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    def getUserByPhone(self, userInformation):
        try:
            user = auth.get_user_by_phone_number(userInformation)
            return user
        except firebase_admin.auth.UserNotFoundError:
            print(f"User with phone number {phone_number} not found.")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    

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
        
    def getEmailApprovals(self):
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM {self.tableName}")
        rows = cursor.fetchall()
        print(f"The lenth of the table is {len(rows)}")
        for row in rows:
            print(row)
        cursor.close()
                
            
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
        
    def tableIfExist(self, table_name):
        try:
            cursor = self.connection.cursor()
            print(f"Table {table_name} does not exist. Creating table.")
            create_table_query = f"""
            CREATE TABLE {table_name} (
                messageId VARCHAR(255) PRIMARY KEY, 
                pii JSON,
                user VARCHAR(255),
                s3Key VARCHAR(255),
                userUid VARCHAR(255),
                approvalState ENUM('approved', 'expired', 'active', 'denied') NOT NULL,
                timeStamp TIMESTAMP
            );
            """
            cursor.execute(create_table_query)
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(f"Table creation ran into some trouble ---------------: {str(e)}")
            
    def insertData(self, rawData):
        res = False
        #approvalState ENUM('approved', 'expired', 'active', 'denied')
        query = f"""
            INSERT INTO {self.tableName} (messageId, pii, s3Key, timeStamp, approvalState, user,userUid)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        messageId = rawData.get("messageId","None"  )
        pii = json.dumps(rawData.get("pii","None"))
        s3Key = rawData.get("s3Key")
        timeStamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(rawData.get("timeStamp")))
        user = json.dumps(rawData.get("user","{}"))
        userUid = self.firebaseConnector.getUserUid(json.loads(user))
        
        data= (messageId, pii, s3Key, timeStamp, "active", user, userUid)
        print(data)
        
        try:
            with self.connection.cursor() as cursor:
                res = cursor.execute(query, data)
                self.connection.commit()
                print("Data inserted successfully"+str(res))
                res = True
        except pymysql.MySQLError as e:
            error_code = e.args[0]
            error_message = e.args[1]
            if error_code == 1146:
                print(f"Table does not exist: {error_message}")
                self.tableIfExist(self.tableName)
                print(f"sucessfully created the table {self.tableName}")
                self.insertData(rawData)
                res = True
            elif error_code == 1062:
                print("the value alredy exist")
                res = true
            else:
                print(f"Failed to insert data: {e}")
                self.connection.rollback()
                res = False
            
        return res
        
        
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
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
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
    print(event)
    
    try:
        for record in event['Records']:
            print(record)
            message_id = record['messageId']
            body = json.loads(record['body'])  
    
            print(f"Body: {body}")
            res = db.insertData(body)
            print(res)
        fb.close()
        return {
            'statusCode': 200,
            'body': json.dumps("it is working")
        }
       
    except Exception as e:
        db.close()
        fb.close()
        print(e)
        

