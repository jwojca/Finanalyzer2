"""
mBank CSV parser for FinAnalazer2.
"""
import csv
import hashlib
from pathlib import Path
from typing import List, Dict, Any


def _parse_amount(value: str) -> float:
    """Parse mBank amount format: '1 234,56' -> 1234.56"""
    cleaned = value.strip().replace('\xa0', '').replace(' ', '').replace(',', '.')
    if not cleaned or cleaned in ('', '-'):
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_date(value: str) -> str:
    """Parse DD-MM-YYYY -> YYYY-MM-DD"""
    value = value.strip()
    if not value:
        return ''
    parts = value.split('-')
    if len(parts) == 3:
        day, month, year = parts
        return f"{year}-{month}-{day}"
    return value


def _clean_str(value: str) -> str:
    """Strip whitespace and surrounding quotes from string fields."""
    v = value.strip()
    if len(v) >= 2 and v[0] in ('"', "'") and v[-1] in ('"', "'"):
        v = v[1:-1]
    return v.strip()


def _detect_format(header_row: list) -> str:
    """
    Detect mBank CSV format from the header row.
    Returns 'credit_card' or 'standard'.
    """
    joined = ';'.join(header_row).lower()
    if 'kart' in joined or 'transakce' in joined:
        return 'credit_card'
    return 'standard'


def _build_transaction(row: list, fmt: str) -> Dict[str, Any]:
    if fmt == 'credit_card':
        # Columns: date_posted, date_executed, description, message,
        #          payer_payee, account_number, ks, vs, ss, card_number, amount
        date_posted = _parse_date(row[0])
        date_executed = _parse_date(row[1])
        description = _clean_str(row[2])
        message = _clean_str(row[3])
        payer_payee = _clean_str(row[4])
        account_number = _clean_str(row[5])
        ks = _clean_str(row[6])
        vs = _clean_str(row[7])
        ss = _clean_str(row[8])
        amount = _parse_amount(row[10])
        balance = 0.0
    else:
        # Standard format: date_posted, date_executed, description, message,
        #                  payer_payee, account_number, ks, vs, ss, amount, balance
        date_posted = _parse_date(row[0])
        date_executed = _parse_date(row[1])
        description = _clean_str(row[2])
        message = _clean_str(row[3])
        payer_payee = _clean_str(row[4])
        account_number = _clean_str(row[5])
        ks = _clean_str(row[6])
        vs = _clean_str(row[7])
        ss = _clean_str(row[8])
        amount = _parse_amount(row[9])
        balance = _parse_amount(row[10])

    hash_source = f"{date_posted}{description}{amount:.2f}{balance:.2f}"
    import_hash = hashlib.md5(hash_source.encode('utf-8')).hexdigest()

    return {
        'date_posted': date_posted,
        'date_executed': date_executed,
        'description': description,
        'message': message,
        'payer_payee': payer_payee,
        'account_number': account_number,
        'ks': ks,
        'vs': vs,
        'ss': ss,
        'amount': amount,
        'balance': balance,
        'import_hash': import_hash,
    }


def parse_mbank_csv(filepath: str) -> List[Dict[str, Any]]:
    """
    Parse an mBank CSV file (standard or credit card format).
    Returns a list of transaction dicts.
    """
    filepath = Path(filepath)
    transactions = []
    fmt = 'standard'

    with open(filepath, encoding='cp1250', newline='') as f:
        reader = csv.reader(f, delimiter=';')
        header_found = False
        for row in reader:
            if not row:
                continue
            if row[0].startswith('#'):
                fmt = _detect_format(row)
                header_found = True
                continue
            if not header_found:
                continue
            min_cols = 11 if fmt == 'credit_card' else 11
            if len(row) < min_cols:
                continue
            transactions.append(_build_transaction(row, fmt))

    return transactions
