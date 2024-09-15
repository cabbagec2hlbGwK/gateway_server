import pyrebase

# Firebase configuration
firebase_config = {
    "apiKey": "AIzaSyC_toR8GM7k78fcEGl4lRgvAAQ2fS9zlQc",
    "authDomain": "digicontrol-ca3b7.firebaseapp.com",
    "projectId": "digicontrol-ca3b7",
    "storageBucket": "digicontrol-ca3b7.appspot.com",
    "messagingSenderId": "918916989686",
    "appId": "1:918916989686:web:ea82cb1d634bc8ea6fa2d7",
    "measurementId": "G-KS9TGY0KSH",
    "databaseURL": ""  # Add database URL if you're using Firebase database
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
    email = "test@test.ca"  # Replace with the actual user's email
    password = "test@123"  # Replace with the actual user's password
    
    token = generate_user_token(email, password)
    print(f"Generated ID token: {token}")

