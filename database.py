import sqlite3
from pathlib import Path
from datetime import date, timedelta

DEFAULT_DB = Path("estoque.db")

class InventoryDB:
    def __init__(self, path=DEFAULT_DB):
        self.path = str(path)
        self._init()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self.connect() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS products(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                barcode TEXT UNIQUE,
                description TEXT DEFAULT '',
                quantity INTEGER NOT NULL DEFAULT 0,
                min_stock INTEGER NOT NULL DEFAULT 0,
                expiry TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS movements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                note TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )""")

    def add_product(self, name, barcode="", description="", quantity=0, min_stock=0, expiry=None):
        with self.connect() as c:
            cur = c.execute("""INSERT INTO products(name,barcode,description,quantity,min_stock,expiry)
                VALUES(?,?,?,?,?,?)""",
                (name.strip(), barcode.strip() or None, description.strip(), int(quantity), int(min_stock), expiry or None))
            pid = cur.lastrowid
            if int(quantity) > 0:
                c.execute("INSERT INTO movements(product_id,kind,quantity,note) VALUES(?,?,?,?)",
                          (pid, "ENTRADA", int(quantity), "Saldo inicial"))
            return pid

    def update_product(self, pid, name, barcode="", description="", min_stock=0, expiry=None):
        with self.connect() as c:
            c.execute("""UPDATE products SET name=?,barcode=?,description=?,min_stock=?,expiry=?,
                updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                (name.strip(), barcode.strip() or None, description.strip(), int(min_stock), expiry or None, int(pid)))

    def delete_product(self, pid):
        with self.connect() as c:
            c.execute("DELETE FROM movements WHERE product_id=?", (int(pid),))
            c.execute("DELETE FROM products WHERE id=?", (int(pid),))

    def list_products(self, query=""):
        q = f"%{query.strip()}%"
        with self.connect() as c:
            rows = c.execute("""SELECT * FROM products
                WHERE name LIKE ? OR COALESCE(barcode,'') LIKE ? OR COALESCE(description,'') LIKE ?
                ORDER BY name COLLATE NOCASE""", (q,q,q)).fetchall()
            return [dict(r) for r in rows]

    def get_product(self, pid):
        with self.connect() as c:
            r = c.execute("SELECT * FROM products WHERE id=?", (int(pid),)).fetchone()
            return dict(r) if r else None

    def find_barcode(self, barcode):
        with self.connect() as c:
            r = c.execute("SELECT * FROM products WHERE barcode=?", (barcode.strip(),)).fetchone()
            return dict(r) if r else None

    def move(self, pid, kind, quantity, note=""):
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        kind = kind.upper()
        if kind not in ("ENTRADA", "SAÍDA"):
            raise ValueError("Tipo de movimentação inválido.")
        with self.connect() as c:
            row = c.execute("SELECT quantity FROM products WHERE id=?", (int(pid),)).fetchone()
            if not row:
                raise ValueError("Produto não encontrado.")
            current = int(row["quantity"])
            updated = current + quantity if kind == "ENTRADA" else current - quantity
            if updated < 0:
                raise ValueError("Não há saldo suficiente para essa saída.")
            c.execute("UPDATE products SET quantity=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (updated, int(pid)))
            c.execute("INSERT INTO movements(product_id,kind,quantity,note) VALUES(?,?,?,?)",
                      (int(pid), kind, quantity, note.strip()))

    def movements(self, limit=100):
        with self.connect() as c:
            rows = c.execute("""SELECT m.*,p.name,p.barcode FROM movements m
                LEFT JOIN products p ON p.id=m.product_id
                ORDER BY m.id DESC LIMIT ?""", (int(limit),)).fetchall()
            return [dict(r) for r in rows]

    def stats(self):
        today = date.today()
        soon = (today + timedelta(days=30)).isoformat()
        today_s = today.isoformat()
        with self.connect() as c:
            total = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            expired = c.execute("SELECT COUNT(*) FROM products WHERE expiry IS NOT NULL AND expiry < ?", (today_s,)).fetchone()[0]
            due = c.execute("SELECT COUNT(*) FROM products WHERE expiry >= ? AND expiry <= ?", (today_s, soon)).fetchone()[0]
            low = c.execute("SELECT COUNT(*) FROM products WHERE quantity <= min_stock").fetchone()[0]
            units = c.execute("SELECT COALESCE(SUM(quantity),0) FROM products").fetchone()[0]
        return {"total": total, "expired": expired, "soon": due, "low": low, "units": units}
