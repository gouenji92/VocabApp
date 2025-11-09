import json
import hashlib

# Hash password "123456"
password = "123456"
password_hash = hashlib.sha256(password.encode()).hexdigest()

# Read users
with open('data/users.json', 'r', encoding='utf-8') as f:
    users = json.load(f)

# Update password for gouenji92
for user in users:
    if user['username'] == 'gouenji92':
        user['password_hash'] = password_hash
        print(f"✅ Reset password for {user['username']}")
        break

# Save back
with open('data/users.json', 'w', encoding='utf-8') as f:
    json.dump(users, f, indent=2, ensure_ascii=False)

print("\n✅ Done! You can now login with:")
print("   Username: gouenji92")
print("   Password: 123456")
