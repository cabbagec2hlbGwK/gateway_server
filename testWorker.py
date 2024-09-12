from utils.manageQueue import SqsConsumer
import os

def main():
    url = os.getenv("APPROVALSQSURL","")

    consumer = SqsConsumer(url)

    @consumer.process
    def handel_event(message):
        try:
            print(f"{type(message)}, {message}")
        except Exception as e:
            print(e)


    consumer.consume_messages()

