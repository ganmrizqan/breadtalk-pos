from db.connection import get_conn
from services.products import show_products, add_product, edit_product, toggle_product_active, delete_product
from services.transactions import create_transaction
from services.reports import report_daily, report_by_product, report_by_cashier

def main():
    print("Breadtalk POS - CLI (MySQL)")
    try:
        conn = get_conn()
    except Exception as e:
        print("Gagal Konek ke DB:", e)
        return
    
    try:
        while True:
            print("===== MENU: =====")
            print("1) Lihat produk")
            print("2) Buat transaksi baru")
            print("3) Laporan harian")
            print("4) Laporan per-produk")
            print("5) Laporan per-kasir harian")
            print("6) Tambah produk")
            print("7) Edit produk")
            print("8) Aktif/Nonaktifkan produk")
            print("9) Hapus produk")
            print("0) Keluar")
            choice = input("Pilih: ").strip()

            if choice == "1":
                show_products(conn)
            elif choice == "2":
                create_transaction(conn)
            elif choice == "3":
                report_daily(conn)
            elif choice == "4":
                report_by_product(conn)
            elif choice == "5":
                report_by_cashier(conn)
            elif choice == "6":
                add_product(conn)
            elif choice == "7":
                edit_product(conn)
            elif choice == "8":
                toggle_product_active(conn)
            elif choice == "9":
                delete_product(conn)
            elif choice == "0":
                break
            else:
                print("Pilihan tidak dikenal.")
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()