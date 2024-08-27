import json
import random
import string
from datetime import datetime, timedelta

def generate_random_values(user_name):
    # Generate random values
    pii_types = random.sample(['SSN', 'Credit Card', 'Passport', 'Phone Number', 'Email', 'Address'], 3)
    message = f"Data processed successfully for user: {user_name}"
    expiry_time = (datetime.utcnow() + timedelta(minutes=random.randint(30, 120))).isoformat()
    pii_sender = ''.join(random.choices(string.ascii_lowercase, k=5)) + "@example.com"
    pii_receiver = [f"{random.choice(['john', 'jane', 'doe', 'alice'])}@example.com" for _ in range(random.randint(1, 3))]
    timestamp = datetime.utcnow().isoformat()
    
    return {
        'piiType': pii_types,
        'message': message,
        'expiryTime': expiry_time,
        'piiSender': pii_sender,
        'piiReciver': pii_receiver,
        'timeStamp': timestamp
    }
print(generate_random_values("testtttt"))
