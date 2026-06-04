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

    # Helper script to execute SQLite query inside VM
    db_script = """import sqlite3
import json
conn = sqlite3.connect('/root/.n8n/database.sqlite')
cur = conn.cursor()
cur.execute("SELECT staticData FROM workflow_entity WHERE id='8I4m2tzGDXQnjS3n'")
row = cur.fetchone()
if row and row[0]:
    sd = json.loads(row[0])
    print("Keys in staticData:", list(sd.keys()))
    global_data = sd.get('global', {})
    print("Keys in global_data:", list(global_data.keys()))
    history = global_data.get('priceHistory', [])
    print("Price history length:", len(history))
    if history:
        print("First 3 entries:")
        for e in history[:3]:
            print("  ", e)
        print("Last 3 entries:")
        for e in history[-3:]:
            print("  ", e)
else:
    print("Workflow staticData not found")
conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/get_static.py', 'w') as f:
        f.write(db_script)
    sftp.close()

    out, err = ssh_run(client, "python3 /tmp/get_static.py")
    print(out)
    if err:
        print("Error:", err)

    ssh_run(client, "rm -f /tmp/get_static.py")
    client.close()

except Exception as e:
    print(f"Error: {e}")
