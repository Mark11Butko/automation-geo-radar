import paramiko
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

password_file = r"C:\Users\lazy1\.ssh\hetzner_access\password.txt"

def ssh_run(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    return out, err

try:
    with open(password_file, 'r', encoding='utf-8') as f:
        line = f.readline().strip()
        password = line.split("password:", 1)[1].strip() if "password:" in line else line

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="178.104.198.141", username="root", password=password, timeout=30)
    print("Connected to Hetzner!")

    # Check all rows and nodes in workflow_entity
    db_script = """import sqlite3
import json
conn = sqlite3.connect('/root/.n8n/database.sqlite')
cur = conn.cursor()
cur.execute("SELECT id, name, active, nodes FROM workflow_entity")
rows = cur.fetchall()
print(f"Total workflows: {len(rows)}")
for r in rows:
    nodes = json.loads(r[3])
    parse_data_node = None
    for n in nodes:
        if n.get('name') == 'Parse Data1':
            parse_data_node = n
            break
    code_info = "No Parse Data1"
    if parse_data_node:
        code = parse_data_node.get('parameters', {}).get('jsCode', '')
        code_info = f"Parse Data1 code len: {len(code)}, has MAX_SINGLE_CAN_PRICE: {'MAX_SINGLE_CAN_PRICE' in code}, has 'energetický náпой': {'energetický náпой' in code}"
    print(f"ID: {r[0]}, Name: {r[1]}, Active: {r[2]}, {code_info}")
conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/debug_db.py', 'w') as f:
        f.write(db_script)
    sftp.close()
    
    out, _ = ssh_run(client, "python3 /tmp/debug_db.py")
    print(out)
    ssh_run(client, "rm -f /tmp/debug_db.py")

    client.close()

except Exception as e:
    print(f"\nFATAL: {type(e).__name__}: {e}")
