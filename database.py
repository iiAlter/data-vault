"""
DataVault 数据库操作层
SQLite + Python
"""
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "vault.db")

def get_conn():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()
    conn = get_conn()
    conn.executescript(schema)
    conn.commit()
    conn.close()

# ============ Links 操作 ============

def add_link(url, title, source=None, summary=None, category="其他", tags=None, note=None):
    """添加链接"""
    conn = get_conn()
    link_id = datetime.now().strftime("%Y%m%d%H%M%S")
    tags_json = json.dumps(tags, ensure_ascii=False) if tags else "[]"
    conn.execute("""
        INSERT INTO links (id, url, title, source, summary, category, tags, collected_at, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (link_id, url, title, source, summary, category, tags_json,
          datetime.now().isoformat(timespec="seconds"), note))
    conn.commit()
    conn.close()
    return link_id

def get_links(category=None, search=None, limit=100):
    """获取链接列表"""
    conn = get_conn()
    query = "SELECT * FROM links WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (title LIKE ? OR summary LIKE ? OR url LIKE ?)"
        params.extend([f"%{search}%"] * 3)
    query += " ORDER BY collected_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_link_stats():
    """链接统计"""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    by_category = conn.execute("""
        SELECT category, COUNT(*) as count
        FROM links GROUP BY category ORDER BY count DESC
    """).fetchall()
    by_source = conn.execute("""
        SELECT source, COUNT(*) as count
        FROM links GROUP BY source ORDER BY count DESC LIMIT 10
    """).fetchall()
    conn.close()
    return {
        "total": total,
        "by_category": [dict(r) for r in by_category],
        "by_source": [dict(r) for r in by_source]
    }

# ============ Expenses 操作 ============

def add_expense(amount, category, description=None, date=None, currency="CNY"):
    """添加消费"""
    conn = get_conn()
    date = date or datetime.now().strftime("%Y-%m-%d")
    conn.execute("""
        INSERT INTO expenses (amount, currency, category, description, date)
        VALUES (?, ?, ?, ?, ?)
    """, (amount, currency, category, description, date))
    conn.commit()
    conn.close()

def get_expenses(month=None, category=None, limit=100):
    """获取消费列表"""
    conn = get_conn()
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if month:
        query += " AND date LIKE ?"
        params.append(f"{month}%")
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY date DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_expense_stats(month=None):
    """消费统计"""
    conn = get_conn()
    where = f"WHERE date LIKE '{month}%'" if month else ""
    total = conn.execute(f"SELECT SUM(amount) FROM expenses {where}").fetchone()[0] or 0
    by_category = conn.execute(f"""
        SELECT category, SUM(amount) as total, COUNT(*) as count
        FROM expenses {where} GROUP BY category ORDER BY total DESC
    """).fetchall()
    by_month = conn.execute("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total
        FROM expenses GROUP BY month ORDER BY month DESC LIMIT 12
    """).fetchall()
    conn.close()
    return {
        "total": round(total, 2),
        "by_category": [dict(r) for r in by_category],
        "by_month": [dict(r) for r in by_month]
    }

# ============ 通用操作 ============

def get_registry():
    """获取所有数据类型"""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM data_registry ORDER BY data_type").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_stats():
    """全局统计"""
    return {
        "links": get_link_stats(),
        "expenses": get_expense_stats()
    }

def get_all_stats_fast():
    """合并版全局统计 — 单次连接，顺序执行所有查询"""
    conn = get_conn()
    links_total = conn.execute("SELECT COUNT(*) as total FROM links").fetchone()[0]
    links_cat   = [dict(r) for r in conn.execute("SELECT category, COUNT(*) as count FROM links GROUP BY category ORDER BY count DESC").fetchall()]
    links_src   = [dict(r) for r in conn.execute("SELECT source, COUNT(*) as count FROM links GROUP BY source ORDER BY count DESC LIMIT 10").fetchall()]
    etotal      = conn.execute("SELECT SUM(amount) as total FROM expenses").fetchone()[0] or 0
    exp_cat     = [dict(r) for r in conn.execute("SELECT category, SUM(amount) as total, COUNT(*) as count FROM expenses GROUP BY category ORDER BY total DESC").fetchall()]
    exp_month   = [dict(r) for r in conn.execute("SELECT strftime('%Y-%m', date) as month, SUM(amount) as total FROM expenses GROUP BY month ORDER BY month DESC LIMIT 12").fetchall()]
    conn.close()
    return {
        "links": {
            "total": links_total,
            "by_category": links_cat,
            "by_source": links_src,
        },
        "expenses": {
            "total": round(etotal, 2),
            "by_category": exp_cat,
            "by_month": exp_month,
        }
    }
