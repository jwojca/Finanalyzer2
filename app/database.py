"""
SQLite database manager for FinAnalazer2.
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).parent.parent / "data" / "transactions.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_conn():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they don't exist."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
                color TEXT DEFAULT '#5599ff',
                is_transfer BOOLEAN DEFAULT 0,
                is_income BOOLEAN DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
                field TEXT DEFAULT 'all',
                priority INTEGER DEFAULT 0,
                note TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_posted TEXT,
                date_executed TEXT,
                description TEXT,
                message TEXT,
                payer_payee TEXT,
                account_number TEXT,
                ks TEXT,
                vs TEXT,
                ss TEXT,
                amount REAL,
                balance REAL,
                category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                is_manual_category BOOLEAN DEFAULT 0,
                import_hash TEXT UNIQUE NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date_posted);
            CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_hash ON transactions(import_hash);
            CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(category_id);
        """)
        # Migration: add note column if missing (safe to run on existing DB)
        try:
            conn.execute("ALTER TABLE keywords ADD COLUMN note TEXT DEFAULT ''")
        except Exception:
            pass


# ─── Categories ──────────────────────────────────────────────────────────────

def get_categories(parent_id=None) -> List[sqlite3.Row]:
    with get_conn() as conn:
        if parent_id is None:
            rows = conn.execute(
                "SELECT * FROM categories WHERE parent_id IS NULL ORDER BY name"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM categories WHERE parent_id = ? ORDER BY name",
                (parent_id,)
            ).fetchall()
    return rows


def get_all_categories() -> List[sqlite3.Row]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM categories ORDER BY parent_id NULLS FIRST, name"
        ).fetchall()
    return rows


def get_category_by_id(cat_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM categories WHERE id = ?", (cat_id,)
        ).fetchone()


def add_category(name: str, parent_id: Optional[int] = None,
                 color: str = '#5599ff',
                 is_transfer: bool = False,
                 is_income: bool = False) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO categories (name, parent_id, color, is_transfer, is_income) VALUES (?, ?, ?, ?, ?)",
            (name, parent_id, color, int(is_transfer), int(is_income))
        )
        return cur.lastrowid


def update_category(cat_id: int, name: str, color: str,
                    is_transfer: bool = False, is_income: bool = False,
                    parent_id: int = None):
    with get_conn() as conn:
        conn.execute(
            "UPDATE categories SET name=?, color=?, is_transfer=?, is_income=?, parent_id=? WHERE id=?",
            (name, color, int(is_transfer), int(is_income), parent_id, cat_id)
        )


def delete_category(cat_id: int):
    """Delete category and cascade to subcategories (via FK) and set transactions to NULL."""
    with get_conn() as conn:
        # Unlink transactions first
        conn.execute(
            "UPDATE transactions SET category_id=NULL, is_manual_category=0 WHERE category_id=?",
            (cat_id,)
        )
        # Also unlink transactions in subcategories
        sub_ids = [row[0] for row in conn.execute(
            "SELECT id FROM categories WHERE parent_id=?", (cat_id,)
        ).fetchall()]
        for sid in sub_ids:
            conn.execute(
                "UPDATE transactions SET category_id=NULL, is_manual_category=0 WHERE category_id=?",
                (sid,)
            )
        conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))


# ─── Keywords ────────────────────────────────────────────────────────────────

