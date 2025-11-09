import sys
sys.path.insert(0, '.')

from app.auth import verify_user

# Test login
username = "gouenji92"
password = "123456"

result = verify_user(username, password)

if result:
    print(f"✅ Login SUCCESS!")
    print(f"   User: {result}")
else:
    print(f"❌ Login FAILED!")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
