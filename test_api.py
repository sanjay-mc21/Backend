import requests
import json

# Server URL
BASE_URL = "http://localhost:8000/api"

def test_login():
    """Test login and get token"""
    response = requests.post(
        f"{BASE_URL}/login/",
        json={
            "username": "superadmin",
            "password": "demopassword"  # Use the demo password from your login view
        },
        headers={
            "Content-Type": "application/json"
        }
    )
    
    print(f"Login Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("token")
        return token
    return None

def test_create_admin(token):
    """Test creating an admin user"""
    if not token:
        print("No authentication token available")
        return
    
    # Create a test admin user
    admin_data = {
        "username": "testadmin3",
        "email": "testadmin3@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "Admin",
        "role": "ADMIN"
    }
    
    # Make the request
    response = requests.post(
        f"{BASE_URL}/users/",
        data=json.dumps(admin_data),
        headers={
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }
    )
    
    print(f"\nCreate Admin Status: {response.status_code}")
    print(f"Request Headers: {response.request.headers}")
    print(f"Request Body: {response.request.body}")
    print(f"Response Headers: {response.headers}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    token = test_login()
    if token:
        print(f"\nAuthentication successful. Token: {token}")
        test_create_admin(token)
    else:
        print("Authentication failed") 