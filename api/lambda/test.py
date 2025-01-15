import pyrebase
import base64

# Firebase configuration
firebase_config = {
  "apiKey": "AIzaSyDVu8qSt4iNzWi0QOPkLy1F0Dz-7hB376s",
  "authDomain": "digicontrol-emailmonitoring.firebaseapp.com",
  "projectId": "digicontrol-emailmonitoring",
  "storageBucket": "digicontrol-emailmonitoring.firebasestorage.app",
  "messagingSenderId": "772360059568",
  "appId": "1:772360059568:web:80a0352225064adcd75975",
  "measurementId": "G-CKWVRBZR8E",
  "databaseURL":""
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebase_config)

# Authenticate the user and get their token
def generate_user_token(email, password):
    try:
        # Initialize Firebase authentication
        auth = firebase.auth()

        # Sign in the user
        user = auth.sign_in_with_email_and_password(email, password)

        # Get the ID token
        id_token = user['idToken']
        return id_token
    except Exception as e:
        return f"Error: {str(e)}"

# Example usage
if __name__ == "__main__":
    email = "test@user.com"  # Replace with the actual user's email
    password = "test@123"  # Replace with the actual user's password
    
    token = generate_user_token(email, password)
    db64=base64.b64encode(token.encode())
    print(db64)

