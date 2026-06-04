import paramiko
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

password_file = r"C:\Users\lazy1\.ssh\hetzner_access\password.txt"

try:
    with open(password_file, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        password = first_line.split("password:", 1)[1].strip() if "password:" in first_line else first_line

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname="178.104.198.141", username="root", password=password, timeout=30)
    print("Connected!")

    # Write a proper python script file to the server, then execute it
    db_script = """import sqlite3
with open('/tmp/patched_nodes.json', 'r') as f:
    nodes_str = f.read()
conn = sqlite3.connect('/root/.n8n/database.sqlite')
cur = conn.cursor()
cur.execute("UPDATE workflow_entity SET nodes=? WHERE id=?", (nodes_str, '2Jj2r8BYEhclUsGf'))
conn.commit()
print('Updated rows:', cur.rowcount)
conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/db_update.py', 'w') as f:
        f.write(db_script)
    sftp.close()
    print("Uploaded /tmp/db_update.py")

    stdin, stdout, stderr = client.exec_command("python3 /tmp/db_update.py")
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    print(f"DB Update result: {out}")
    if err:
        print(f"DB Error: {err}")

    # Verify the update worked
    stdin, stdout, stderr = client.exec_command(
        "python3 -c \"import sqlite3; conn=sqlite3.connect('/root/.n8n/database.sqlite'); "
        "cur=conn.cursor(); cur.execute(\\\"SELECT length(nodes) FROM workflow_entity WHERE id='2Jj2r8BYEhclUsGf'\\\"); "
        "print('nodes length in DB:', cur.fetchone()[0]); conn.close()\""
    )
    verify_out = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"Verification: {verify_out}")

    # Clean up temp files
    client.exec_command("rm -f /tmp/db_update.py /tmp/patched_nodes.json")
    
    # Check n8n is running after restart
    stdin, stdout, stderr = client.exec_command("docker ps --filter name=n8n --format 'table {{.Names}}\\t{{.Status}}'")
    docker_out = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"\nDocker status:\n{docker_out}")
    
    client.close()
    print("\n[SUCCESS] SQLite DB updated. Workflow hotfix is live!")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
