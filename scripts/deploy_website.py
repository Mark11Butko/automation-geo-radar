import paramiko
import os

password_file = r"C:\Users\lazy1\.ssh\hetzner_access\password.txt"
local_html = r"C:\Users\lazy1\.gemini\antigravity\scratch\index.html"
local_i18n = r"C:\Users\lazy1\.gemini\antigravity\scratch\i18n.js"

remote_html = "/var/www/butkomark.com/index.html"
remote_i18n = "/var/www/butkomark.com/i18n.js"

try:
    with open(password_file, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        if "password:" in first_line:
            password = first_line.split("password:", 1)[1].strip()
        else:
            password = first_line

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print("Connecting to 178.104.198.141...")
    client.connect(hostname='178.104.198.141', username='root', password=password, timeout=15)
    print("Connected successfully!")

    sftp = client.open_sftp()
    
    print(f"Uploading {local_html} to {remote_html}...")
    sftp.put(local_html, remote_html)
    print("Uploaded index.html successfully.")
    
    print(f"Uploading {local_i18n} to {remote_i18n}...")
    sftp.put(local_i18n, remote_i18n)
    print("Uploaded i18n.js successfully.")
    
    sftp.close()
    
    print("Reloading Nginx service...")
    stdin, stdout, stderr = client.exec_command("systemctl reload nginx")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("Nginx reloaded successfully!")
    else:
        print("Failed to reload Nginx. stderr:")
        print(stderr.read().decode('utf-8'))
        
    client.close()
    print("Deployment completed!")
except Exception as e:
    print(f"Deployment error: {e}")
