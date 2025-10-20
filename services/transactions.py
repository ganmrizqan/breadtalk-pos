import logging
import datetime as dt
from decimal import Decimal
from typing import List, Tuple, Optional
from tabulate import tabulate
from utils.helpers import input_nonempty, input_decimal, input_int
from utils.logging_tools import log_exceptions

logger = logging.getLogger(__name__)

SQL_LIST_CASHIER = "" \
"SELECT cashier_id, employee_code, full_name " \
"FROM cashiers " \
"ORDER BY cashier_id;"

SQL_LIST_PAYMENT_METHOD = "" \
"SELECT payment_method_id, method_code, method_name " \
"FROM payment_methods " \
"ORDER BY payment_method_id;"

SQL_GET_PRODUCT_BY_SKU = "" \
"SELECT product_id, product_name, price " \
"FROM products " \
"WHERE sku = %s AND is_active = 1;"

SQL_INSERT_TX_HEADER = "" \
"INSERT INTO transactions (receipt_no, store_id, cashier_id, txn_datetime, subtotal, discount_amount, tax_amount, total_amount, customer_note, payment_method_id) " \
"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"

SQL_INSERT_TX_ITEM = "" \
"INSERT INTO transaction_items (transaction_id, product_id, quantity, unit_price, line_discount, line_total) " \
"VALUES (%s, %s, %s, %s, %s, %s);"

SQL_INSERT_PAYMENT = "" \
"INSERT INTO payments (transaction_id, payment_method_id, amount, referencee) " \
"VALUES (%s, %s, %s, %s);"

SQL_GET_LAST_INSERT_ID = "SELECT LAST_INSERT_ID();"

def show_cashiers(conn):
    with conn.cursor() as cur:
        cur.execute(SQL_LIST_CASHIER)
        rows = cur.fetchall()
    print(tabulate(rows, headers=["ID", "Code", "Name"], tablefmt="grid"))

def show_payment_methods(conn):
    with conn.cursor() as cur:
        cur.execute(SQL_LIST_PAYMENT_METHOD)
        rows = cur.fetchall()
    print(tabulate(rows, headers=["ID", "Code", "Name"], tablefmt="grid"))

def generate_receipt_no(store_code: str = "BT01") -> str:
    now = dt.datetime.now()
    return f"{store_code}-{now:%Y%m%d-%H%M%S}"

def fetch_product_by_sku(conn, sku: str):
    with conn.cursor() as cur:
        cur.execute(SQL_GET_PRODUCT_BY_SKU, (sku,))
        return cur.fetchone()

@log_exceptions("Create transaction error")
def create_transaction(conn):
    logger.info("Create transaction started")
    print("=== Buat Transaksi Baru ===")
    show_cashiers(conn)
    cashier_id = input_int("Pilih cashier ID: ", min_value=1)
    store_id = 1

    items: List[Tuple[int, Decimal, Decimal, Decimal]] = []

    while True:
        sku = input_nonempty("Masukkan SKU (atau 'done' untuk selesai): ")
        if sku.lower() == "done":
            break
        prod = fetch_product_by_sku(conn, sku)
        if not prod:
            print("SKU tidak ditemukan atau tidak aktif.")
            continue
        product_id, product_name, unit_price = prod
        print(f"{product_name} @ {unit_price}")
        qty = input_decimal("QTY: ", min_value=Decimal("0.001"))
        disc = input_decimal("Diskon baris (RP, 0 kalau tidak ada): ", min_value=Decimal("0"))
        items.append((product_id, qty, Decimal(str(unit_price)), disc))

    if not items:
        print("Tidak ada item. Transaksi dibatalkan.")
        return
    
    note: Optional[str] = input("Catatan pelanggan (Opsional): ").strip() or None

    subtotal = Decimal("0")
    for _, qty, unit_price, disc in items:
        line_total = (qty * unit_price) - disc
        if line_total < 0:
            line_total = Decimal("0")
        subtotal += line_total

    tax = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
    discount_header = Decimal("0.00")
    total = subtotal - discount_header + tax
    logger.debug("Tx computed subtotal=%s discount=%s tax=%s total=%s items=%d",
                 subtotal, discount_header, tax, total, len(items))

    show_payment_methods(conn)
    pay_method_id = input_int("Pilih payment method ID: ", min_value=1)
    pay_amount = total
    pay_ref = input("Reference (Kartu/QR/Nota): ").strip() or None

    receipt_no = generate_receipt_no()
    now = dt.datetime.now()

    try:
        with conn.cursor() as cur:
            cur.execute(
                SQL_INSERT_TX_HEADER, 
                (
                    receipt_no,
                    store_id,
                    cashier_id,
                    now,
                    subtotal,
                    discount_header,
                    tax,
                    total,
                    note,
                    pay_method_id,
                ),
            )
            cur.execute(SQL_GET_LAST_INSERT_ID)
            tx_id = cur.fetchone()[0]

            for (product_id, qty, unit_price, disc) in items:
                line_total = (qty * unit_price) - disc
                if line_total < 0:
                    line_total = Decimal("0")
                cur.execute(
                    SQL_INSERT_TX_ITEM,
                    (
                        tx_id,
                        product_id,
                        qty,
                        unit_price,
                        disc,
                        line_total,
                    ),
                )
            
            cur.execute(
                SQL_INSERT_PAYMENT,
                (
                    tx_id,
                    pay_method_id,
                    pay_amount,
                    pay_ref,
                ),
            )
        conn.commit()
        logger.info("Transaction commited tx_id=%s total=%s items=%s", tx_id, total, len(items))
        print("Transaksi berhasil disimpan.")
        print(f"Receipt No: {receipt_no}")
        print(f"Subtotal: {subtotal}")
        print(f"Tax (10%): {tax}")
        print(f"Total: {total}")
    
    except Exception as e:
        conn.rollback()
        logger.exception("Transaction failed; rolling back")
        print("Gagal menyimpan transaksi:", e)