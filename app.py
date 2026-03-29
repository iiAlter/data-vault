"""
DataVault Flask 后端
"""
import os
import secrets
import hashlib
from functools import wraps
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, make_response

import database as db

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# ============ Token 配置 ============
TOKEN_FILE = os.path.expanduser("~/.data-vault-token")
DATA_VAULT_TOKEN = os.environ.get("DATA_VAULT_TOKEN", "").strip()

def _load_token():
    """获取有效 token"""
    if DATA_VAULT_TOKEN:
        return DATA_VAULT_TOKEN
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    # 首次生成
    new_token = secrets.token_urlsafe(32)
    with open(TOKEN_FILE, "w") as f:
        f.write(new_token)
    os.chmod(TOKEN_FILE, 0o600)
    return new_token

DATA_TOKEN = _load_token()

# ============ Auth Middleware ============

def require_auth(f):
    """API 认证装饰器：校验 Bearer token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = request.cookies.get("dv_token", "")

        if not token or not secrets.compare_digest(token, DATA_TOKEN):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def require_page_auth(f):
    """页面认证装饰器：校验 cookie token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("dv_token", "")
        if not token or not secrets.compare_digest(token, DATA_TOKEN):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

# ============ API 路由 ============

@app.route("/api/registry")
@require_auth
def api_registry():
    return jsonify(db.get_registry())

@app.route("/api/stats")
@require_auth
def api_stats():
    return jsonify(db.get_all_stats())

@app.route("/api/token-verify", methods=["POST"])
def api_token_verify():
    """验证 token 是否正确（登录接口）"""
    data = request.json or {}
    token = data.get("token", "").strip()
    if secrets.compare_digest(token, DATA_TOKEN):
        resp = make_response(jsonify({"success": True}))
        resp.set_cookie("dv_token", token, httponly=True, samesite="Lax", max_age=86400 * 7)
        return resp
    return jsonify({"success": False, "error": "Token 无效"}), 401

@app.route("/api/logout", methods=["POST"])
@require_auth
def api_logout():
    resp = make_response(jsonify({"success": True}))
    resp.delete_cookie("dv_token")
    return resp

@app.route("/api/me")
@require_auth
def api_me():
    """当前登录状态"""
    return jsonify({"authenticated": True})

# --- Links ---

@app.route("/api/links", methods=["GET"])
@require_auth
def api_get_links():
    return jsonify(db.get_links(
        category=request.args.get("category"),
        search=request.args.get("search"),
        limit=int(request.args.get("limit", 100))
    ))

@app.route("/api/links", methods=["POST"])
@require_auth
def api_add_link():
    data = request.json
    link_id = db.add_link(
        url=data["url"],
        title=data["title"],
        source=data.get("source"),
        summary=data.get("summary"),
        category=data.get("category", "其他"),
        tags=data.get("tags"),
        note=data.get("note")
    )
    return jsonify({"success": True, "id": link_id})

@app.route("/api/links/stats")
@require_auth
def api_links_stats():
    return jsonify(db.get_link_stats())

# --- Expenses ---

@app.route("/api/expenses", methods=["GET"])
@require_auth
def api_get_expenses():
    return jsonify(db.get_expenses(
        month=request.args.get("month"),
        category=request.args.get("category"),
        limit=int(request.args.get("limit", 100))
    ))

@app.route("/api/expenses", methods=["POST"])
@require_auth
def api_add_expense():
    data = request.json
    db.add_expense(
        amount=float(data["amount"]),
        category=data["category"],
        description=data.get("description"),
        date=data.get("date"),
        currency=data.get("currency", "CNY")
    )
    return jsonify({"success": True})

@app.route("/api/expenses/stats")
@require_auth
def api_expenses_stats():
    return jsonify(db.get_expense_stats(month=request.args.get("month")))

# ============ 页面路由 ============

@app.route("/login")
def login_page():
    token = request.cookies.get("dv_token", "")
    if token and secrets.compare_digest(token, DATA_TOKEN):
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/")
@require_page_auth
def index():
    return render_template("index.html")

@app.route("/links")
@require_page_auth
def links_page():
    return render_template("links.html")

@app.route("/expenses")
@require_page_auth
def expenses_page():
    return render_template("expenses.html")

@app.route("/ports")
@require_page_auth
def ports_page():
    return render_template("ports.html")

@app.route("/settings")
@require_page_auth
def settings_page():
    return render_template("settings.html")

@app.route("/api/ports")
@require_auth
def api_ports():
    import subprocess
    import re

    ss_result = subprocess.run(
        ["ss", "-tlnp"],
        capture_output=True, text=True, timeout=10
    )

    ps_result = subprocess.run(
        ["ps", "aux"],
        capture_output=True, text=True, timeout=10
    )
    pid_map = {}
    for line in ps_result.stdout.strip().split("\n"):
        parts = line.split(None, 10)
        if len(parts) < 11:
            continue
        pid = parts[1]
        cmd = parts[10] if len(parts) > 10 else ""
        proc = cmd.split()[0] if cmd.strip() else ""
        if "/" in proc:
            proc = proc.split("/")[-1]
        if proc and not proc.startswith("["):
            pid_map[pid] = proc

    lsof_result = subprocess.run(
        ["lsof", "-i", "-P", "-n"],
        capture_output=True, text=True, timeout=10
    )
    lsof_map = {}
    for line in lsof_result.stdout.strip().split("\n"):
        parts = line.split()
        if len(parts) < 9:
            continue
        name = parts[-1] if parts else ""
        port_match = re.search(r':(\d+)$', name)
        if port_match:
            port = port_match.group(1)
            proc = parts[0]
            pid = parts[1]
            if port not in lsof_map:
                lsof_map[port] = (proc, pid)

    ports = []
    lines = ss_result.stdout.strip().split("\n")
    for line in lines[1:]:
        if not line.strip():
            continue
        port_match = re.search(r':(\d+)\s', line)
        port = port_match.group(1) if port_match else ""
        proc_match = re.search(r'pid=(\d+)', line)
        pid = proc_match.group(1) if proc_match else ""
        if pid:
            process = pid_map.get(pid, "")
        else:
            proc_name_match = re.search(r'users:\(\("([^"]+)",', line)
            process = proc_name_match.group(1) if proc_name_match else ""
        if not process and port in lsof_map:
            process, pid = lsof_map[port]
        state = line.split()[0] if line.split() else ""
        ports.append({
            "port": port,
            "state": state,
            "process": process,
            "pid": pid,
        })

    return jsonify({"ports": ports})

if __name__ == "__main__":
    print("DataVault 启动中...")
    print(f"访问 http://localhost:18001")
    print(f"Token: {DATA_TOKEN[:8]}... (完整 token 在 ~/.data-vault-token)")
    app.run(host="0.0.0.0", port=18001, debug=True)
