from decimal import Decimal
from typing import Optional

def input_nonempty(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        if s:
            return s
        print("Tidak boleh kosong.")

def input_decimal(prompt: str, min_value: Optional[Decimal] = None) -> Decimal:
    while True:
        try:
            val = Decimal(input(prompt).strip())
            if min_value is not None and val < min_value:
                print(f"Harus >= {min_value}")
                continue
            return val
        except Exception:
            print("Input angka tidak valid.")

def input_int(prompt: str, min_value: Optional[int] = None) -> int:
    while True:
        try:
            val = int(input(prompt).strip())
            if min_value is not None and val < min_value:
                print(f"Harus >= {min_value}")
                continue
            return val
        except Exception:
            print("Input integer tidak valid.")