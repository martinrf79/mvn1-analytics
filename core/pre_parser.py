import pandas as pd
import json
import re
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PreParser:
    """Convertidor universal de formatos a estructura estandar."""

    STANDARD_COLUMNS = {
        "producto": str,
        "precio_venta": float,
        "cantidad": int,
        "costo": float,
        "sucursal": str,
    }

    # ═══ FIX: Aliases en LOWERCASE para matching case-insensitive ═══
    COLUMN_ALIASES = {
        "producto": [
            "producto", "product", "product line", "product_line", "item",
            "articulo", "descripcion", "nombre", "name", "categoria",
            "category", "linea", "tipo", "type", "prod", "mercancia",
        ],
        "precio_venta": [
            "precio_venta", "precio", "price", "unit price", "unit_price",
            "precio_unitario", "precio venta", "selling_price", "sale_price",
            "valor", "value", "pvp", "monto", "amount", "total", "ingreso",
        ],
        "cantidad": [
            "cantidad", "quantity", "qty", "cant", "unidades", "units",
            "count", "piezas", "num", "pieces", "vol", "volume",
        ],
        "costo": [
            "costo", "cost", "cogs", "costo_unitario", "unit_cost",
            "unit cost", "precio_compra", "precio compra", "gasto",
            "expense", "purchase_price", "coste",
        ],
        "sucursal": [
            "sucursal", "branch", "store", "tienda", "sede", "local",
            "location", "ubicacion", "oficina", "office", "city",
            "ciudad", "punto_venta", "region", "zona", "area",
        ],
    }

    def parse(self, file_path: str) -> Dict:
        """Parse un archivo en cualquier formato soportado."""
        path = Path(file_path)
        if not path.exists():
            return {
                "status": "error",
                "error": "Archivo no encontrado: {}".format(file_path),
                "format_detected": "unknown",
            }
        try:
            ext = path.suffix.lower()
            parsers = {
                ".csv": self._parse_csv,
                ".json": self._parse_json,
                ".txt": self._parse_txt,
                ".tsv": self._parse_tsv,
                ".xlsx": self._parse_excel,
                ".xls": self._parse_excel,
            }
            parser_func = parsers.get(ext, self._parse_csv)
            result = parser_func(file_path)

            # ═══ FIX: Si pocas columnas utiles, intentar detectar header real ═══
            if result.get("status") == "success" and result.get("rows", 0) > 0:
                useful = self._count_useful_columns(result["data"])
                if useful < 2:
                    logger.info("PreParser: solo {} columnas utiles, buscando header...".format(useful))
                    better = self._parse_with_header_detection(file_path)
                    if better and better.get("status") == "success":
                        better_useful = self._count_useful_columns(better["data"])
                        if better_useful > useful:
                            logger.info("PreParser: header encontrado, {} columnas utiles".format(better_useful))
                            result = better

            return result
        except Exception as e:
            logger.error("Error parsing {}: {}".format(file_path, e))
            return {"status": "error", "error": str(e), "format_detected": "unknown"}

    def _count_useful_columns(self, df):
        """Cuenta columnas que matchean con aliases conocidos."""
        count = 0
        for col in df.columns:
            col_lower = str(col).strip().lower().replace("_", " ").replace("-", " ")
            for aliases in self.COLUMN_ALIASES.values():
                if col_lower in aliases:
                    count += 1
                    break
        return count

    def _detect_separator(self, line):
        """Detecta el separador mas probable en una linea."""
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

    def _parse_with_header_detection(self, file_path):
        """Escanea primeras 30 lineas buscando fila que parece header real."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = []
                for _ in range(30):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line)

            best_result = None
            best_matches = 0

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
                if matches >= 2 and matches > best_matches:
                    sep = self._detect_separator(stripped)
                    try:
                        df = pd.read_csv(
                            file_path, sep=sep, skiprows=i,
                            encoding="utf-8", on_bad_lines="skip"
                        )
                        if not df.empty and len(df.columns) >= 2:
                            result = self._build_result(df, "csv")
                            if result.get("status") == "success":
                                best_result = result
                                best_matches = matches
                    except Exception:
                        continue
            return best_result
        except Exception as e:
            logger.debug("Header detection failed: {}".format(e))
            return None

    def _parse_csv(self, file_path: str) -> Dict:
        """Parse CSV con deteccion automatica de separador."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                first_line = f.readline()

            sep = self._detect_separator(first_line)
            df = pd.read_csv(file_path, encoding="utf-8", sep=sep, on_bad_lines="skip")

            # ═══ FIX: Si quedo 1 sola columna, probar otros separadores ═══
            if len(df.columns) <= 1:
                for alt_sep in [";", "\t", "|", ","]:
                    if alt_sep == sep:
                        continue
                    try:
                        df2 = pd.read_csv(file_path, encoding="utf-8", sep=alt_sep, on_bad_lines="skip")
                        if len(df2.columns) > len(df.columns):
                            df = df2
                            break
                    except Exception:
                        continue

            return self._build_result(df, "csv")
        except Exception as e:
            return {"status": "error", "error": str(e), "format_detected": "csv"}

    def _parse_json(self, file_path: str) -> Dict:
        """Parse JSON (lista de objetos o objeto unico)."""
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
        """Parse TXT con formatos mixtos (pipe, key:value, etc)."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            records = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if all(c in "-=_*#~" for c in line.replace(" ", "")):
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
        """Parse TSV (tab-separated)."""
        try:
            df = pd.read_csv(file_path, sep="\t", encoding="utf-8", on_bad_lines="skip")
            return self._build_result(df, "tsv")
        except Exception as e:
            return {"status": "error", "error": str(e), "format_detected": "tsv"}

    def _parse_excel(self, file_path: str) -> Dict:
        """Parse Excel (.xlsx, .xls)."""
        try:
            df = pd.read_excel(file_path)
            # ═══ FIX: Si el header no esta en fila 0, buscar ═══
            if len(df.columns) <= 2 or all("unnamed" in str(c).lower() for c in df.columns):
                for skip in range(1, 15):
                    try:
                        df2 = pd.read_excel(file_path, skiprows=skip)
                        if len(df2.columns) > 2 and self._count_useful_columns(df2) >= 2:
                            df = df2
                            break
                    except Exception:
                        break
            return self._build_result(df, "excel")
        except Exception as e:
            return {"status": "error", "error": str(e), "format_detected": "excel"}

    def _parse_line(self, line: str) -> Optional[Dict]:
        """Parsea una linea de texto con formato variable."""
        record = {}
        line = line.replace("$", "").replace("\u20ac", "")
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
            pattern = r"(\w[\w\s]*?)\s*[=:]\s*([^|,;=:]+)"
            for match in re.finditer(pattern, line):
                record[match.group(1).strip().lower().replace(" ", "_")] = match.group(2).strip()
        return record if record else None

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza nombres de columnas al estandar."""
        original_cols = list(df.columns)

        # ═══ FIX 1: Lowercase TODO para matching case-insensitive ═══
        df.columns = [str(c).strip().lower().replace("  ", " ") for c in df.columns]

        # ═══ FIX 2: Eliminar columnas unnamed ═══
        unnamed = [c for c in df.columns if "unnamed" in c]
        if unnamed:
            df = df.drop(columns=unnamed, errors="ignore")

        # ═══ FIX 3: Mapear con aliases (todo lowercase) ═══
        rename_map = {}
        used_std = set()

        # Primero marcar las que ya tienen nombre estandar
        for col in df.columns:
            if col in self.STANDARD_COLUMNS:
                used_std.add(col)

        # Mapear el resto
        for col in df.columns:
            if col in self.STANDARD_COLUMNS:
                continue
            col_variants = set()
            col_variants.add(col)
            col_variants.add(col.replace("_", " "))
            col_variants.add(col.replace("-", " "))
            col_variants.add(col.replace(".", " "))

            for std_name, aliases in self.COLUMN_ALIASES.items():
                if std_name in used_std:
                    continue
                matched = False
                for variant in col_variants:
                    if variant in aliases:
                        rename_map[col] = std_name
                        used_std.add(std_name)
                        matched = True
                        break
                if matched:
                    break

        if rename_map:
            df = df.rename(columns=rename_map)
            logger.info("Columnas mapeadas: {}".format(rename_map))

        # ═══ FIX 4: Convertir tipos SOLO para columnas estandar encontradas ═══
        for col in df.columns:
            if col not in self.STANDARD_COLUMNS:
                continue
            target_type = self.STANDARD_COLUMNS[col]
            try:
                if target_type == float:
                    if df[col].dtype == object:
                        df[col] = (df[col].astype(str)
                                   .str.replace("$", "", regex=False)
                                   .str.replace(",", "", regex=False)
                                   .str.replace("\u20ac", "", regex=False)
                                   .str.replace("EUR", "", regex=False)
                                   .str.strip())
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                elif target_type == int:
                    if df[col].dtype == object:
                        df[col] = (df[col].astype(str)
                                   .str.replace(",", "", regex=False)
                                   .str.strip())
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                elif target_type == str:
                    df[col] = df[col].astype(str)
            except Exception:
                pass

        # ═══ FIX 5: NO filtrar columnas - mantener TODAS ═══
        # El viejo codigo hacia: df = df[valid_cols].copy()
        # Eso eliminaba columnas extras que podrian ser utiles
        return df

    def _build_result(self, df: pd.DataFrame, fmt: str) -> Dict:
        """Construye resultado estandarizado."""
        if df is None or df.empty:
            return {"status": "error", "error": "DataFrame vacio", "format_detected": fmt, "rows": 0}

        # Limpiar filas/columnas totalmente vacias
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")

        if df.empty:
            return {"status": "error", "error": "DataFrame vacio tras limpieza", "format_detected": fmt, "rows": 0}

        original_cols = list(df.columns)
        normalized = self._normalize_columns(df)
        rows = len(normalized)

        return {
            "data": normalized,
            "format_detected": fmt,
            "rows": rows,
            "columns": list(normalized.columns),
            "columns_original": original_cols,
            "status": "success" if rows > 0 else "error",
        }


def run():
    """Funcion requerida por el sistema."""
    logger.info("PreParser configurado correctamente")
    return {"status": "configured", "module": "PreParser"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run()
    print(result)