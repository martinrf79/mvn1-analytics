import pandas as pd
import json
import re
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PreParser:
    STANDARD_COLUMNS = {
        "producto": str,
        "precio_venta": float,
        "cantidad": int,
        "costo": float,
        "sucursal": str,
    }

    COLUMN_MAP = {
        "product line": "producto",
        "Product line": "producto",
        "product": "producto",
        "Product": "producto",
        "PRODUCTO": "producto",
        "unit price": "precio_venta",
        "Unit price": "precio_venta",
        "price": "precio_venta",
        "Price": "precio_venta",
        "quantity": "cantidad",
        "Quantity": "cantidad",
        "Qty": "cantidad",
        "qty": "cantidad",
        "cogs": "costo",
        "COGS": "costo",
        "cost": "costo",
        "Cost": "costo",
        "Costo": "costo",
        "branch": "sucursal",
        "Branch": "sucursal",
        "store": "sucursal",
        "Store": "sucursal",
        "tienda": "sucursal",
        "Tienda": "sucursal",
    }

    def parse(self, file_path: str) -> Dict:
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "error": f"Archivo no encontrado: {file_path}", "format_detected": "unknown"}
        try:
            ext = path.suffix.lower()
            parsers = {".csv": self._parse_csv, ".json": self._parse_json, ".txt": self._parse_txt, ".tsv": self._parse_tsv, ".xlsx": self._parse_excel, ".xls": self._parse_excel}
            parser_func = parsers.get(ext, self._parse_csv)
            return parser_func(file_path)
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return {"status": "error", "error": str(e), "format_detected": "unknown"}

    def _parse_csv(self, file_path: str) -> Dict:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                first_line = f.readline()
            sep = ","
            if chr(9) in first_line:
                sep = chr(9)
            elif ";" in first_line:
                sep = ";"
            df = pd.read_csv(file_path, encoding="utf-8", sep=sep, on_bad_lines="skip")
            return self._build_result(df, "csv")
        except Exception as e:
            return {"status": "error", "error": str(e), "format_detected": "csv"}

    def _parse_json(self, file_path: str) -> Dict:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                if any(isinstance(v, list) for v in data.values()):
                    for key, value in data.items():
                        if isinstance(value, list):
                            df = pd.DataFrame(value)
                            break
                else:
                    df = pd.DataFrame([data])
            else:
                raise ValueError("Formato JSON no soportado")
            return self._build_result(df, "json")
        except Exception as e:
            return {"status": "error", "error": str(e), "format_detected": "json"}

    def _parse_txt(self, file_path: str) -> Dict:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            records = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                record = self._parse_line(line)
                if record and len(record) >= 2:
                    records.append(record)
            if not records:
                return self._parse_csv(file_path)
            df = pd.DataFrame(records)
            return self._build_result(df, "txt")
        except Exception as e:
            return {"status": "error", "error": str(e), "format_detected": "txt"}

    def _parse_tsv(self, file_path: str) -> Dict:
        try:
            df = pd.read_csv(file_path, sep=chr(9), encoding="utf-8")
            return self._build_result(df, "tsv")
        except Exception as e:
            return {"status": "error", "error": str(e), "format_detected": "tsv"}

    def _parse_excel(self, file_path: str) -> Dict:
        try:
            df = pd.read_excel(file_path)
            return self._build_result(df, "excel")
        except Exception as e:
            return {"status": "error", "error": str(e), "format_detected": "excel"}

    def _parse_line(self, line: str) -> Optional[Dict]:
        record = {}
        line = line.replace("$", "").replace(chr(8364), "")
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            for part in parts:
                if ":" in part:
                    key, _, value = part.partition(":")
                    record[key.strip().lower().replace(" ", "_")] = value.strip()
                elif "=" in part:
                    key, _, value = part.partition("=")
                    record[key.strip().lower().replace(" ", "_")] = value.strip()
        elif ":" in line or "=" in line:
            pattern = r"(\w+)\s*[=:]\s*([^|,;]+)"
            for match in re.finditer(pattern, line):
                record[match.group(1).lower().replace(" ", "_")] = match.group(2).strip()
        return record if record else None

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [str(c).strip() for c in df.columns]
        df = df.rename(columns=self.COLUMN_MAP)
        valid_cols = [c for c in df.columns if c in self.STANDARD_COLUMNS]
        if valid_cols:
            df = df[valid_cols].copy()
        for col in df.columns:
            if col in self.STANDARD_COLUMNS:
                target_type = self.STANDARD_COLUMNS[col]
                try:
                    if target_type == float:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                    elif target_type == int:
                        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                    elif target_type == str:
                        df[col] = df[col].astype(str)
                except Exception:
                    pass
        return df

    def _build_result(self, df: pd.DataFrame, fmt: str) -> Dict:
        normalized = self._normalize_columns(df)
        return {"data": normalized, "format_detected": fmt, "rows": len(normalized), "columns": list(normalized.columns), "columns_original": list(df.columns), "status": "success"}


def run():
    logger.info("PreParser configurado correctamente")
    return {"status": "configured", "module": "PreParser"}
