import os
import re
import subprocess
import shutil
from flask import Flask, render_template_string, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecret-change-this")

PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin Panel</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: monospace; background: #0d1117; color: #c9d1d9; min-height: 100vh; }
  .icon { width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; vertical-align: -3px; }
  .header { background: #161b22; padding: 16px 24px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { font-size: 18px; color: #58a6ff; display: flex; align-items: center; gap: 10px; }
  .header h1 .icon { width: 20px; height: 20px; }
  .logout { color: #f85149; text-decoration: none; font-size: 13px; display: inline-flex; align-items: center; gap: 6px; }
  .logout:hover { text-decoration: underline; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; padding: 24px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }
  .card h2 { font-size: 13px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
  .card h2 .icon { color: #58a6ff; }
  .stat { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #21262d; }
  .stat:last-child { border-bottom: none; }
  .stat-label { color: #8b949e; font-size: 13px; }
  .stat-value { color: #e6edf3; font-size: 13px; font-weight: bold; }
  .badge { padding: 2px 8px; border-radius: 4px; font-size: 12px; }
  .badge-green { background: #1a4731; color: #3fb950; }
  .badge-yellow { background: #3d2b00; color: #e3b341; }
  .badge-red { background: #4b1c1c; color: #f85149; }
  pre { font-size: 12px; color: #8b949e; white-space: pre-wrap; word-break: break-all; line-height: 1.6; }
  .progress-bar { background: #21262d; border-radius: 4px; height: 6px; margin-top: 6px; }
  .progress-fill { height: 6px; border-radius: 4px; background: #238636; }
  .progress-fill.warn { background: #e3b341; }
  .progress-fill.danger { background: #f85149; }

  /* Login */
  .login-wrap { display: flex; justify-content: center; align-items: center; min-height: 100vh; }
  .login-box { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 40px; width: 320px; }
  .login-box h1 { color: #58a6ff; font-size: 22px; margin-bottom: 24px; text-align: center; }
  .login-box input { width: 100%; padding: 10px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #e6edf3; font-size: 14px; margin-bottom: 12px; }
  .login-box input:focus { outline: none; border-color: #58a6ff; }
  .login-box button { width: 100%; padding: 10px; background: #238636; border: none; border-radius: 6px; color: #fff; font-size: 14px; cursor: pointer; }
  .login-box button:hover { background: #2ea043; }
  .error { color: #f85149; font-size: 13px; text-align: center; margin-bottom: 12px; }
</style>
</head>
<body>
{% if not logged_in %}
<div class="login-wrap">
  <div class="login-box">
    <h1><svg class="icon" style="width:24px;height:24px" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg> Admin Panel</h1>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="post" action="/login">
      <input type="password" name="password" placeholder="Şifre" autofocus>
      <button type="submit">Giriş Yap</button>
    </form>
  </div>
</div>
{% else %}
<div class="header">
  <h1><svg class="icon" viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg> Sunucu Admin Paneli</h1>
  <a class="logout" href="/logout"><svg class="icon" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg> Çıkış Yap</a>
</div>
<div class="grid">

  <!-- Disk Kullanımı -->
  <div class="card">
    <h2><svg class="icon" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.7-4 3-9 3s-9-1.3-9-3M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5"/></svg> Disk Kullanımı</h2>
    {% for disk in disks %}
    <div class="stat">
      <span class="stat-label">{{ disk.mount }}</span>
      <span class="stat-value">{{ disk.used }} / {{ disk.total }}</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill {% if disk.pct > 85 %}danger{% elif disk.pct > 70 %}warn{% endif %}"
           style="width: {{ disk.pct }}%"></div>
    </div>
    <div style="font-size:11px; color:#8b949e; margin: 4px 0 10px; text-align:right">
      %{{ disk.pct }} kullanılıyor — {{ disk.free }} boş
    </div>
    {% endfor %}
  </div>

  <!-- Bellek -->
  <div class="card">
    <h2><svg class="icon" viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3"/></svg> Bellek (RAM)</h2>
    {% for k, v in memory.items() %}
    <div class="stat">
      <span class="stat-label">{{ k }}</span>
      <span class="stat-value">{{ v }}</span>
    </div>
    {% endfor %}
    <div class="progress-bar" style="margin-top:12px">
      <div class="progress-fill {% if mem_pct > 85 %}danger{% elif mem_pct > 70 %}warn{% endif %}"
           style="width: {{ mem_pct }}%"></div>
    </div>
    <div style="font-size:11px; color:#8b949e; margin-top:4px; text-align:right">
      %{{ mem_pct }} kullanılıyor
    </div>
  </div>

  <!-- CPU Kullanımı -->
  <div class="card">
    <h2><svg class="icon" viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> CPU Kullanımı</h2>
    <div style="text-align:center; font-size:42px; font-weight:bold; color:{% if cpu_pct > 85 %}#f85149{% elif cpu_pct > 70 %}#e3b341{% else %}#3fb950{% endif %}; padding: 12px 0;">
      %{{ cpu_pct }}
    </div>
    <div class="progress-bar" style="margin-bottom:16px">
      <div class="progress-fill {% if cpu_pct > 85 %}danger{% elif cpu_pct > 70 %}warn{% endif %}"
           style="width: {{ cpu_pct }}%"></div>
    </div>
    {% for k, v in system.items() %}
    <div class="stat">
      <span class="stat-label">{{ k }}</span>
      <span class="stat-value">{{ v }}</span>
    </div>
    {% endfor %}
  </div>

  <!-- Siteler -->
  <div class="card">
    <h2><svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg> Siteler / Dizinler</h2>
    {% if sites %}
      {% for site in sites %}
      <div class="stat">
        <span class="stat-label">{{ site.name }}{% if site.port != '-' %} <span style="color:#58a6ff">:{{ site.port }}</span>{% endif %}</span>
        <span class="stat-value">{{ site.size }}</span>
      </div>
      {% endfor %}
    {% else %}
      <p style="color:#8b949e; font-size:13px">Site dizini bulunamadı.</p>
    {% endif %}
  </div>

  <!-- Çalışan Servisler -->
  <div class="card">
    <h2><svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg> Servisler</h2>
    {% for svc in services %}
    <div class="stat">
      <span class="stat-label">{{ svc.name }}</span>
      <span class="badge {% if svc.active %}badge-green{% else %}badge-red{% endif %}">
        {{ 'aktif' if svc.active else 'kapalı' }}
      </span>
    </div>
    {% endfor %}
  </div>

  <!-- Açık Portlar -->
  <div class="card">
    <h2><svg class="icon" viewBox="0 0 24 24"><path d="M9 2v6M15 2v6M6 8h12l-1 5a5 5 0 0 1-10 0z"/><path d="M12 17v5"/></svg> Dinlenen Portlar</h2>
    <pre>{{ ports }}</pre>
  </div>

</div>
{% endif %}
</body>
</html>
"""

def run(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return ""

def get_disks():
    disks = []
    out = run("df -h --output=target,size,used,avail,pcent -x tmpfs -x devtmpfs -x squashfs 2>/dev/null")
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            pct = int(parts[4].replace('%', ''))
        except Exception:
            pct = 0
        disks.append({
            "mount": parts[0],
            "total": parts[1],
            "used":  parts[2],
            "free":  parts[3],
            "pct":   pct
        })
    return disks

def get_cpu_usage():
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        vals = list(map(int, line.split()[1:]))
        idle1, total1 = vals[3], sum(vals)
        import time; time.sleep(0.5)
        with open("/proc/stat") as f:
            line = f.readline()
        vals = list(map(int, line.split()[1:]))
        idle2, total2 = vals[3], sum(vals)
        diff_total = total2 - total1
        diff_idle  = idle2 - idle1
        if diff_total == 0:
            return 0
        return int((diff_total - diff_idle) / diff_total * 100)
    except Exception:
        return 0

def get_memory():
    out = run("free -h")
    lines = out.splitlines()
    if len(lines) < 2:
        return {}
    parts = lines[1].split()
    return {
        "Toplam": parts[1] if len(parts) > 1 else "-",
        "Kullanılan": parts[2] if len(parts) > 2 else "-",
        "Boş": parts[3] if len(parts) > 3 else "-",
        "Paylaşılan": parts[4] if len(parts) > 4 else "-",
        "Önbellek": parts[5] if len(parts) > 5 else "-",
        "Kullanılabilir": parts[6] if len(parts) > 6 else "-",
    }, (int(parts[2].replace('G','').replace('M','').replace('K','')) if len(parts) > 2 else 0)

def mem_percent():
    out = run("free")
    lines = out.splitlines()
    if len(lines) < 2:
        return 0
    parts = lines[1].split()
    try:
        return int(int(parts[2]) / int(parts[1]) * 100)
    except Exception:
        return 0

def get_system():
    uptime = run("uptime -p")
    cpu_cores = run("nproc")
    cpu_model = run("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2").strip()
    load = run("cat /proc/loadavg | awk '{print $1, $2, $3}'")
    hostname = run("hostname")
    kernel = run("uname -r")
    ip = run("hostname -I | awk '{print $1}'")
    return {
        "Hostname": hostname,
        "IP": ip,
        "Kernel": kernel,
        "CPU": cpu_model or f"{cpu_cores} çekirdek",
        "CPU Çekirdek": cpu_cores,
        "Yük (1/5/15 dk)": load,
        "Çalışma Süresi": uptime,
    }

def get_nginx_site_ports():
    conf_dir = "/etc/nginx/sites-enabled"
    ports = {}
    if not os.path.isdir(conf_dir):
        return ports
    for fname in os.listdir(conf_dir):
        try:
            with open(os.path.join(conf_dir, fname)) as f:
                content = f.read()
        except Exception:
            continue
        for block in re.findall(r"server\s*\{(?:[^{}]|\{[^{}]*\})*\}", content):
            root_match = re.search(r"root\s+([^;]+);", block)
            if not root_match:
                continue
            root_path = root_match.group(1).strip().rstrip("/")
            proxy_match = re.search(r"proxy_pass\s+https?://[^:/]+:(\d+)", block)
            listen_match = re.search(r"listen\s+(\d+)", block)
            if proxy_match:
                ports[root_path] = proxy_match.group(1)
            elif listen_match:
                ports[root_path] = listen_match.group(1)
    return ports

def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

def get_nginx_proxy_keywords():
    """root direktifi olmayan, sadece proxy_pass kullanan configler için
    dosya adı ve server_name'den anahtar kelime çıkarır (bulanık eşleştirme için)."""
    conf_dir = "/etc/nginx/sites-enabled"
    entries = []
    if not os.path.isdir(conf_dir):
        return entries
    for fname in os.listdir(conf_dir):
        path = os.path.join(conf_dir, fname)
        try:
            with open(path) as f:
                content = f.read()
        except Exception:
            continue
        proxy_ports = re.findall(r"proxy_pass\s+https?://[^:/]+:(\d+)", content)
        if not proxy_ports:
            continue
        port = proxy_ports[0]
        keywords = {_norm(fname)}
        for sn_line in re.findall(r"server_name\s+([^;]+);", content):
            for token in sn_line.split():
                token = token.strip()
                if token.startswith("www."):
                    token = token[4:]
                if token and token != "_":
                    keywords.add(_norm(token.split(".")[0]))
        entries.append((keywords, port))
    return entries

def match_proxy_port(dirname, entries):
    norm_dir = _norm(dirname)
    if not norm_dir:
        return None
    for keywords, port in entries:
        for kw in keywords:
            if kw and (kw in norm_dir or norm_dir in kw):
                return port
    return None

def get_sites():
    dirs = ["/var/www", "/home", "/srv/www", "/srv"]
    paths = []
    seen = set()
    for base in dirs:
        if not os.path.isdir(base):
            continue
        try:
            for name in os.listdir(base):
                full = os.path.join(base, name)
                if os.path.isdir(full) and full not in seen:
                    seen.add(full)
                    paths.append(full)
        except Exception:
            pass

    sizes = {}
    if paths:
        quoted = " ".join(f"'{p}'" for p in paths)
        out = run(f"timeout 15 du -sh {quoted} 2>/dev/null")
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) == 2:
                sizes[parts[1]] = parts[0]

    ports = get_nginx_site_ports()
    proxy_entries = get_nginx_proxy_keywords()

    sites = []
    for full in paths:
        port = ports.get(full)
        if not port:
            port = match_proxy_port(os.path.basename(full), proxy_entries)
        sites.append({
            "name": full,
            "size": sizes.get(full, "?"),
            "port": port or "-",
        })
    return sites

def get_services():
    names = ["nginx", "apache2", "mysql", "mariadb", "postgresql", "php-fpm",
             "php8.4-fpm", "php8.3-fpm", "redis", "memcached", "ssh", "docker",
             "fail2ban", "ufw"]
    out = run(f"systemctl is-active {' '.join(names)} 2>/dev/null")
    statuses = out.splitlines()
    services = []
    for name, status in zip(names, statuses):
        if status and status != "unknown":
            services.append({"name": name, "active": status == "active"})
    return services

def get_ports():
    out = run("ss -tlnp 2>/dev/null | grep LISTEN | awk '{print $4, $6}' | sort")
    if not out:
        out = run("netstat -tlnp 2>/dev/null | grep LISTEN | awk '{print $4, $7}' | sort")
    return out or "Bilgi alınamadı"

@app.route("/login", methods=["POST"])
def login():
    if request.form.get("password") == PASSWORD:
        session["auth"] = True
        return redirect("/")
    return render_template_string(HTML, logged_in=False, error="Hatalı şifre!")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/")
def index():
    if not session.get("auth"):
        return render_template_string(HTML, logged_in=False, error=None)

    try:
        disks = get_disks()
    except Exception:
        disks = []
    mem_dict = {}
    mem_pct = 0
    try:
        mem_raw = run("free")
        out_h = run("free -h")
        raw_lines = mem_raw.splitlines()
        h_lines = out_h.splitlines()
        if len(raw_lines) > 1 and len(h_lines) > 1:
            parts = raw_lines[1].split()
            h_parts = h_lines[1].split()
            labels = ["Toplam","Kullanılan","Boş","Paylaşılan","Önbellek","Kullanılabilir"]
            for i, label in enumerate(labels):
                if i + 1 < len(h_parts):
                    mem_dict[label] = h_parts[i + 1]
            mem_pct = int(int(parts[2]) / int(parts[1]) * 100)
    except Exception:
        mem_pct = 0

    return render_template_string(HTML,
        logged_in=True,
        disks=disks,
        memory=mem_dict,
        mem_pct=mem_pct,
        cpu_pct=get_cpu_usage(),
        system=get_system(),
        sites=get_sites(),
        services=get_services(),
        ports=get_ports(),
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Admin panel http://0.0.0.0:{port} adresinde çalışıyor")
    print(f"Şifre: {PASSWORD}")
    app.run(host="0.0.0.0", port=port, debug=False)
