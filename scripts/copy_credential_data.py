import paramiko
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

password_file = r"C:\Users\lazy1\.ssh\hetzner_access\password.txt"

try:
    with open(password_file, 'r', encoding='utf-8') as f:
        line = f.readline().strip()
        password = line.split("password:", 1)[1].strip() if "password:" in line else line

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="178.104.198.141", username="root", password=password, timeout=30)
    print("Connected to Hetzner!")

    db_script = """import sqlite3

db_path = '/root/.n8n/database.sqlite'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get encrypted data of huMb6dTyl9jvJRAZ (working key)
cur.execute("SELECT data FROM credentials_entity WHERE id='huMb6dTyl9jvJRAZ'")
working_data = cur.fetchone()[0]

print(f"Working credential encrypted data (len={len(working_data)})")

# Update 9eiWE5YLlEZDffTx with working data
cur.execute("UPDATE credentials_entity SET data=? WHERE id='9eiWE5YLlEZDffTx'", (working_data,))
conn.commit()
print("Updated credential '9eiWE5YLlEZDffTx' with working encrypted data!")

# Let's verify the database content is indeed matching
cur.execute("SELECT data FROM credentials_entity WHERE id='9eiWE5YLlEZDffTx'")
updated_data = cur.fetchone()[0]
if updated_data == working_data:
    print("Verification: Data successfully copied in SQLite!")
else:
    print("Verification failed! Data does not match!")

conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/copy_creds.py', 'w') as f:
        f.write(db_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/copy_creds.py")
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print("Error:", err)

    client.exec_command("rm -f /tmp/copy_creds.py")
    
    # Run n8n decrypted export to verify n8n can actually decrypt the copied credential
    print("\nRunning export to verify n8n decryption...")
    stdin, stdout, stderr = client.exec_command("docker exec n8n n8n export:credentials --decrypted --all")
    out = stdout.read().decode('utf-8', errors='replace').strip()
    import json
    try:
        creds = json.loads(out)
        gemini_creds = [c for c in creds if c.get('type') == 'googlePalmApi']
        print(json.dumps(gemini_creds, indent=2))
    except Exception as e:
        print("Failed to parse decrypted output:", e)
        print(out[:1000])

    client.close()

except Exception as e:
    print(f"Error: {e}")
