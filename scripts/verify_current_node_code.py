import paramiko
import io
import sys
import json

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

    # Check workflow_entity columns and values for Parse Data1
    db_script = """import sqlite3
import json
conn = sqlite3.connect('/root/.n8n/database.sqlite')
cur = conn.cursor()
cur.execute("SELECT name, nodes, active FROM workflow_entity WHERE id='2Jj2r8BYEhclUsGf'")
row = cur.fetchone()
if row:
    name, nodes_str, active = row
    print("Workflow Name:", name)
    print("Active:", active)
    nodes = json.loads(nodes_str)
    for node in nodes:
        if node.get('name') == 'Parse Data1':
            code = node.get('parameters', {}).get('jsCode', '')
            print("--- Code length:", len(code))
            print("Contains MAX_SINGLE_CAN_PRICE?:", 'MAX_SINGLE_CAN_PRICE' in code)
            print("Contains MULTIPACK_STOPWORDS?:", 'MULTIPACK_STOPWORDS' in code)
            print("Contains 'energetický náпой'?:", 'energetický náпой' in code)
            print("Contains 'energetick\\\\u00fd n\\\\u00e1poj'?:", 'energetick\\u00fd n\\u00e1poj' in code)
            # Print first 200 and last 200 chars of code
            print("Start of code:\\n", code[:300])
            print("End of code:\\n", code[-300:])
else:
    print("Workflow not found")
conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/verify_db.py', 'w') as f:
        f.write(db_script)
    sftp.close()
    
    out, _ = ssh_run(client, "python3 /tmp/verify_db.py")
    print(out)
    ssh_run(client, "rm -f /tmp/verify_db.py")

    client.close()

except Exception as e:
    print(f"\nFATAL: {type(e).__name__}: {e}")
