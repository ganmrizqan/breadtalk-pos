[README.md](https://github.com/user-attachments/files/22187482/README.md)
# Breadtalk POS – CLI (MySQL)

CLI sederhana untuk mengelola produk, transaksi, dan laporan ala kasir (mirip struk BreadTalk). Dibuat dengan Python + MySQL. Cocok untuk belajar dan dipakai internal skala kecil.

> English blurb: A lightweight Python + MySQL CLI POS to manage products, create transactions, and print quick reports (daily / per‑product / per‑cashier).

---

## ✨ Fitur
- **Produk**: lihat daftar, tambah, edit, aktif/nonaktif, hapus
- **Transaksi**: buat transaksi baru, pilih kasir & metode pembayaran
- **Laporan**: harian, per‑produk, per‑kasir harian
- **Tampilan tabel rapi** dengan `tabulate` (format `github`)
- **Konfigurasi via `.env`**, koneksi MySQL lewat `mysql-connector-python`

---

## 📦 Prasyarat
- Python 3.10+
- MySQL 8+ (atau kompatibel)
- Git (opsional, untuk versioning)

---

## 🚀 Quickstart

### 1) Clone & masuk folder
```bash
git clone https://github.com/<username>/breadtalk-pos.git
cd breadtalk-pos
```

### 2) Buat & aktifkan virtual env
**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
> Jika muncul error *“running scripts is disabled”*, jalankan:  
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` lalu buka ulang terminal.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

### 4) Salin & isi variabel lingkungan
```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```
Isi `.env`:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASS=your_password
DB_NAME=breadtalk_pos
```

### 5) Jalankan aplikasi
```bash
python main.py
```

---

## 🗂️ Struktur Proyek
```
breadtalk-pos/
├─ main.py
├─ services/
│  ├─ products.py          # Lihat + CRUD produk
│  ├─ transactions.py      # Buat transaksi baru
│  ├─ reports.py           # Laporan harian/per‑produk/per‑kasir
│  └─ __init__.py
├─ db/
│  ├─ connection.py        # Koneksi MySQL + dotenv
│  └─ __init__.py
├─ requirements.txt
├─ .env.example
└─ README.md
```

---

## 🧰 Dependensi Utama
- `mysql-connector-python`
- `python-dotenv`
- `tabulate`

Tambahkan lib lain sesuai kebutuhan (mis. `pyinstaller` untuk build exe).

---

## 🛢️ Contoh Skema Database (minimal)
> **Catatan:** Sesuaikan dengan kebutuhan. Ini contoh ringkas yang kompatibel dengan kode.

```sql
CREATE TABLE categories (
  category_id   INT AUTO_INCREMENT PRIMARY KEY,
  category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE products (
  product_id    INT AUTO_INCREMENT PRIMARY KEY,
  sku           VARCHAR(32) NOT NULL UNIQUE,
  product_name  VARCHAR(200) NOT NULL,
  category_id   INT NULL,
  price         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  is_active     TINYINT(1) NOT NULL DEFAULT 1,
  FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE cashiers (
  cashier_id INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(100) NOT NULL
);

CREATE TABLE payment_methods (
  payment_method_id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL
);

CREATE TABLE tx_headers (
  tx_id        INT AUTO_INCREMENT PRIMARY KEY,
  receipt_no   VARCHAR(50),
  cashier_id   INT NOT NULL,
  created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  subtotal     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  discount     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  tax          DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  total        DECIMAL(12,2) NOT NULL DEFAULT 0.00,
  note         VARCHAR(255),
  payment_method_id INT NULL,
  FOREIGN KEY (cashier_id) REFERENCES cashiers(cashier_id),
  FOREIGN KEY (payment_method_id) REFERENCES payment_methods(payment_method_id)
);

CREATE TABLE tx_items (
  tx_item_id INT AUTO_INCREMENT PRIMARY KEY,
  tx_id      INT NOT NULL,
  product_id INT NOT NULL,
  qty        INT NOT NULL,
  price      DECIMAL(10,2) NOT NULL,
  line_total DECIMAL(12,2) NOT NULL,
  FOREIGN KEY (tx_id) REFERENCES tx_headers(tx_id),
  FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

**Seed minimal (opsional):**
```sql
INSERT INTO categories (category_name) VALUES ('Bread'), ('Pastry'), ('Drink');
INSERT INTO payment_methods (code, name) VALUES ('CASH', 'Cash'), ('QRIS', 'QRIS'), ('CARD', 'Debit/Credit');
INSERT INTO cashiers (name) VALUES ('Admin'), ('Kasir 1'), ('Kasir 2');
```

---

## 🖥️ Menu Utama (contoh)
```
Breadtalk POS – CLI (MySQL)
===Menu===
1) Lihat produk
2) Buat transaksi baru
3) Laporan harian
4) Laporan per-produk
5) Laporan per-kasir harian
6) Tambah produk
7) Edit produk
8) Aktif/Nonaktifkan produk
9) Hapus produk
0) Keluar
```

---

## 🧾 Output Tabel (format `github`)
```
|   ID | SKU   | Name        | Category   |   Price |   Active |
|-----:|:------|:------------|:-----------|--------:|---------:|
|    1 | A001  | Roti Tawar  | Bread      |   12.50 |        1 |
|    2 | A002  | Donat       | Pastry     |    8.00 |        1 |
```

---

## 🧪 Testing Lokal (opsional)
- Jalankan `DESCRIBE` untuk memastikan kolom: `DESCRIBE products;`, `DESCRIBE categories;`.
- Cek query langsung di MySQL Workbench sebelum dipakai di Python bila ada error sintaks.

---

## 🛡️ Troubleshooting
- **PowerShell policy** saat aktivasi venv:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```
- **‘git’ is not recognized** → pastikan Git terinstal & PATH sudah di-refresh (restart terminal).
- **MySQL auth** → cek `.env` sesuai kredensial DB kamu.

---

## 📦 Build EXE (opsional)
```bash
pip install pyinstaller
pyinstaller --onefile --name BreadtalkPOS --hidden-import=mysql.connector main.py
# Hasil: dist/BreadtalkPOS.exe
```

---

## 📝 Lisensi
MIT License — bebas digunakan untuk keperluan belajar/komersial dengan atribusi.

---

## 🙌 Kontribusi
PR & issue welcome. Untuk perubahan besar, buka issue dulu untuk diskusi rencana perubahan.

---

## 📣 Kredit
Dibangun bareng asisten AI + semangat ngodingmu. Keep shipping! 🚀
