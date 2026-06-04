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

conn = sqlite3.connect('/root/.n8n/database.sqlite')
cur = conn.cursor()

# Find active workflows
cur.execute("SELECT id, name, active, activeVersionId FROM workflow_entity")
workflows = cur.fetchall()

print("=== SEARCHING ACTIVE WORKFLOWS FOR BAD CREDENTIALS (9eiWE5YLlEZDffTx) ===")
for wf_id, name, active, active_version_id in workflows:
    # We check the active version if active, otherwise check the draft version
    if active and active_version_id:
        cur.execute("SELECT nodes FROM workflow_history WHERE versionId=?", (active_version_id,))
        row = cur.fetchone()
        if row and row[0]:
            nodes = json.loads(row[0])
        else:
            # Fallback to draft
            cur.execute("SELECT nodes FROM workflow_entity WHERE id=?", (wf_id,))
            nodes = json.loads(cur.fetchone()[0])
    else:
        cur.execute("SELECT nodes FROM workflow_entity WHERE id=?", (wf_id,))
        nodes = json.loads(cur.fetchone()[0])

    for node in nodes:
        creds = node.get('credentials', {})
        for ctype, cinfo in creds.items():
            cid = cinfo.get('id')
            if cid == '9eiWE5YLlEZDffTx':
                print(f"  Found bad creds in Workflow '{name}' (ID: {wf_id}, Active: {active}): Node '{node['name']}' ({node['type']})")

conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/check_all_wfs_creds.py', 'w') as f:
        f.write(db_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/check_all_wfs_creds.py")
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print("Error:", err)

    client.exec_command("rm -f /tmp/check_all_wfs_creds.py")
    client.close()

except Exception as e:
    print(f"Error: {e}")
