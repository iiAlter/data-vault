-- DataVault 数据库结构
-- SQLite

-- 数据类型注册表（所有数据类型的元数据）
CREATE TABLE IF NOT EXISTS data_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_type TEXT NOT NULL UNIQUE,  -- 'links', 'expenses', etc.
    label TEXT NOT NULL,              -- 显示名称
    description TEXT,                -- 说明
    icon TEXT DEFAULT '📊',          -- 图标
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 链接收藏表
CREATE TABLE IF NOT EXISTS links (
    id TEXT PRIMARY KEY,              -- YYYYMMDDHHMMSS 格式
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    source TEXT,
    summary TEXT,
    category TEXT DEFAULT '其他',
    tags TEXT,                        -- JSON 数组存储
    collected_at TEXT NOT NULL,       -- ISO 格式
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 消费记录表
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'CNY',
    category TEXT NOT NULL,
    description TEXT,
    date TEXT NOT NULL,               -- YYYY-MM-DD 格式
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 初始化数据类型注册
INSERT OR IGNORE INTO data_registry (data_type, label, description, icon) VALUES
    ('links', '链接收藏', '李子收藏的链接', '🔗'),
    ('expenses', '消费记录', '日常消费明细', '💰');