def get_keywords(category_id: Optional[int] = None) -> List[sqlite3.Row]:
    with get_conn() as conn:
        if category_id is not None:
            rows = conn.execute(
                """SELECT k.*, c.name as category_name
                   FROM keywords k JOIN categories c ON k.category_id=c.id
                   WHERE k.category_id=?
                   ORDER BY k.priority DESC, k.keyword""",
                (category_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT k.*, c.name as category_name
                   FROM keywords k JOIN categories c ON k.category_id=c.id
                   ORDER BY k.priority DESC, k.keyword"""
            ).fetchall()
    return rows


def add_keyword(keyword: str, category_id: int,
                field: str = 'all', priority: int = 0, note: str = '') -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO keywords (keyword, category_id, field, priority, note) VALUES (?, ?, ?, ?, ?)",
            (keyword, category_id, field, priority, note or '')
        )
        return cur.lastrowid


def update_keyword(kw_id: int, keyword: str, category_id: int,
                   field: str = 'all', priority: int = 0, note: str = ''):
    with get_conn() as conn:
        conn.execute(
            "UPDATE keywords SET keyword=?, category_id=?, field=?, priority=?, note=? WHERE id=?",
            (keyword, category_id, field, priority, note or '', kw_id)
        )


def delete_keyword(kw_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM keywords WHERE id=?", (kw_id,))


# ─── Transactions ─────────────────────────────────────────────────────────────

def insert_transaction(
    date_posted: str, date_executed: str, description: str,
    message: str, payer_payee: str, account_number: str,
    ks: str, vs: str, ss: str,
    amount: float, balance: float, import_hash: str,
    category_id: Optional[int] = None,
    is_manual_category: bool = False
) -> bool:
    """Insert a transaction. Returns True if inserted, False if duplicate."""
    with get_conn() as conn:
        try:
            conn.execute(
                """INSERT INTO transactions
                   (date_posted, date_executed, description, message, payer_payee,
                    account_number, ks, vs, ss, amount, balance, import_hash,
                    category_id, is_manual_category)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (date_posted, date_executed, description, message, payer_payee,
                 account_number, ks, vs, ss, amount, balance, import_hash,
                 category_id, int(is_manual_category))
            )
            return True
        except sqlite3.IntegrityError:
            return False


def get_transactions(filters: Optional[Dict[str, Any]] = None) -> List[sqlite3.Row]:
    """
    filters keys:
      year: int | None
      month: int | None  (1-12)
      category_id: int | 0 (0 = uncategorized) | None (all)
      type: 'income' | 'expense' | 'all'
      search: str
      limit: int
      offset: int
      exclude_transfers: bool
    """
    if filters is None:
        filters = {}

    conditions = []
    params: List[Any] = []

    year = filters.get('year')
    month = filters.get('month')
    category_id = filters.get('category_id')
    tx_type = filters.get('type', 'all')
    search = filters.get('search', '').strip()
    limit = filters.get('limit', 500)
    offset = filters.get('offset', 0)
    exclude_transfers = filters.get('exclude_transfers', False)

    if year:
        conditions.append("strftime('%Y', t.date_posted) = ?")
        params.append(str(year))
    if month:
        conditions.append("strftime('%m', t.date_posted) = ?")
        params.append(f"{month:02d}")
    if category_id == 0:
        conditions.append("t.category_id IS NULL")
    elif category_id is not None:
        conditions.append("(t.category_id = ? OR c.parent_id = ?)")
        params.extend([category_id, category_id])
    if tx_type == 'income':
        conditions.append("t.amount > 0")
    elif tx_type == 'expense':
        conditions.append("t.amount < 0")
    if search:
        conditions.append(
            "(t.description LIKE ? OR t.message LIKE ? OR t.payer_payee LIKE ?)"
        )
        like = f"%{search}%"
        params.extend([like, like, like])
    if exclude_transfers:
        conditions.append("(c.is_transfer = 0 OR c.is_transfer IS NULL)")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT t.*,
               c.name as category_name,
               c.color as category_color,
               c.is_transfer as cat_is_transfer,
               c.is_income as cat_is_income,
               c.parent_id as cat_parent_id
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        {where}
        ORDER BY t.date_posted DESC, t.id DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return rows


def get_transaction_count(filters: Optional[Dict[str, Any]] = None) -> int:
    if filters is None:
        filters = {}

    conditions = []
    params: List[Any] = []

    year = filters.get('year')
    month = filters.get('month')
    category_id = filters.get('category_id')
    tx_type = filters.get('type', 'all')
    search = filters.get('search', '').strip()
    exclude_transfers = filters.get('exclude_transfers', False)

    if year:
        conditions.append("strftime('%Y', t.date_posted) = ?")
        params.append(str(year))
    if month:
        conditions.append("strftime('%m', t.date_posted) = ?")
        params.append(f"{month:02d}")
    if category_id == 0:
        conditions.append("t.category_id IS NULL")
    elif category_id is not None:
        conditions.append("(t.category_id = ? OR c.parent_id = ?)")
        params.extend([category_id, category_id])
    if tx_type == 'income':
        conditions.append("t.amount > 0")
    elif tx_type == 'expense':
        conditions.append("t.amount < 0")
    if search:
        conditions.append(
            "(t.description LIKE ? OR t.message LIKE ? OR t.payer_payee LIKE ?)"
        )
        like = f"%{search}%"
        params.extend([like, like, like])
    if exclude_transfers:
        conditions.append("(c.is_transfer = 0 OR c.is_transfer IS NULL)")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT COUNT(*)
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        {where}
    """

    with get_conn() as conn:
        return conn.execute(sql, params).fetchone()[0]


def update_transaction_category(tx_id: int, category_id: Optional[int],
                                 is_manual: bool = True):
    with get_conn() as conn:
        conn.execute(
            "UPDATE transactions SET category_id=?, is_manual_category=? WHERE id=?",
            (category_id, int(is_manual), tx_id)
        )


def get_uncategorized_count() -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE category_id IS NULL"
        ).fetchone()
    return row[0] if row else 0


def batch_categorize(assignments: List[Dict[str, Any]]):
    """assignments: list of {tx_id: int, category_id: int}"""
    with get_conn() as conn:
        for a in assignments:
            conn.execute(
                "UPDATE transactions SET category_id=?, is_manual_category=0 WHERE id=?",
                (a['category_id'], a['tx_id'])
            )


# ─── Analytics ───────────────────────────────────────────────────────────────

def get_category_totals(year: Optional[int] = None,
                        month: Optional[int] = None,
                        expense_only: bool = True,
                        exclude_transfers: bool = True) -> List[Dict]:
    """
    Returns list of {category_id, category_name, parent_id, color, total}
    Grouped by top-level category.
    """
    conditions = ["t.amount != 0"]
    params: List[Any] = []

    if year:
        conditions.append("strftime('%Y', t.date_posted) = ?")
        params.append(str(year))
    if month:
        conditions.append("strftime('%m', t.date_posted) = ?")
        params.append(f"{month:02d}")
    if expense_only:
        conditions.append("t.amount < 0")
    if exclude_transfers:
        conditions.append("(c.is_transfer = 0 OR c.is_transfer IS NULL)")
        conditions.append("(p.is_transfer = 0 OR p.is_transfer IS NULL)")

    where = "WHERE " + " AND ".join(conditions)

    sql = f"""
        SELECT
            COALESCE(p.id, c.id) as top_cat_id,
            COALESCE(p.name, c.name, 'Bez kategorie') as top_cat_name,
            COALESCE(p.color, c.color, '#888888') as color,
            SUM(t.amount) as total
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN categories p ON c.parent_id = p.id
        {where}
        GROUP BY top_cat_id
        ORDER BY total ASC
    """

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    result = []
    for r in rows:
        result.append({
            'category_id': r['top_cat_id'],
            'category_name': r['top_cat_name'],
            'color': r['color'],
            'total': r['total']
        })
    return result


def get_monthly_totals(year: Optional[int] = None,
                       exclude_transfers: bool = True) -> List[Dict]:
    """
    Returns monthly income/expense breakdown.
    [{month: 1, income: X, expense: Y}, ...]
    """
    conditions = []
    params: List[Any] = []

    if year:
        conditions.append("strftime('%Y', t.date_posted) = ?")
        params.append(str(year))
    if exclude_transfers:
        conditions.append("(c.is_transfer = 0 OR c.is_transfer IS NULL)")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT
            CAST(strftime('%m', t.date_posted) AS INTEGER) as month,
            SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END) as income,
            SUM(CASE WHEN t.amount < 0 THEN t.amount ELSE 0 END) as expense
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        {where}
        GROUP BY month
        ORDER BY month
    """

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [{'month': r['month'], 'income': r['income'] or 0.0,
             'expense': r['expense'] or 0.0} for r in rows]


def get_monthly_category_totals(year: Optional[int] = None,
                                 exclude_transfers: bool = True) -> List[Dict]:
    """Returns per-month, per-top-category expense totals for bar chart."""
    conditions = ["t.amount < 0"]
    params: List[Any] = []

    if year:
        conditions.append("strftime('%Y', t.date_posted) = ?")
        params.append(str(year))
    if exclude_transfers:
        conditions.append("(c.is_transfer = 0 OR c.is_transfer IS NULL)")
        conditions.append("(p.is_transfer = 0 OR p.is_transfer IS NULL)")

    where = "WHERE " + " AND ".join(conditions)

    sql = f"""
        SELECT
            CAST(strftime('%m', t.date_posted) AS INTEGER) as month,
            COALESCE(p.id, c.id) as top_cat_id,
            COALESCE(p.name, c.name, 'Bez kategorie') as top_cat_name,
            COALESCE(p.color, c.color, '#888888') as color,
            SUM(ABS(t.amount)) as total
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN categories p ON c.parent_id = p.id
        {where}
        GROUP BY month, top_cat_id
        ORDER BY month, total DESC
    """

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [{'month': r['month'], 'category_id': r['top_cat_id'],
             'category_name': r['top_cat_name'], 'color': r['color'],
             'total': r['total']} for r in rows]


def get_available_years() -> List[int]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT CAST(strftime('%Y', date_posted) AS INTEGER) as yr "
            "FROM transactions ORDER BY yr"
        ).fetchall()
    return [r['yr'] for r in rows if r['yr']]


def get_summary_stats(year: Optional[int] = None,
                      month: Optional[int] = None,
                      exclude_transfers: bool = True) -> Dict:
    """Returns total income, expense, balance for filters."""
    conditions = []
    params: List[Any] = []

    if year:
        conditions.append("strftime('%Y', t.date_posted) = ?")
        params.append(str(year))
    if month:
        conditions.append("strftime('%m', t.date_posted) = ?")
        params.append(f"{month:02d}")
    if exclude_transfers:
        conditions.append("(c.is_transfer = 0 OR c.is_transfer IS NULL)")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sql = f"""
        SELECT
            SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END) as income,
            SUM(CASE WHEN t.amount < 0 THEN t.amount ELSE 0 END) as expense
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        {where}
    """

    with get_conn() as conn:
        row = conn.execute(sql, params).fetchone()

    income = row['income'] or 0.0
    expense = row['expense'] or 0.0
    return {'income': income, 'expense': expense, 'balance': income + expense}
