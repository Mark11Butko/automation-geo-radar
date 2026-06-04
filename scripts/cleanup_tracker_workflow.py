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

    cleanup_script = """import sqlite3
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
connections = json.loads(row[1])
active_version_id = row[2]

print(f"Nodes before cleanup: {[n['name'] for n in nodes]}")

# Filter nodes to keep only one "Normalize Geolocation" node
cleaned_nodes = []
geo_added = False
for node in nodes:
    if node['name'] == 'Normalize Geolocation':
        if not geo_added:
            cleaned_nodes.append(node)
            geo_added = True
    else:
        cleaned_nodes.append(node)

print(f"Nodes after cleanup: {[n['name'] for n in cleaned_nodes]}")

# Save draft
cur.execute("UPDATE workflow_entity SET nodes=? WHERE id='pP5tmGtJfoiwU7PK'", (json.dumps(cleaned_nodes),))

# Save history if active
if active_version_id:
    cur.execute("UPDATE workflow_history SET nodes=? WHERE versionId=?", (json.dumps(cleaned_nodes), active_version_id))
    print("Updated workflow_history active version!")

conn.commit()
print("Database cleanup committed successfully!")
conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/cleanup_nodes.py', 'w') as f:
        f.write(cleanup_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/cleanup_nodes.py")
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print("Error:", err)

    client.exec_command("rm -f /tmp/cleanup_nodes.py")
    client.close()

except Exception as e:
    print(f"Error: {e}")
