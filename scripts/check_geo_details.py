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

    # Helper script to execute SQLite query inside VM to print evaluation parameters
    db_script = """import sqlite3
import json

db_path = '/root/.n8n/database.sqlite'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get execution 2966 data
cur.execute("SELECT data FROM execution_data WHERE executionId='2966'")
row = cur.fetchone()
if row:
    data_json = json.loads(row[0])
    def de_index(val, data_list):
        if isinstance(val, str) and val.isdigit():
            idx = int(val)
            if 0 <= idx < len(data_list):
                return de_index(data_list[idx], data_list)
        if isinstance(val, dict):
            return {k: de_index(v, data_list) for k, v in val.items()}
        if isinstance(val, list):
            return [de_index(v, data_list) for v in val]
        return val
    
    root = de_index(data_json[0], data_json)
    runData = root.get('resultData', {}).get('runData', {})
    
    # Check IP Geolocation node data in detail
    geo_runs = runData.get('IP Geolocation', [])
    print(json.dumps(geo_runs, indent=2))

conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/check_geo_details.py', 'w') as f:
        f.write(db_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/check_geo_details.py")
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print("Error:", err)

    client.exec_command("rm -f /tmp/check_geo_details.py")
    client.close()

except Exception as e:
    print(f"Error: {e}")
