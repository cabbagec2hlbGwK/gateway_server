#THIS CLASS IS TO MANAGE ALL THE ENCRYPTION AND DECRIPTION AND HANDELING THE S3 
#SO WE CAN ABSTRACT THE LAYER

import boto3
import pickle
import io
import os
import logging
import hashlib
import base64
from cryptography.fernet import Fernet

log = logging.getLogger("manageS3_task")

class S3Manage:
    def __init__(self,key, bucketName) -> None:
        self.key = base64.b64encode(key).decode("ascii")
        print(type(self.key))
        self.cipher = Fernet(self.key)
        self.s3Client = boto3.client("s3")
        self.bucketName = bucketName

    def encryptData(self, data):
        #this fuction will handel encoding the data and enc
        try:
            pickledData = pickle.dumps(data)
            return self.cipher.encrypt(pickledData)
        except Exception as e:
            log.error(e)

    def decriptData(self, data):
        try:
            decData = self.cipher.decrypt(data)
            formatedData = pickle.loads(decData)
            return formatedData
        except Exception as e:
            log.error(e)

    def s3Get(self, key):
        buffer = io.BytesIO()
        self.s3Client.download_fileobj(self.bucketName, key, buffer)
        buffer.seek(0)
        encrypted_data = buffer.read()
        return self.decriptData(encrypted_data)


    def s3Put(self, data):
        encData = self.encryptData(data)
        buffer = io.BytesIO(encData)
        key = str(hashlib.sha256(encData).hexdigest())
        self.s3Client.upload_fileobj(buffer, self.bucketName,key)
        return key


def main():
    data = {"test":"values","test2":"values"}
    key = os.getenv("ENCKEY", "t"*32).encode('utf-8')
    bucketName = os.getenv("S3BUCKET","testbbuckker12")
    s3Manager = S3Manage(key, bucketName)
    key = s3Manager.s3Put(data)
    val = s3Manager.s3Get(key)
    print(val.get("test"))




if __name__=="__main__":
    main()
