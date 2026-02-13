import requests
import jwt
from datetime import datetime, timedelta, timezone
import sys

# Configuration
BASE_URL = 'http://127.0.0.1:8080'
SECRET_KEY = 'dev-secret-key' # Assuming this is the key being used
ADMIN_USER_ID = 1

def generate_admin_token():
    payload = {
        'user_id': ADMIN_USER_ID,
        'role': 'admin',
        'exp': datetime.now(timezone.utc) + timedelta(minutes=60)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def test_pdf_download():
    token = generate_admin_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"Testing PDF download from: {BASE_URL}/api/pos/reports/sales/pdf/download")
    
    try:
        response = requests.get(
            f'{BASE_URL}/api/pos/reports/sales/pdf/download',
            headers=headers,
            params={'token': token} # Send token in params too just in case
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code != 200:
            print("\nError Response Body:")
            print(response.text[:1000]) # Print first 1000 chars
        else:
            print("Success! Got PDF.")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == '__main__':
    test_pdf_download()
