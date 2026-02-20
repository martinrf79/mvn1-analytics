import pandas as pd
import re
import logging
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class PreAnalyzer:
    """Analizador previo que lee y repara datos desordenados."""

    COLUMN_ALIASES = {
        "producto": [
            "producto", "product", "product line", "product_line", "item",
            "articulo", "descripcion", "nombre", "name", "prod", "linea",
            "categoria", "category", "tipo", "type", "mercancia",
        ],
        "precio_venta": [
            "precio_venta", "precio", "price", "unit price", "unit_price",
            "precio_unitario", "valor", "value", "pvp", "precio venta",
            "sale_price", "selling_price", "monto", "amount", "total",
            "ingreso",
        ],
        "cantidad": [
            "cantidad", "quantity", "qty", "cant", "unidades", "units",
            "count", "num", "piezas", "pieces", "vol", "volume",
        ],
        "costo": [
            "costo", "cost", "cogs", "precio_costo", "unit_cost",
            "costo_unitario", "purchase_price", "precio_compra", "gasto",
            "expense", "coste", "unit cost",
        ],
        "sucursal": [
            "sucursal", "branch", "store", "tienda", "sede", "local",
            "location", "ubicacion", "oficina", "office", "punto_venta",
            "city", "ciudad", "region", "zona", "area",
        ],
    }

    def __init__(self):
        self._fixes = []
        self._auto_created_columns = set()

    def analyze_and_fix(self, file_path: str) -> Dict:
        """Lee, analiza y repara un archivo de datos."""
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "error": "Archivo no encontrado", "format_detected": "unknown"}
        try:
            self._fixes = []
            self._auto_created_columns = set()

            df = self._smart_read(file_path)
            if df is None or df.empty:
                return {"status": "error", "error": "No se pudieron extraer datos", "format_detected": "unknown"}

            original_cols = list(df.columns)
            logger.info("PreAnalyzer: {} filas leidas, columnas: {}".format(len(df), list(df.columns)))

            df = self._clean_dataframe(df)
            df = self._map_columns(df)
            df = self._fix_data_types(df)
            df = self._fill_missing_columns(df)
            df = self._remove_garbage_rows(df)

            # ═══ FIX: Si quedo vacio, reintentar SIN filtro de basura ═══
            if df.empty:
                logger.warning("PreAnalyzer: vacio tras limpieza, reintentando sin filtro...")
                df = self._smart_read(file_path)
                if df is not None and not df.empty:
                    df = self._clean_dataframe(df)
                    df = self._map_columns(df)
                    df = self._fix_data_types(df)
                    self._auto_created_columns = set()
                    df = self._fill_missing_columns(df)
                    # NO llamar _remove_garbage_rows
                    self._fixes.append("Filtro de basura desactivado para preservar datos")

            if df.empty:
                return {"status": "error", "error": "No quedaron datos validos", "format_detected": "unknown"}

            return {
                "data": df,
                "format_detected": path.suffix.lower().replace(".", "") or "txt",
                "rows": len(df),
                "columns": list(df.columns),
                "columns_original": original_cols,
                "status": "success",
                "pre_analyzed": True,
                "fixes_applied": self._fixes,
            }
        except Exception as e:
            logger.error("PreAnalyzer error: {}".format(e))
            return {"status": "error", "error": str(e), "format_detected": "unknown"}

    def _detect_separator(self, line):
        """Detecta el separador mas probable."""
        candidates = [
            (",", line.count(",")),
            (";", line.count(";")),
            ("\t", line.count("\t")),
            ("|", line.count("|")),
        ]
        candidates = [(sep, cnt) for sep, cnt in candidates if cnt > 0]
        if candidates:
            return max(candidates, key=lambda x: x[1])[0]
        return ","

    def _find_header_row(self, file_path: str):
        """Escanea primeras 30 lineas para encontrar header real."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = []
                for _ in range(30):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)

            best_row = 0
            best_matches = 0
            best_sep = ","

            for i, line in enumerate(lines):
                stripped = line.strip()
                if not stripped or len(stripped) < 3:
                    continue
                line_lower = stripped.lower()
                matches = 0
                for aliases in self.COLUMN_ALIASES.values():
                    for alias in aliases:
                        if alias in line_lower:
                            matches += 1
                            break
                if matches > best_matches:
                    best_matches = matches
                    best_row = i
                    best_sep = self._detect_separator(stripped)

            if best_matches >= 2:
                return best_row, best_sep
        except Exception:
            pass
        return None, None

    def _smart_read(self, file_path: str) -> Optional[pd.DataFrame]:
        """Lee archivo probando multiples estrategias."""
        # Primero intentar detectar header
        header_row, header_sep = self._find_header_row(file_path)

        strategies = []

        # Si encontramos header, priorizarlo
        if header_row is not None:
            strategies.append(
                ("Header detectado (fila {})".format(header_row),
                 lambda: pd.read_csv(file_path, sep=header_sep, skiprows=header_row,
                                     encoding="utf-8", on_bad_lines="skip"))
            )

        # Estrategias estandar
        strategies.extend([
            ("CSV coma", lambda: pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")),
            ("CSV punto y coma", lambda: pd.read_csv(file_path, sep=";", encoding="utf-8", on_bad_lines="skip")),
            ("CSV tab", lambda: pd.read_csv(file_path, sep="\t", encoding="utf-8", on_bad_lines="skip")),
            ("CSV pipe", lambda: pd.read_csv(file_path, sep="|", encoding="utf-8", on_bad_lines="skip")),
            ("Latin1 coma", lambda: pd.read_csv(file_path, encoding="latin-1", on_bad_lines="skip")),
            ("Latin1 punto y coma", lambda: pd.read_csv(file_path, sep=";", encoding="latin-1", on_bad_lines="skip")),
        ])

        # Probar con skiprows
        for skip in [1, 2, 3, 5]:
            s = skip  # captura variable
            strategies.append(
                ("CSV skip {}".format(s),
                 lambda s=s: pd.read_csv(file_path, encoding="utf-8", skiprows=s, on_bad_lines="skip"))
            )

        strategies.append(("Texto libre", lambda: self._read_freetext(file_path)))

        best_df = None
        best_score = 0
        best_name = ""

        for name, reader in strategies:
            try:
                df = reader()
                if df is None or df.empty or len(df.columns) < 1:
                    continue

                # Puntuar: columnas utiles pesan mas
                useful = self._count_useful_columns(df)
                score = useful * 100 + min(len(df), 50) + len(df.columns)

                if score > best_score:
                    best_score = score
                    best_df = df
                    best_name = name

                    # 3+ columnas utiles con datos = suficiente
                    if useful >= 3 and len(df) > 0:
                        self._fixes.append("Formato: {}".format(name))
                        logger.info("PreAnalyzer: '{}' score={} cols_utiles={} filas={}".format(
                            name, score, useful, len(df)))
                        return df
            except Exception:
                continue

        if best_df is not None:
            self._fixes.append("Formato: {}".format(best_name))
            logger.info("PreAnalyzer: usando '{}' score={} filas={}".format(best_name, best_score, len(best_df)))

        return best_df

    def _read_freetext(self, file_path: str) -> Optional[pd.DataFrame]:
        """Lee archivo de texto libre intentando extraer datos."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        records = []
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            if all(c in "-=_*#~" for c in line.replace(" ", "")):
                continue
            record = {}
            # Intentar key:value o key=value
            pairs = re.findall(r"(\w[\w\s]*?)\s*[=:]\s*([^|,;=:]+)", line)
            if pairs:
                for key, val in pairs:
                    clean_key = key.strip().lower().replace(" ", "_")
                    clean_val = val.strip().rstrip(",;|")
                    record[clean_key] = clean_val
            # Si no encontro pares, separar por delimitadores
            if not record:
                for sep in ["|", "\t", ";", ","]:
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
        """Cuenta columnas que matchean aliases conocidos."""
        count = 0
        for col in df.columns:
            col_lower = str(col).strip().lower().replace("_", " ").replace("-", " ")
            for aliases in self.COLUMN_ALIASES.values():
                if col_lower in aliases:
                    count += 1
                    break
        return count

    def _clean_dataframe(self, df):
        """Limpia DataFrame de basura obvia."""
        df.columns = [str(c).strip().lower().replace("  ", " ").replace(" ", "_") for c in df.columns]
        # Eliminar columnas vacias
        empty_cols = [c for c in df.columns if df[c].isna().all()]
        if empty_cols:
            df = df.drop(columns=empty_cols)
            self._fixes.append("{} columnas vacias eliminadas".format(len(empty_cols)))
        # Eliminar filas vacias
        before = len(df)
        df = df.dropna(how="all")
        dropped = before - len(df)
        if dropped > 0:
            self._fixes.append("{} filas vacias eliminadas".format(dropped))
        # Eliminar columnas unnamed
        unnamed = [c for c in df.columns if "unnamed" in str(c).lower()]
        if unnamed:
            df = df.drop(columns=unnamed)
        return df

    def _map_columns(self, df):
        """Mapea columnas a nombres estandar."""
        rename_map = {}
        used_std = set()

        for std_name, aliases in self.COLUMN_ALIASES.items():
            if std_name in df.columns:
                used_std.add(std_name)
                continue
            if std_name in used_std:
                continue
            for col in df.columns:
                col_clean = str(col).strip().lower().replace("_", " ").replace("-", " ")
                if col_clean in aliases:
                    rename_map[col] = std_name
                    used_std.add(std_name)
                    break

        if rename_map:
            df = df.rename(columns=rename_map)
            self._fixes.append("Columnas mapeadas: {}".format(dict(rename_map)))
        return df

    def _fix_data_types(self, df):
        """Corrige tipos de datos."""
        for col in ["precio_venta", "costo"]:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = (df[col].astype(str)
                               .str.replace("$", "", regex=False)
                               .str.replace(",", "", regex=False)
                               .str.replace("EUR", "", regex=False)
                               .str.replace("\u20ac", "", regex=False)
                               .str.strip())
                df[col] = pd.to_numeric(df[col], errors="coerce")
                mask = df[col] < 0
                if mask.any():
                    df.loc[mask, col] = df.loc[mask, col].abs()
                    self._fixes.append("{}: {} negativos corregidos".format(col, int(mask.sum())))

        if "cantidad" in df.columns:
            if df["cantidad"].dtype == object:
                df["cantidad"] = df["cantidad"].astype(str).str.replace(",", "", regex=False).str.strip()
                extracted = df["cantidad"].str.extract(r"(\d+)")
                if not extracted.empty:
                    df["cantidad"] = extracted[0]
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
        """Crea columnas faltantes con valores por defecto."""
        defaults = {
            "producto": "Sin clasificar",
            "precio_venta": 0.0,
            "cantidad": 1,
            "costo": 0.0,
            "sucursal": "General",
        }
        for col, default_val in defaults.items():
            if col not in df.columns:
                df[col] = default_val
                # ═══ FIX CRITICO: Trackear columna auto-creada ═══
                self._auto_created_columns.add(col)
                self._fixes.append("Columna '{}' creada con valor por defecto".format(col))
            else:
                nulls = int(df[col].isna().sum())
                if nulls > 0:
                    if isinstance(default_val, (int, float)):
                        median = df[col].median()
                        fill_val = median if pd.notna(median) else default_val
                        df[col] = df[col].fillna(fill_val)
                    else:
                        df[col] = df[col].fillna(default_val)
                    self._fixes.append("{}: {} nulos rellenados".format(col, nulls))

        std_cols = ["producto", "precio_venta", "cantidad", "costo", "sucursal"]
        extra = [c for c in df.columns if c not in std_cols]
        df = df[std_cols + extra]
        return df

    def _remove_garbage_rows(self, df):
        """Elimina filas basura pero con protecciones."""
        before = len(df)

        # ═══ FIX CRITICO: NO filtrar por precio/costo si fueron AUTO-CREADOS ═══
        if "precio_venta" in df.columns and "costo" in df.columns:
            precio_auto = "precio_venta" in self._auto_created_columns
            costo_auto = "costo" in self._auto_created_columns

            if not (precio_auto and costo_auto):
                # Solo filtrar si al menos UNA columna tiene datos reales
                mask = (
                    ((df["precio_venta"].isna()) | (df["precio_venta"] == 0)) &
                    ((df["costo"].isna()) | (df["costo"] == 0))
                )
                # ═══ FIX: NUNCA eliminar si se eliminarian TODAS las filas ═══
                if mask.any() and not mask.all():
                    df = df[~mask]
                elif mask.all():
                    self._fixes.append("Filtro precio/costo omitido (eliminaria todas las filas)")

        # Eliminar filas con texto basura en producto
        if "producto" in df.columns:
            garbage = [
                "producto", "product", "item", "nombre", "---", "===",
                "***", "nan", "none", "null", "header", "total", "subtotal",
            ]
            mask = df["producto"].str.lower().str.strip().isin(garbage)
            # ═══ FIX: No eliminar si se eliminarian todas ═══
            if mask.any() and not mask.all():
                df = df[~mask]

        dropped = before - len(df)
        if dropped > 0:
            self._fixes.append("{} filas basura eliminadas".format(dropped))

        return df.reset_index(drop=True)


def run():
    return {"status": "configured", "module": "PreAnalyzer"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run()
    print(result)