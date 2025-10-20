import logging
from tabulate import tabulate
from decimal import Decimal, InvalidOperation
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

SQL_LIST_PRODUCTS = "" \
"SELECT p.product_id, p.sku, p.product_name AS name, COALESCE(c.category_name, '-') AS category_name, p.price, p.is_active " \
"FROM products p " \
"LEFT JOIN categories c ON c.category_id = p.category_id " \
"{where} " \
"ORDER BY p.product_id;"

SQL_GET_PRODUCT_BY_SKU = "" \
"SELECT product_id " \
"FROM products " \
"WHERE sku=%s;"

SQL_INSERT_PRODUCT = "" \
"INSERT INTO products (sku, product_name, category_id, price, is_active) " \
"VALUES (%s, %s, %s, %s, %s);"

SQL_FIND_CATEGORY_BY_NAME = "" \
"SELECT category_id " \
"FROM categories " \
"WHERE category_name=%s;"

SQL_INSERT_CATEGORY = "" \
"INSERT INTO categories (category_name) " \
"VALUES (%s);"

SQL_GET_PRODUCT_BY_ID = "" \
"SELECT p.product_id, p.sku, p.product_name AS name, COALESCE(c.category_name, '-') AS category_name, p.price, p.is_active " \
"FROM products p " \
"LEFT JOIN categories c ON c.category_id = p.category_id " \
"WHERE p.product_id=%s;"

SQL_GET_PRODUCT_DETAIL_BY_SKU = "" \
"SELECT p.product_id, p.sku, p.product_name, p.price, p.is_active, p.category_id, COALESCE(c.category_name, '-') AS category_name " \
"FROM products p " \
"LEFT JOIN categories c ON c.category_id = p.category_id " \
"WHERE p.sku=%s;"

SQL_UPDATE_PRODUCT = "" \
"UPDATE products " \
"SET sku=%s, product_name=%s, category_id=%s, price=%s, is_active=%s " \
"WHERE product_id=%s;"

SQL_DELETE_PRODUCT = "" \
"DELETE FROM products " \
"WHERE product_id=%s;"

HEADERS = {"product_id":"ID", "sku":"SKU", "product_name":"Name", "category_name":"Category", "price":"Price", "is_active":"Active"}

def list_products(conn, include_inactive: bool = False, q: str | None = None):
    where_clauses = []
    params = []

    if not include_inactive:
        where_clauses.append("p.is_active = 1")

    if q:
        like = f"%{q.strip()}%"
        where_clauses.append("(p.sku LIKE %s OR p.product_name LIKE %s OR c.category_name LIKE %s)")
        params.extend([like, like, like])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    sql = SQL_LIST_PRODUCTS.format(where=where_sql)

    logger.info("List products include_inactive=%s q=%s", include_inactive, q)
    with conn.cursor(dictionary=True) as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    if not rows:
        print("Tidak ada data product yang cocok.")
        return
    
    print(tabulate(rows, headers=HEADERS, tablefmt="grid", floatfmt=",.2f"))

def show_products(conn):
    logger.info("Show products invoked")
    list_products(conn, include_inactive=False, q=None)

    with conn.cursor(dictionary=True) as cur:
        cur.execute(SQL_LIST_PRODUCTS)
        rows = cur.fetchall()
    logger.debug("Fetched %d product rows", len(rows))
    if not rows:
        print("Belum ada produk.")
        return

    table = [
        [r["product_id"], r["sku"], r["name"], r["category_name"], r["price"], r["is_active"]]
        for r in rows
    ]
    headers = ["ID", "SKU", "Name", "Category", "Price", "Active"]
    print(tabulate(table, headers=headers, tablefmt="grid", floatfmt=",.2f"))

