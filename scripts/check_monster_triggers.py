import paramiko
import json

password_file = r"C:\Users\lazy1\.ssh\hetzner_access\password.txt"

try:
    with open(password_file, 'r', encoding='utf-8') as f:
        line = f.readline().strip()
        password = line.split("password:", 1)[1].strip() if "password:" in line else line

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="178.104.198.141", username="root", password=password, timeout=30)

    db_script = """import sqlite3
import json

db_path = '/root/.n8n/database.sqlite'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT nodes FROM workflow_entity WHERE id='8I4m2tzGDXQnjS3n'")
row = cur.fetchone()
if row:
    nodes = json.loads(row[0])
    for node in nodes:
        if node.get('name') in ('Schedule Trigger', 'Friday Digest Trigger'):
            print(f"Node '{node.get('name')}': {json.dumps(node.get('parameters'), indent=2)}")
else:
    print("Workflow not found!")
conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/check_triggers.py', 'w') as f:
        f.write(db_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/check_triggers.py")
    print(stdout.read().decode('utf-8'))
    client.exec_command("rm -f /tmp/check_triggers.py")
    client.close()

except Exception as e:
    print("Error:", e)
