import os
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
  .header { background: #161b22; padding: 16px 24px; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
  .header h1 { font-size: 18px; color: #58a6ff; }
  .logout { color: #f85149; text-decoration: none; font-size: 13px; }
  .logout:hover { text-decoration: underline; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; padding: 24px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }
  .card h2 { font-size: 13px; color: #8b949e; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 16px; }
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
    <h1>🔐 Admin Panel</h1>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="post" action="/login">
      <input type="password" name="password" placeholder="Şifre" autofocus>
      <button type="submit">Giriş Yap</button>
    </form>
  </div>
</div>
{% else %}
<div class="header">
  <h1>⚡ Sunucu Admin Paneli</h1>
  <a class="logout" href="/logout">Çıkış Yap</a>
</div>
<div class="grid">

  <!-- Disk Kullanımı -->
  <div class="card">
    <h2>💾 Disk Kullanımı</h2>
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
    <h2>🧠 Bellek (RAM)</h2>
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
    <h2>⚡ CPU Kullanımı</h2>
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
    <h2>🌐 Siteler / Dizinler</h2>
    {% if sites %}
      {% for site in sites %}
      <div class="stat">
        <span class="stat-label">{{ site.name }}</span>
        <span class="stat-value">{{ site.size }}</span>
      </div>
      {% endfor %}
    {% else %}
      <p style="color:#8b949e; font-size:13px">Site dizini bulunamadı.</p>
    {% endif %}
  </div>

  <!-- Çalışan Servisler -->
  <div class="card">
    <h2>⚙️ Servisler</h2>
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
    <h2>🔌 Dinlenen Portlar</h2>
    <pre>{{ ports }}</pre>
  </div>

</div>
{% endif %}
</body>
</html>
"""

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True).strip()
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

def get_sites():
    dirs = ["/var/www", "/home", "/srv/www", "/srv"]
    sites = []
    seen = set()
    for base in dirs:
        if not os.path.isdir(base):
            continue
        try:
            for name in os.listdir(base):
                full = os.path.join(base, name)
                if os.path.isdir(full) and full not in seen:
                    seen.add(full)
                    size = run(f"du -sh '{full}' 2>/dev/null | cut -f1")
                    sites.append({"name": f"{base}/{name}", "size": size or "?"})
        except Exception:
            pass
    return sites

def get_services():
    names = ["nginx", "apache2", "mysql", "mariadb", "postgresql", "php-fpm",
             "php8.4-fpm", "php8.3-fpm", "redis", "memcached", "ssh", "docker",
             "fail2ban", "ufw"]
    services = []
    for name in names:
        status = run(f"systemctl is-active {name} 2>/dev/null")
        if status:  # sadece sistemde olan servisleri göster
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