def _get_or_create_category(conn, category_name: str) -> Optional[int]:
    name = (category_name or "").strip()
    if not name:
        return None
    with conn.cursor() as cur:
        cur.execute(SQL_FIND_CATEGORY_BY_NAME, (name,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(SQL_INSERT_CATEGORY, (name,))
        return cur.lastrowid
    
def _product_exists(conn, sku: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(SQL_GET_PRODUCT_BY_SKU, (sku,))
        return cur.fetchone() is not None
    
def edit_product(conn):
    logger.info("Edit product invoked")
    print("\n===== EDIT PRODUK =====")
    sku = input("Masukkan SKU produk yang akan diubah: ").strip().upper()
    if not sku:
        print("SKU wajib diisi.")
        return
    
    with conn.cursor(dictionary=True) as cur:
        cur.execute(SQL_GET_PRODUCT_DETAIL_BY_SKU, (sku,))
        row = cur.fetchone()

    if not row:
        print("Produk tidak ditemukan.")
        return
    
    print("\nData saat ini:")
    print(tabulate(
        [row],
        headers={
            "product_id": "ID", "sku": "SKU", "product_name": "Name", 
            "category_name": "Category", "price": "Price", "is_active": "Active"
        }, tablefmt="grid", floatfmt=",.2f"
    ))

    new_sku = input(f"SKU baru [{row['sku']}]: ").strip().upper() or row["sku"]
    new_name = input(f"Nama baru [{row['product_name']}]: ").strip() or row["product_name"]
    cat_in = input(f"Kategori baru (kosong = tidak berubah) [{row['category_name']}]: ").strip()
    price_in = input(f"Harga baru [{row['price']}]: ").strip()
    act_in = input(f"Aktif? (Y/n) [{'Y' if row['is_active'] else 'n'}]: ").strip().lower()

    if new_sku != row["sku"] and _product_exists(conn, new_sku):
        print("Gagal: SKU baru sudah digunakan produk lain.")
        return
    
    if price_in:
        try:
            new_price = Decimal(price_in)
            if new_price < 0:
                raise InvalidOperation
        except InvalidOperation:
            print("Harga tidak valid.")
            return
    else:
        new_price = Decimal(row["price"])

    if cat_in == "":
        new_cat_id = row["category_id"]
    else:
        new_cat_id = _get_or_create_category(conn, cat_in)

    new_active = 0 if act_in == "n" else 1

    try:
        with conn.cursor() as cur:
            cur.execute(
                SQL_UPDATE_PRODUCT,
                (new_sku, new_name, new_cat_id, new_price, new_active, row["product_id"])
            )
        conn.commit()
        logger.info("Product updated id=%s sku=%s", row["product_id"], new_sku)
        print("Product berhasil diperbarui.")
    except Exception as e:
        conn.rollback()
        logger.exception("Update failed product_id=%s", row["product_id"])
        print(f"Gagal update: {e}")

def toggle_product_active(conn):
    logger.info("Toggle product invoked")
    print("\n===== AKTIF/NONAKTIF PRODUK =====")
    sku = input("Masukkan SKU: ").strip().upper()
    if not sku:
        print("SKU wajib diisi.")
        return
    
    with conn.cursor(dictionary=True) as cur:
        cur.execute(SQL_GET_PRODUCT_DETAIL_BY_SKU, (sku,))
        row = cur.fetchone()

    if not row:
        print("Produk tidak ditemukan.")
        return
    
    new_active = 0 if row["is_active"] else 1
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE products SET is_active=%s WHERE product_id=%s",
            (new_active, row["product_id"])
        )
    conn.commit()
    logger.info("Product %s now %s", row["sku"], "active" if new_active else "inactive")
    status = "aktif" if new_active else "nonaktif"
    print(f"Produk {row['sku']} sekarang {status}.")

def delete_product(conn):
    logger.info("Delete product invoked")
    print("\n===== HAPUS PRODUK =====")
    sku = input("Masukkan SKU yang akan dihapus: ").strip().upper()
    if not sku:
        print("SKU wajib diisi.")
        return
    
    with conn.cursor(dictionary=True) as cur:
        cur.execute(SQL_GET_PRODUCT_DETAIL_BY_SKU, (sku,))
        row = cur.fetchone()

    if not row:
        print("Produk tidak ditemukan.")
        return
    
    print("\nTarget dihapus:")
    print(tabulate([row], headers={
        "product_id": "ID", "sku": "SKU", "product_name": "Name",
        "category_name": "Category", "price": "Price", "is_active": "Active"
    }, tablefmt="grid", floatfmt=",.2f"))

    yn = input("Yakin hapus? ketik 'hapus' untuk konfirmasi: ").strip().lower()
    if yn != "hapus":
        print("Dibatalkan.")
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute(SQL_DELETE_PRODUCT, (row["product_id"],))
        conn.commit()
        logger.info("Product deleted id=%s sku=%s", row["product_id"], row["sku"])
        print("Produk berhasil dihapus.")
    except Exception as e:
        conn.rollback()
        logger.exception("Delete failed product_id=%s; maybe foreign key", row["product_id"])
        print(f"Gagal hapus (kemungkinan terkain foreign key). "
              f"Pertimbangkan nonaktifkan saja. Detail: {e}")
    
def add_product(conn):
    logger.info("Add produk invoked")
    print("\n===== TAMBAH PRODUK =====")
    sku = input("SKU (unik): ").strip().upper()
    name = input("Nama produk: ").strip()
    price_str = input("Harga (contoh 12.50): ").strip()
    cat_name = input("Kategori (Kosongkan jika tidak ada): ").strip()
    active_in = input("Aktif? [Y/n]: ").strip().lower()

    if not sku or not name:
        print("SKU dan Nama produk wajib diisi.")
        return
    
    if _product_exists(conn, sku):
        print("Gagal: SKU sudah terdaftar.")
        return
    
    try:
        price = Decimal(price_str)
        if price < 0:
            raise InvalidOperation
    except InvalidOperation:
        logger.warning("Invalid price input: %s", price_str)
        print("Harga tidak valid.")
        return
    
    is_active = 0 if active_in == "n" else 1
    category_id = _get_or_create_category(conn, cat_name)

    with conn.cursor() as cur:
        cur.execute(SQL_INSERT_PRODUCT, (sku, name, category_id, price, is_active))
        new_id = cur.lastrowid
    conn.commit()
    logger.info("Product created sku=%s id=%s price=%s category_id=%s", sku, new_id, price, category_id)

    with conn.cursor(dictionary=True) as cur:
        cur.execute(SQL_GET_PRODUCT_BY_ID, (new_id,))
        row = cur.fetchone()

    print("\nProduk berhasil ditambahkan:")
    print(tabulate(
        [row],
        headers={
            "product_id": "ID", "sku": "SKU", "name": "Name", 
            "category_name": "Category", "price": "Price", "is_active": "Active"
        },
        tablefmt="grid", floatfmt=",.2f"
    ))

def products_menu(conn):
    while True:
        print("\n===== MENU PRODUK =====")
        print("1) Daftar produk (aktif saja)")
        print("2) Daftar produk (termasuk nonaktif)")
        print("3) Cari produk")
        print("4) Tambah produk")
        print("5) Edit produk")
        print("6) Aktif/Nonaktifkan produk")
        print("7) Hapus produk")
        print("0) Kembali")
        c = input("Pilih: ").strip()

        if c == "1":
            list_products(conn, include_inactive=False)
        elif c == "2":
            list_products(conn, include_inactive=True)
        elif c == "3":
            q = input("Kata kunci (SKU/Nama/Kategori): ").strip()
            list_products(conn, include_inactive=True, q=q)
        elif c == "4":
            add_product(conn)
        elif c == "5":
            edit_product(conn)
        elif c == "6":
            toggle_product_active(conn)
        elif c == "7":
            delete_product(conn)
        elif c == "0":
            break
        else:
            print("Pilihan tidak valid.")