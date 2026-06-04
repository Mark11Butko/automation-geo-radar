import paramiko

password_file = r"C:\Users\lazy1\.ssh\hetzner_access\password.txt"

try:
    with open(password_file, 'r', encoding='utf-8') as f:
        line = f.readline().strip()
        password = line.split("password:", 1)[1].strip() if "password:" in line else line

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="178.104.198.141", username="root", password=password, timeout=30)
    print("Connected to Hetzner!")

    # Check active database directly and print only ASCII
    db_script = """import sqlite3
import json

conn = sqlite3.connect('/root/.n8n/database.sqlite')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print("Tables count:", len(tables))
print("Tables list:", [t for t in tables if t.isascii()])

# Inspect version columns of Bender workflow
cur.execute("SELECT id, active, versionId, activeVersionId FROM workflow_entity WHERE id='yRmRVSebpTwDRGB8'")
row = cur.fetchone()
if row:
    print("Bender columns:")
    print("  id:", row[0])
    print("  active:", row[1])
    print("  versionId:", row[2])
    print("  activeVersionId:", row[3])

# Check if there is a workflow_version table
if 'workflow_version' in tables:
    cur.execute("SELECT count(*) FROM workflow_version WHERE workflowId='yRmRVSebpTwDRGB8'")
    print("Rows in workflow_version:", cur.fetchone()[0])
    
# Check if there is a workflow_history table
if 'workflow_history' in tables:
    cur.execute("SELECT count(*) FROM workflow_history WHERE workflowId='yRmRVSebpTwDRGB8'")
    print("Rows in workflow_history:", cur.fetchone()[0])

conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/list_db_tables.py', 'w') as f:
        f.write(db_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/list_db_tables.py")
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print("Error:", err)

    client.exec_command("rm -f /tmp/list_db_tables.py")
    client.close()

except Exception as e:
    print("Fatal Error:", e)
