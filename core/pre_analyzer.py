import pandas as pd
import re
import logging
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class PreAnalyzer:
    COLUMN_ALIASES = {
        "producto": ["producto","product","product line","product_line","item","articulo","descripcion","nombre","name","prod","linea","categoria","category","tipo","type"],
        "precio_venta": ["precio_venta","precio","price","unit price","unit_price","precio_unitario","valor","value","pvp","precio venta","sale_price","selling_price","monto","amount","precio_venta"],
        "cantidad": ["cantidad","quantity","qty","cant","unidades","units","count","num","piezas","pieces","vol","volume"],
        "costo": ["costo","cost","cogs","precio_costo","unit_cost","costo_unitario","purchase_price","precio_compra","gasto","expense"],
        "sucursal": ["sucursal","branch","store","tienda","sede","local","location","ubicacion","oficina","office","punto_venta","city","ciudad"],
    }

    def __init__(self):
        self._fixes = []

    def analyze_and_fix(self, file_path: str) -> Dict:
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "error": "Archivo no encontrado", "format_detected": "unknown"}
        try:
            self._fixes = []
            df = self._smart_read(file_path)
            if df is None or df.empty:
                return {"status": "error", "error": "No se pudieron extraer datos", "format_detected": "unknown"}
            original_cols = list(df.columns)
            df = self._clean_dataframe(df)
            df = self._map_columns(df)
            df = self._fix_data_types(df)
            df = self._fill_missing_columns(df)
            df = self._remove_garbage_rows(df)
            if df.empty:
                return {"status": "error", "error": "No quedaron datos validos", "format_detected": "unknown"}
            return {"data": df, "format_detected": path.suffix.lower().replace(".", "") or "txt", "rows": len(df), "columns": list(df.columns), "columns_original": original_cols, "status": "success", "pre_analyzed": True, "fixes_applied": self._fixes}
        except Exception as e:
            logger.error("PreAnalyzer error: {}".format(e))
            return {"status": "error", "error": str(e), "format_detected": "unknown"}

    def _smart_read(self, file_path: str) -> Optional[pd.DataFrame]:
        strategies = [
            ("CSV coma", lambda: pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")),
            ("CSV punto y coma", lambda: pd.read_csv(file_path, sep=";", encoding="utf-8", on_bad_lines="skip")),
            ("CSV tab", lambda: pd.read_csv(file_path, sep="\t", encoding="utf-8", on_bad_lines="skip")),
            ("CSV pipe", lambda: pd.read_csv(file_path, sep="|", encoding="utf-8", on_bad_lines="skip")),
            ("Latin1", lambda: pd.read_csv(file_path, encoding="latin-1", on_bad_lines="skip")),
            ("Texto libre", lambda: self._read_freetext(file_path)),
        ]
        best_df = None
        best_cols = 0
        for name, reader in strategies:
            try:
                df = reader()
                if df is not None and not df.empty and len(df.columns) >= 2:
                    useful = self._count_useful_columns(df)
                    if useful > best_cols:
                        best_cols = useful
                        best_df = df
                        self._fixes.append("Formato: {}".format(name))
                        if useful >= 3:
                            return df
            except Exception:
                continue
        return best_df

    def _read_freetext(self, file_path: str) -> Optional[pd.DataFrame]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        records = []
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            if all(c in "-=_*#" for c in line.replace(" ", "")):
                continue
            record = {}
            pairs = re.findall(r"(\w[\w\s]*?)\s*[=:]\s*([^|,;=:]+)", line)
            if pairs:
                for key, val in pairs:
                    clean_key = key.strip().lower().replace(" ", "_")
                    clean_val = val.strip().rstrip(",;|")
                    record[clean_key] = clean_val
            if not record:
                for sep in ["|", ",", "\t", ";"]:
                    parts = [p.strip() for p in line.split(sep)]
                    if len(parts) >= 3:
                        for i, part in enumerate(parts):
                            if ":" in part or "=" in part:
                                delim = ":" if ":" in part else "="
                                k, _, v = part.partition(delim)
                                record[k.strip().lower().replace(" ", "_")] = v.strip()
                            else:
                                record["col_{}".format(i)] = part
                        break
            if record and len(record) >= 2:
                records.append(record)
        if records:
            self._fixes.append("Texto libre: {} registros".format(len(records)))
            return pd.DataFrame(records)
        return None

    def _count_useful_columns(self, df):
        count = 0
        for col in df.columns:
            col_lower = str(col).strip().lower().replace("_", " ")
            for aliases in self.COLUMN_ALIASES.values():
                if col_lower in aliases:
                    count += 1
                    break
        return count

    def _clean_dataframe(self, df):
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        empty_cols = [c for c in df.columns if df[c].isna().all()]
        if empty_cols:
            df = df.drop(columns=empty_cols)
            self._fixes.append("{} columnas vacias eliminadas".format(len(empty_cols)))
        before = len(df)
        df = df.dropna(how="all")
        dropped = before - len(df)
        if dropped > 0:
            self._fixes.append("{} filas vacias eliminadas".format(dropped))
        unnamed = [c for c in df.columns if "unnamed" in str(c).lower()]
        if unnamed:
            df = df.drop(columns=unnamed)
        return df

    def _map_columns(self, df):
        rename_map = {}
        for std_name, aliases in self.COLUMN_ALIASES.items():
            if std_name in df.columns:
                continue
            for col in df.columns:
                col_clean = str(col).strip().lower().replace("_", " ").replace("-", " ")
                if col_clean in aliases:
                    rename_map[col] = std_name
                    break
        if rename_map:
            df = df.rename(columns=rename_map)
            self._fixes.append("Columnas mapeadas: {}".format(dict(rename_map)))
        return df

    def _fix_data_types(self, df):
        for col in ["precio_venta", "costo"]:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False).str.replace("EUR", "", regex=False).str.strip()
                df[col] = pd.to_numeric(df[col], errors="coerce")
                mask = df[col] < 0
                if mask.any():
                    df.loc[mask, col] = df.loc[mask, col].abs()
                    self._fixes.append("{}: {} negativos corregidos".format(col, int(mask.sum())))
        if "cantidad" in df.columns:
            if df["cantidad"].dtype == object:
                df["cantidad"] = df["cantidad"].astype(str).str.replace(",", "", regex=False).str.strip()
                df["cantidad"] = df["cantidad"].str.extract(r"(\d+)")[0]
            df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")
            mask = (df["cantidad"].isna()) | (df["cantidad"] <= 0)
            if mask.any():
                df.loc[mask, "cantidad"] = 1
            df["cantidad"] = df["cantidad"].astype(int)
        for col in ["producto", "sucursal"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace({"nan": "Sin datos", "None": "Sin datos", "": "Sin datos"})
        return df

    def _fill_missing_columns(self, df):
        defaults = {"producto": "Sin clasificar", "precio_venta": 0.0, "cantidad": 1, "costo": 0.0, "sucursal": "General"}
        for col, default_val in defaults.items():
            if col not in df.columns:
                df[col] = default_val
                self._fixes.append("Columna '{}' creada".format(col))
            else:
                nulls = int(df[col].isna().sum())
                if nulls > 0:
                    if isinstance(default_val, (int, float)):
                        median = df[col].median()
                        df[col] = df[col].fillna(median if pd.notna(median) else default_val)
                    else:
                        df[col] = df[col].fillna(default_val)
                    self._fixes.append("{}: {} nulos rellenados".format(col, nulls))
        std_cols = ["producto", "precio_venta", "cantidad", "costo", "sucursal"]
        extra = [c for c in df.columns if c not in std_cols]
        df = df[std_cols + extra]
        return df

    def _remove_garbage_rows(self, df):
        before = len(df)
        if "precio_venta" in df.columns and "costo" in df.columns:
            mask = ((df["precio_venta"].isna()) | (df["precio_venta"] == 0)) & ((df["costo"].isna()) | (df["costo"] == 0))
            df = df[~mask]
        if "producto" in df.columns:
            garbage = ["producto", "product", "item", "nombre", "---", "===", "***"]
            for word in garbage:
                df = df[~df["producto"].str.lower().str.strip().eq(word)]
        dropped = before - len(df)
        if dropped > 0:
            self._fixes.append("{} filas basura eliminadas".format(dropped))
        return df.reset_index(drop=True)


def run():
    return {"status": "configured", "module": "PreAnalyzer"}
