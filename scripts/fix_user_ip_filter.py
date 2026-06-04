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
import json

db_path = '/root/.n8n/database.sqlite'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get workflow draft
cur.execute("SELECT nodes, connections, activeVersionId FROM workflow_entity WHERE id='pP5tmGtJfoiwU7PK'")
row = cur.fetchone()
if not row:
    print("Workflow not found!")
    exit(1)

nodes = json.loads(row[0])
active_version_id = row[2]

# Narrow down IP filter: replace '46.34.' with '46.34.251.'
updated = False
for node in nodes:
    if node['name'] == 'Normalize Geolocation':
        code = node['parameters']['jsCode']
        if "ip.startsWith('46.34.')" in code:
            node['parameters']['jsCode'] = code.replace("ip.startsWith('46.34.')", "ip.startsWith('46.34.251.')")
            print("Successfully narrowed down IP filter from '46.34.' to '46.34.251.'")
            updated = True
        else:
            print("String not found, checking if already updated...")

if updated:
    # Save draft
    cur.execute("UPDATE workflow_entity SET nodes=? WHERE id='pP5tmGtJfoiwU7PK'", (json.dumps(nodes),))

    # Save active version
    if active_version_id:
        cur.execute("UPDATE workflow_history SET nodes=? WHERE versionId=?", (json.dumps(nodes), active_version_id))
        print("Updated active version in workflow_history!")

    conn.commit()
    print("Changes saved successfully to SQLite!")
else:
    print("No changes made.")

conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/narrow_filter.py', 'w') as f:
        f.write(db_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/narrow_filter.py")
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print("Error:", err)

    client.exec_command("rm -f /tmp/narrow_filter.py")
    client.close()

except Exception as e:
    print(f"Error: {e}")
