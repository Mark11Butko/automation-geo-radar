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

    update_script = """import sqlite3
import json
import uuid

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

print(f"Loaded workflow draft. Nodes count: {len(nodes)}")

# Define the user filter and geolocation normalizer JS code
js_code = \"\"\"const userIps = [
  '46.34.251.226',
  '84.245.121.104',
  '84.245.120.175',
  '195.91.12.118',
  '62.197.198.132'
];

const results = [];

for (const item of $input.all()) {
  const data = item.json;
  const ip = data.ip;
  if (!ip || ip === 'Unknown' || ip === '127.0.0.1' || ip === '::1') {
    continue;
  }

  const isUser = userIps.includes(ip) || 
                 ip.startsWith('46.34.') || 
                 ip.startsWith('84.245.120.') || 
                 ip.startsWith('84.245.121.');

  if (isUser) {
    continue;
  }

  let city = data.city || 'N/A';
  let country = data.country || 'N/A';
  let lat = data.latitude || null;
  let lon = data.longitude || null;

  let connection = data.connection || {};
  let org = connection.org || '';
  let isp = connection.isp || '';

  let finalOrg = org.trim();
  if (!finalOrg || finalOrg.toLowerCase() === 'n/a') {
    finalOrg = isp.trim();
  }
  if (!finalOrg) {
    finalOrg = 'N/A';
  }

  let finalIsp = isp.trim() || 'N/A';

  let security = data.security || {};
  let isVpnOrProxy = security.vpn || security.proxy || security.tor || security.hosting || false;

  results.push({
    json: {
      ip: ip,
      city: city,
      country: country,
      org: finalOrg,
      isp: finalIsp,
      latitude: lat,
      longitude: lon,
      isVpnOrProxy: isVpnOrProxy
    }
  });
}

return results;\"\"\"

# Define the Telegram alert HTML text template
tg_text = \"\"\"=🔍 <b>АКТИВНОСТЬ НА САЙТЕ (TRACKER)</b>

⚡ <b>Событие:</b> {{ $('Data Normalizer (Smart)').first().json.event }}
🔗 <b>Источник:</b> {{ $('Data Normalizer (Smart)').first().json.referrer }}
🏢 <b>Организация:</b> {{ $json.org }} / {{ $json.isp }}
📍 <b>Локация:</b> <a href="https://www.google.com/maps?q={{ $json.latitude }},{{ $json.longitude }}">{{ $json.city }}, {{ $json.country }}</a>
🖥️ <b>Устройство:</b> {{ $('Data Normalizer (Smart)').first().json.userAgent || 'N/A' }}
📏 <b>Экран:</b> {{ $('Data Normalizer (Smart)').first().json.resolution || 'N/A' }}
🌐 <b>Язык:</b> {{ $('Data Normalizer (Smart)').first().json.lang || 'N/A' }}
🛡️ <b>VPN/Бот:</b> {{ $json.isVpnOrProxy ? 'Да 🤖' : 'Нет 👤' }}
🌐 <b>IP:</b> {{ $json.ip || 'N/A' }}\"\"\"

new_node_id = str(uuid.uuid4())

# 1. Update existing nodes or insert new ones
updated_nodes = []
geo_node_found = False
tg_node_found = False

for node in nodes:
    if node['name'] == 'IP Geolocation':
        node['parameters'] = {
            "url": "=https://ipwho.is/{{ $json.ip }}",
            "options": {}
        }
        node['typeVersion'] = 4.1
        geo_node_found = True
        updated_nodes.append(node)
    elif node['name'] == 'Telegram Alert (Rich)':
        node['parameters'] = {
            "chatId": "464591691",
            "text": tg_text,
            "additionalFields": {
                "appendAttribution": False,
                "parse_mode": "HTML"
            }
        }
        node['position'] = [256, 1024]
        tg_node_found = True
        updated_nodes.append(node)
    else:
        updated_nodes.append(node)

# Create and add the new Code Node
normalize_node = {
    "parameters": {
        "mode": "runOnceForAllItems",
        "jsCode": js_code
    },
    "name": "Normalize Geolocation",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [64, 1024],
    "id": new_node_id
}
updated_nodes.append(normalize_node)

# 2. Update connections dict
# Remove the old connection IP Geolocation -> Telegram Alert (Rich)
# And add IP Geolocation -> Normalize Geolocation -> Telegram Alert (Rich)
if 'IP Geolocation' in connections:
    connections['IP Geolocation']['main'] = [
        [
            {
                "node": "Normalize Geolocation",
                "type": "main",
                "index": 0
            }
        ]
    ]

connections['Normalize Geolocation'] = {
    "main": [
        [
            {
                "node": "Telegram Alert (Rich)",
                "type": "main",
                "index": 0
            }
        ]
    ]
}

print("Workflow draft nodes and connections modified locally in script.")

# 3. Update database
# Update draft version
cur.execute("UPDATE workflow_entity SET nodes=?, connections=? WHERE id='pP5tmGtJfoiwU7PK'",
            (json.dumps(updated_nodes), json.dumps(connections)))

# Update published version in history if active
if active_version_id:
    cur.execute("UPDATE workflow_history SET nodes=?, connections=? WHERE versionId=?",
                (json.dumps(updated_nodes), json.dumps(connections), active_version_id))
    print(f"Updated active version {active_version_id} in workflow_history!")

conn.commit()
print("Successfully saved modifications to SQLite database!")
conn.close()
"""
    sftp = client.open_sftp()
    with sftp.open('/tmp/run_update_wf.py', 'w') as f:
        f.write(update_script)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/run_update_wf.py")
    print(stdout.read().decode('utf-8', errors='replace'))
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print("Error:", err)

    client.exec_command("rm -f /tmp/run_update_wf.py")
    client.close()

except Exception as e:
    print(f"Error: {e}")
