import paramiko
import io
import sys
import json

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

    # Helper script to execute SQLite query inside VM
    db_script = """import sqlite3
import json
conn = sqlite3.connect('/root/.n8n/database.sqlite')
cur = conn.cursor()
cur.execute("SELECT connections FROM workflow_entity WHERE id='8I4m2tzGDXQnjS3n'")
row = cur.fetchone()
if row and row[0]:
    conns = json.loads(row[0])
    print("=== Live Connections ===")
    for k, v in conns.items():
        if 'Loop' in k or 'Broadcast' in k or 'Rate' in k:
            print(f"{k} connects to:")
            print(json.dumps(v, indent=2))
else:
    print("Workflow not found")
conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/check_live_conns.py', 'w') as f:
        f.write(db_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/check_live_conns.py")
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print("Error:", err)

    client.exec_command("rm -f /tmp/check_live_conns.py")
    client.close()

except Exception as e:
    print(f"Error: {e}")
