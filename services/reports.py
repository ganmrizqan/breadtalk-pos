import logging
from tabulate import tabulate

logger = logging.getLogger(__name__)

SQL_DAILY_SUMMARY = "" \
"SELECT DATE(txn_datetime) AS d, COUNT(*) AS trx, SUM(total_amount) AS revenue " \
"FROM transactions " \
"GROUP BY DATE(txn_datetime) " \
"ORDER BY d DESC;"

SQL_VIEW_SALES_BY_PRODUCT = "" \
"SELECT * FROM v_sales_by_product " \
"ORDER BY revenue DESC;"

SQL_VIEW_SALES_BY_CASHIER = "" \
"SELECT * FROM v_sales_by_cashier_daily " \
"ORDER BY sale_date DESC, total_sales DESC;"

def report_daily(conn, date_str=None):
    logger.info("Report daily invoked date=%s", date_str)
    print("===== LAPORAN HARIAN =====")
    with conn.cursor() as cur:
        cur.execute(SQL_DAILY_SUMMARY)
        rows = cur.fetchall()
    logger.debug("Daily report rows=%d", len(rows))
    print(tabulate(rows, headers=["Date", "Transactions", "Revenue"], tablefmt="grid", floatfmt=",.2f"))

def report_by_product(conn, date_str=None):
    logger.info("Report per-product invoked date=%s", date_str)
    print("===== LAPORAN PER-PRODUK =====")
    with conn.cursor() as cur:
        cur.execute(SQL_VIEW_SALES_BY_PRODUCT)
        rows = cur.fetchall()
    print(tabulate(rows, headers=["Product ID", "Product Name", "Qty Sold", "Revenue"], tablefmt="grid", floatfmt=",.2f"))

def report_by_cashier(conn, date_str=None):
    logger.info("Report per-cashier invoked date=%s", date_str)
    print("===== LAPORAN PER_KASIR HARIAN =====")
    with conn.cursor()as cur:
        cur.execute(SQL_VIEW_SALES_BY_CASHIER)
        rows = cur.fetchall()
    print(tabulate(rows, headers=["Sale Date", "Cashier ID", "Full Name", "Total Sales"], tablefmt="grid", floatfmt=",.2f"))