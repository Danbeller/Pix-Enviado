# Adicione limite para evitar DoS
def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    
    # Verificar tamanho máximo
    if os.path.getsize(LOG_FILE) > 10 * 1024 * 1024:  # 10MB
        print("Arquivo de logs muito grande")
        return []
    # ... resto do código
from flask import Flask, request, render_template_string, redirect, session
from datetime import datetime
import requests
import json
import os

app = Flask(__name__)

# 🔐 segurança via variáveis de ambiente
app.secret_key = os.environ.get("SECRET_KEY", "trocar_essa_chave")

# 📂 usar /tmp no Railway
LOG_FILE = "/tmp/logs.json"

# ================= IP =================
def get_real_ip(req):
    if req.headers.get('X-Forwarded-For'):
        return req.headers.get('X-Forwarded-For').split(',')[0].strip()
    return req.remote_addr

# ================= GEO =================
def get_ip_info(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = res.json()
        if data.get('status') == 'success':
            return data
    except Exception as e:
        print("Erro GEO:", e)
    return {}

# ================= LOAD =================
def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

# ================= SAVE =================
def save_log(entry):
    logs = load_logs()
    logs.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

# ================= HOME =================
@app.route('/')
def home():
    ip = get_real_ip(request)
    ua = request.headers.get('User-Agent')
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    info = get_ip_info(ip)

    logs = load_logs()
    repetido = any(l['ip'] == ip for l in logs)

    entry = {
        "ip": ip,
        "cidade": info.get("city", "N/A"),
        "pais": info.get("country", "N/A"),
        "isp": info.get("isp", "N/A"),
        "lat": info.get("lat"),
        "lon": info.get("lon"),
        "hora": now,
        "ua": ua,
        "repetido": repetido
    }

    save_log(entry)

    return "<h3>Carregando documento...</h3>"

# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    senha_correta = os.environ.get("ADMIN_PASSWORD", "admin123")

    if request.method == 'POST':
        if request.form.get("senha") == senha_correta:
            session['logado'] = True
            return redirect('/painel')

    return '''
    <form method="post" style="text-align:center;margin-top:100px;">
        <h2>Painel Seguro</h2>
        <input type="password" name="senha" placeholder="Senha"/>
        <br><br>
        <button>Entrar</button>
    </form>
    '''

# ================= PAINEL =================
@app.route('/painel')
def painel():
    if not session.get('logado'):
        return redirect('/login')

    logs = load_logs()

    html = """
    <html>
    <head>
        <title>Painel</title>
        <style>
            body { background:#0f172a; color:#e2e8f0; font-family:Arial; }
            .card { background:#1e293b; padding:15px; margin:10px; border-radius:10px; }
            .red { color:red; }
        </style>
    </head>
    <body>

    <h1>Painel de Rastreamento</h1>

    {% for l in logs %}
        <div class="card">
            <b>IP:</b> {{l.ip}} {% if l.repetido %}<span class="red">(Repetido)</span>{% endif %}<br>
            <b>Local:</b> {{l.cidade}} - {{l.pais}}<br>
            <b>ISP:</b> {{l.isp}}<br>
            <b>Hora:</b> {{l.hora}}<br>
            <b>User-Agent:</b> {{l.ua}}<br>
        </div>
    {% endfor %}

    </body>
    </html>
    """

    return render_template_string(html, logs=logs)

# ================= EXPORT =================
@app.route('/export')
def export():
    if not os.path.exists(LOG_FILE):
        return "Sem logs ainda"
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
