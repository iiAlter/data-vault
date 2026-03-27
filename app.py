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

if __name__ == "__main__":
    print("DataVault 启动中...")
    print("访问 http://localhost:5188")
    app.run(host="0.0.0.0", port=5188, debug=True)
