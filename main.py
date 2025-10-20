import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from db.connection import get_conn
from services.products import show_products, add_product, edit_product, toggle_product_active, delete_product, products_menu
from services.transactions import create_transaction
from services.reports import report_daily, report_by_product, report_by_cashier
from services.cashiers import cashiers_menu

class SecretsFilter(logging.Filter):
    # Masking sederhana buar cegah kebocoran kata sandi di log.
    def filter(self, record):
        secrets = [os.getenv(k) for k in ("DB_PASS", "PASSWORD", "SECRET", "API_KEY", "TOKEN") if os.getenv(k)]
        
        # Mask msg "mentah"
        if isinstance(record.msg, str):
            for s in secrets:
                record.msg = record.msg.replace(s, "******")

        # Mask di args juga kalau string
        if record.args:
            new_args = []
            for a in (record.args if isinstance(record.args, tuple) else (record.args,)):
                if isinstance(a, str):
                    for s in secrets:
                        a = a.replace(s, "******")
                new_args.append(a)
            record.args = tuple(new_args)
        return True
    
def _mk_handler(path: str, level: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = TimedRotatingFileHandler(
        filename=path,
        when="midnight",
        # backupCount=14,
        backupCount=int(os.getenv("LOG_BACKUP_DAYS", "14")),
        encoding="utf-8"
    )
    handler.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)
    handler.addFilter(SecretsFilter())
    return handler

def configure_logging():
    log_dir = os.getenv("LOG_DIR", "logs")
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Root logger + console
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    console.addFilter(SecretsFilter())
    root.addHandler(console)

    # Satu file umum
    root.addHandler(_mk_handler(os.path.join(log_dir, "app.log"), level))

    # File per-modul (map: logger_name -> filename)
    module_files = {
        "db.connection": os.path.join(log_dir, "db.log"),
        "services.products": os.path.join(log_dir, "products.log"),
        "services.transactions": os.path.join(log_dir, "transactions.log"),
        "services.reports": os.path.join(log_dir, "reports.log"),
        "services.cashiers": os.path.join(log_dir, "cashiers.log"),
    }

    for logger_name, filepath in module_files.items():
        lg = logging.getLogger(logger_name)
        # Penting: biarkan propagate=True agar tetap tampil di console & app.log
        lg.propagate = True
        # Hindari double handler kalau configure_logging dipanggil ulang
        if not any(isinstance(h, TimedRotatingFileHandler) and getattr(h, 'baseFilename', None) and os.path.basename(h.baseFilename) == os.path.basename(filepath) for h in lg.handlers):
            lg.addHandler(_mk_handler(filepath, level))

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
            print("1) Buat transaksi baru")
            print("2) Laporan harian")
            print("3) Laporan per-produk")
            print("4) Laporan per-kasir harian")
            print("5) Kelola produk")
            print("6) Kelola kasir")
            print("0) Keluar")
            choice = input("Pilih: ").strip()

            if choice == "1":
                create_transaction(conn)
            elif choice == "2":
                report_daily(conn)
            elif choice == "3":
                report_by_product(conn)
            elif choice == "4":
                report_by_cashier(conn)
            elif choice == "5":
                products_menu(conn)
            elif choice == "6":
                cashiers_menu(conn)
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
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("=====Breadtalk POS Started")
    try:
        main()
    except Exception:
        logging.getLogger(__name__).exception("Unhandled Exception")
        sys.exit(1)