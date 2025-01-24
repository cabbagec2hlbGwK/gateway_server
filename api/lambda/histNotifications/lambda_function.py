import json
import random
import string
from datetime import datetime, timedelta

def generate_random_values(user_name):
    # Generate random values
    pii_types = random.sample(['SSN', 'Credit Card', 'Passport', 'Phone Number', 'Email', 'Address'], 3)
    message = f"Data processed successfully for user: {user_name}"
    pii_sender = ''.join(random.choices(string.ascii_lowercase, k=5)) + "@example.com"
    pii_receiver = [f"{random.choice(['john', 'jane', 'doe', 'alice'])}@example.com" for _ in range(random.randint(1, 3))]
    timestamp = datetime.utcnow().isoformat()
    state = f"{random.choice(['0','1'])}"
    
    return {
        'piiType': pii_types,
        'message': message,
        'piiSender': pii_sender,
        'piiReciver': pii_receiver,
        'acknowledgeTimeStamp': timestamp,
        'state':state
    }

def lambda_handler(event, context):
    # Required headers
    required_headers = ['userName', 'ID_TOKEN', 'device_time']
    
    # Extracting headers
    headers = event.get('headers', {})
    print(f"{json.dumps(event)} {context}")
    
    # Check for missing headers
    missing_headers = [header for header in required_headers if header not in headers]
    
    if missing_headers:
        # Respond with a message indicating missing headers
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
    id_token = headers.get('ID_TOKEN')
    device_time = headers.get('device_time')
    
    # Generate the random values
    data = []
    for a in range(10):
        data.append(generate_random_values(user_name))
    response_data = {'notifications':data}
    
    return {
        'statusCode': 200,
        'body': json.dumps(response_data),
        'headers': {
            'Content-Type': 'application/json'
        }
    }

