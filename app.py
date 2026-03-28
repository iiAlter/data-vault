"""
DataVault Flask 后端
"""
from flask import Flask, jsonify, request, render_template
import database as db

app = Flask(__name__, template_folder="templates", static_folder="static")

# 确保数据库已初始化
db.init_db()

# ============ API 路由 ============

@app.route("/api/registry")
def api_registry():
    """数据类型注册表"""
    return jsonify(db.get_registry())

@app.route("/api/stats")
def api_stats():
    """全局统计"""
    return jsonify(db.get_all_stats())

# --- Links ---

@app.route("/api/links", methods=["GET"])
def api_get_links():
    return jsonify(db.get_links(
        category=request.args.get("category"),
        search=request.args.get("search"),
        limit=int(request.args.get("limit", 100))
    ))

@app.route("/api/links", methods=["POST"])
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
def api_links_stats():
    return jsonify(db.get_link_stats())

# --- Expenses ---

@app.route("/api/expenses", methods=["GET"])
def api_get_expenses():
    return jsonify(db.get_expenses(
        month=request.args.get("month"),
        category=request.args.get("category"),
        limit=int(request.args.get("limit", 100))
    ))

@app.route("/api/expenses", methods=["POST"])
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
def api_expenses_stats():
    return jsonify(db.get_expense_stats(month=request.args.get("month")))

# ============ 页面路由 ============

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/links")
def links_page():
    return render_template("links.html")

@app.route("/expenses")
def expenses_page():
    return render_template("expenses.html")

@app.route("/ports")
def ports_page():
    return render_template("ports.html")

@app.route("/settings")
def settings_page():
    return render_template("settings.html")

@app.route("/api/ports")
def api_ports():
    import subprocess
    import re

    # Run ss -tlnp
    ss_result = subprocess.run(
        ["ss", "-tlnp"],
        capture_output=True, text=True, timeout=10
    )

    # Build a pid->process map from ps aux
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

    # Get additional process info via lsof for listening ports
    lsof_result = subprocess.run(
        ["lsof", "-i", "-P", "-n"],
        capture_output=True, text=True, timeout=10
    )
    lsof_map = {}  # port -> (process, pid)
    for line in lsof_result.stdout.strip().split("\n"):
        parts = line.split()
        if len(parts) < 9:
            continue
        # lsof format: COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
        # NAME like: *:6806 or 127.0.0.1:6806
        name = parts[-1] if parts else ""
        port_match = re.search(r':(\d+)$', name)
        if port_match:
            port = port_match.group(1)
            proc = parts[0]
            pid = parts[1]
            if port not in lsof_map:
                lsof_map[port] = (proc, pid)

    # Parse ss output
    ports = []
    lines = ss_result.stdout.strip().split("\n")
    for line in lines[1:]:
        if not line.strip():
            continue
        port_match = re.search(r':(\d+)\s', line)
        port = port_match.group(1) if port_match else ""
        proc_match = re.search(r'pid=(\d+)', line)
        pid = proc_match.group(1) if proc_match else ""
        # Priority: ss data > ps map > lsof
        if pid:
            process = pid_map.get(pid, "")
        else:
            proc_name_match = re.search(r'users:\(\("([^"]+)",', line)
            process = proc_name_match.group(1) if proc_name_match else ""
        # Fill from lsof if still missing
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
    print("访问 http://localhost:18001")
    app.run(host="0.0.0.0", port=18001, debug=True)
