from flask import Flask, render_template, jsonify, request
import boto3
import json

app = Flask(__name__)

# Configure AWS SQS
sqs = boto3.client('sqs', region_name='us-east-1')  # Update 'your-region'
queue_url = 'https://sqs.us-east-1.amazonaws.com/536380612665/scaned.fifo'  # Update with your SQS Queue URL

def get_message():
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )
    messages = response.get('Messages', [])
    if messages:
        return messages[0]
    return None

def format_pii(pii):
    pii_fields = pii.split()
    return "\n".join(f"- {field}" for field in pii_fields)

@app.route('/')
def index():
    message = get_message()
    if message:
        body = json.loads(message['Body'])
        pii_message = format_pii(body.get('pii', ''))
        return render_template('index.html', message_body=pii_message, receipt_handle=message['ReceiptHandle'])
    else:
        return "No messages in queue."

@app.route('/process', methods=['POST'])
def process():
    action = request.json['action']
    receipt_handle = request.json['receipt_handle']

    if action == 'approve':
        # Handle approval logic here
        pass
    elif action == 'deny':
        # Handle denial logic here
        pass

    # Delete the message from the queue
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)

