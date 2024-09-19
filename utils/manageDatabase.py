from datetime import datetime, timedelta
import pymysql  
from botocore.exceptions import ClientError 
from pymysql.err import OperationalError, ProgrammingError


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
        
    def tagMessageSent(self, messageId):
        with self.connection.cursor() as cursor:
            query = f"UPDATE {self.tableName} SET hasMessageBeenSent = 1 WHERE messageId = %s"
            cursor.execute(query,(messageId, ))

    def getApprovedMessage(self):
        rows = []
        try:
            with self.connection.cursor() as cursor:
                query = f"SELECT messageId, timeStamp, s3Key FROM {self.tableName} WHERE approvalState = approved AND hasMessageBeenSent = 0"
                cursor.execute(query)
                rows = cursor.fetchall()
        except Exception as e:
            print(e)
        return rows

    def apply(self,user, state, messageId):
        cursor = self.connection.cursor()
        query = f"SELECT userUid FROM {self.tableName} WHERE messageId = %s;"
        cursor.execute(query,(messageId,))
        rows = cursor.fetchall()
        for row in rows:
            if str(user.uid).strip() == str(row[0]).strip():
                print("user is authenticatrd")
                cursor.execute(f"UPDATE {self.tableName} SET approvalState = %s WHERE messageId = %s ;",(state, messageId,))
                self.connection.commit()
                print("the message is a")
                cursor.close()
                return True
            else:
                print("Verification failed: Wrong user")
                cursor.close()
                return False
                
            
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
        
           
