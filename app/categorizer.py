"""
Auto-categorizer for FinAnalazer2.
Matches transactions against keyword rules.
"""
from typing import Optional, List, Dict, Any
from app import database as db

# Type alias – actual sqlite3.Row used at runtime
sqlite3_Row_compat = Any


def categorize_transaction(tx: Dict[str, Any],
                           keywords: List[sqlite3_Row_compat]) -> Optional[int]:
    """
    Match a transaction dict against a list of keyword rows.
    Returns category_id or None.
    Keyword rows must have: keyword, category_id, field, priority.
    Higher priority wins; among equal priority, longer keyword wins.
    """
    best_cat = None
    best_priority = -999
    best_len = 0

    description = (tx.get('description') or '').upper()
    message = (tx.get('message') or '').upper()
    payer_payee = (tx.get('payer_payee') or '').upper()

    for kw in keywords:
        kw_text = kw['keyword'].upper()
        field = kw['field'] or 'all'
        priority = kw['priority'] or 0

        matched = False
        if field == 'all':
            matched = (kw_text in description or
                       kw_text in message or
                       kw_text in payer_payee)
        elif field == 'description':
            matched = kw_text in description
        elif field == 'message':
            matched = kw_text in message
        elif field in ('payer_payee', 'payer'):
            matched = kw_text in payer_payee

        if matched:
            kw_len = len(kw_text)
            if (priority > best_priority or
                    (priority == best_priority and kw_len > best_len)):
                best_priority = priority
                best_len = kw_len
                best_cat = kw['category_id']

    return best_cat


def categorize_all_uncategorized() -> int:
    """
    Fetch all keywords, then all uncategorized transactions,
    assign categories. Returns number of categorized transactions.
    """
    keywords = db.get_keywords()
    if not keywords:
        return 0

    # Get uncategorized transactions (no category_id)
    txs = db.get_transactions({'category_id': 0, 'limit': 999999, 'offset': 0})
    if not txs:
        return 0

    assignments = []
    for tx in txs:
        tx_dict = {
            'description': tx['description'],
            'message': tx['message'],
            'payer_payee': tx['payer_payee'],
        }
        cat_id = categorize_transaction(tx_dict, keywords)
        if cat_id is not None:
            assignments.append({'tx_id': tx['id'], 'category_id': cat_id})

    if assignments:
        db.batch_categorize(assignments)

    return len(assignments)


def recategorize_all(auto_only: bool = True) -> int:
    """
    Recategorize all transactions (or only non-manual ones).
    Returns number of transactions updated.
    """
    keywords = db.get_keywords()
    if not keywords:
        return 0

    filters: Dict[str, Any] = {'limit': 999999, 'offset': 0}
    all_txs = db.get_transactions(filters)

    assignments = []
    for tx in all_txs:
        if auto_only and tx['is_manual_category']:
            continue

        tx_dict = {
            'description': tx['description'],
            'message': tx['message'],
            'payer_payee': tx['payer_payee'],
        }
        cat_id = categorize_transaction(tx_dict, keywords)
        if cat_id is not None:
            assignments.append({'tx_id': tx['id'], 'category_id': cat_id})
        elif not auto_only:
            # Reset to uncategorized
            assignments.append({'tx_id': tx['id'], 'category_id': None})

    if assignments:
        db.batch_categorize(assignments)

    return len(assignments)
