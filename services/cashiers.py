import logging
from tabulate import tabulate

logger = logging.getLogger(__name__)

SQL_LIST_CASHIERS_BASE = "" \
"SELECT cashier_id, code, employee_code, full_name, is_active " \
"FROM cashiers " \
"{where} " \
"ORDER BY cashier_id"

SQL_GET_BY_CODE = "" \
"SELECT cashier_id, code, employee_code, full_name, is_active " \
"FROM cashiers " \
"WHERE employee_code=%s"

SQL_CHECK_CODE_EXISTS = "" \
"SELECT 1 " \
"FROM cashiers " \
"WHERE code=%s"

SQL_INSERT = "" \
"INSERT INTO cashiers (code, employee_code, full_name, is_active) " \
"VALUES (%s, %s, %s, %s)"

SQL_UPDATE = "" \
"UPDATE cashiers " \
"SET code=%s, employee_code, full_name=%s, is_active=%s " \
"WHERE cashier_id=%s"

SQL_DELETE = "" \
"DELETE FROM cashiers " \
"WHERE cashier_id=%s"

HEADERS = {"cashier_id":"ID", "code":"Code", "employee_code":"EmpCode", "full_name":"Name", "is_active":"Active"}

def _generate_cashier_code(conn) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(cashier_id), 0) + 1 FROM cashiers")
        next_id = int(cur.fetchone()[0])
    return f"CSH-{next_id:03d}"

def list_cashiers(conn, include_inactive=False):
    where = "" if include_inactive else "WHERE is_active=1"
    with conn.cursor(dictionary=True) as cur:
        cur.execute(SQL_LIST_CASHIERS_BASE.format(where=where))
        rows = cur.fetchall()
    if not rows:
        print("Belum ada kasir.")
        return
    print(tabulate(rows, headers=HEADERS, tablefmt="grid"))

def add_cashier(conn):
    print("\n===== TAMBAH KASIR =====")
    code = input("Kode kasir (unik, kosongkan untuk auto): ").strip().upper()
    emp = input("Employee code (opsional): ").strip()
    name = input("Nama lengkap: ").strip()
    active = 0 if input("Aktif? [Y/n]: ").strip().lower() == "n" else 1
    
    if not name:
        print("Nama wajib diisi."); return
    
    if not code:
        code = _generate_cashier_code(conn)
        
    with conn.cursor() as cur:
        cur.execute(SQL_CHECK_CODE_EXISTS, (code,))
        if cur.fetchone():
            print("Gagal: kode kasir sudah dipakai."); return
        cur.execute(SQL_INSERT, (code, (emp or None), name, active))
    conn.commit()
    logger.info("Cashier created id=%s code=%s", code, name)
    print(f"Kasir ditambahkan dengan kode: {code}")

    with conn.cursor(dictionary=True)as cur:
        cur.execute(SQL_GET_BY_CODE, (code,))
        row = cur.fetchone()
    print("\nKasir ditambahkan:")
    print(tabulate([row], headers=HEADERS, tablefmt="grid"))

def edit_cashier(conn):
    print("\n===== EDIT KASIR =====")
    code = input("Masukkan KODE kasir yang akan diubah: ").strip().upper()
    if not code: print("Kode wajib diisi."); return

    with conn.curosr(dictionary=True) as cur:
        cur.execute(SQL_GET_BY_CODE, (code,))
        row = cur.fetchone()
    if not row:
        print("Kasir tidak ditemukan."); return
    
    print("\nData saat ini:")
    print(tabulate([row], headers=HEADERS, tablefmt="grid"))

    new_code = input(f"Kode baru [{row['code']}]: ").strip().upper() or row["code"]
    new_emp = input(f"Employee kode baru [{row.get('employee_code') or ''}]: ").strip() or row.get("employee_code")
    new_name = input(f"Nama baru [{row['full_name']}]: ").strip() or row["full_name"]
    act_in = input(f"Aktif? (Y/n) [{'Y' if row['is_active'] else 'n'}]: ").strip().lower()
    new_active = 0 if act_in == "n" else 1

    if new_code != row["code"]:
        with conn.cursor() as cur:
            cur.execute(SQL_CHECK_CODE_EXISTS, (new_code,))
            if cur.fetchone():
                print("Gagal: kode kasir baru sudah dipakai."); return
            
    with conn.cursor() as cur:
        cur.execute(SQL_UPDATE, (new_code, (new_emp or None), new_name, new_active, row["cashier_id"]))
    conn.commit()
    logger.info("Cashier updated id=%s code=%s", row["cashier_id"], new_code)
    print("Kasir diperbarui.")

def toggle_cashier_active(conn):
    print("\n===== AKTIF/NONAKTIF KASIR =====")
    code = input("Masukkan KODE kasir: ").strip().upper()
    if not code: print("Kode wajib diisi."); return

    with conn.cursor(dictionary=True) as cur:
        cur.execute(SQL_GET_BY_CODE, (code,))
        row = cur.fetchone()
    if not row: print("Kasir tidak ditemukan."); return

    new_active = 0 if row["is_active"] else 1
    with conn.cursor() as cur:
        cur.execute("UPDATE cashiers SET is_active=%s WHERE cashier_id=%s", (new_active, row["cashier_id"]))
    conn.commit()
    logger.info("Cashier %s now %s", row["code"], "active" if new_active else "inactive")
    print(f"Kasir {row['code']} sekarang {'aktif' if new_active else 'nonaktif'}.")

def delete_cashier(conn):
    print("\n===== HAPUS KASIR =====")
    code = input("Masukkan KODE kasir: ").strip().upper()
    if not code: print("Kode wajib diisi."); return

    with conn.cursor(dictionary=True) as cur:
        cur.execute(SQL_GET_BY_CODE, (code,))
        row = cur.fetcone()
    if not row: print("Kasir tidak ditemukan."); return

    print(tabulate([row], headers=HEADERS, tablefmt="grid"))
    if input("Ketik 'hapus' unutk konfirmasi: ").strip().lower() != "hapus":
        print("Dibatalkan."); return
    
    import mysql.connector
    try:
        with conn.cursor() as cur:
            cur.execute(SQL_DELETE, (row["cashier_id"],))
        conn.commit()
        logger.info("Cashier deleted id=%s code=%s", row["cashier_id"], row["code"])
        print("Kasir dihapus.")
    except mysql.connector.Error as err:
        if getattr(err, "errno", None) == 1451:
            print("Gagal hapus: kasir sudah dipakai di transaksi. Nonaktifkan saja.")
        else:
            print(f"Gagal hapus: {err}")

def cashiers_menu(conn):
    while True:
        print("\n===== MENU KASIR =====")
        print("1) Daftar kasir (aktif saja)")
        print("2) Daftar kasir (termasuk nonaktif)")
        print("3) Tambah kasir")
        print("4) Edit kasir")
        print("5) Aktif/Nonaktifkan kasir")
        print("6) Hapus kasir")
        print("0) Kembali")
        c = input("Pilih: ").strip()
        if c == "1": list_cashiers(conn, include_inactive=False)
        elif c == "2": list_cashiers(conn, include_inactive=True)
        elif c == "3": add_cashier(conn)
        elif c == "4": edit_cashier(conn)
        elif c == "5": toggle_cashier_active(conn)
        elif c == "6": delete_cashier(conn)
        elif c == "0": break
        else: print("Pilihan tidak valid.")