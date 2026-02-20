import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  OK  {path}")

print("="*50)
print("  Creando 11 scripts completos...")
print("="*50)

# SCRIPT 1
write_file("core/pre_parser.py", """import pandas as pd
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
            pattern = r"(\\w+)\\s*[=:]\\s*([^|,;]+)"
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
""")

# SCRIPT 2
write_file("core/data_validator.py", """import pandas as pd
import numpy as np
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class DataValidator:
    def __init__(self, min_confidence: float = 0.60):
        self.min_confidence = min_confidence
        self.issues: List[str] = []

    def validate(self, df: pd.DataFrame) -> Dict:
        self.issues = []
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            return {"quality_score": 0, "valid": False, "error": "DataFrame vacio", "issues": ["Datos vacios"]}
        try:
            duplicates = self._check_duplicates(df)
            nulls = self._check_nulls(df)
            ranges = self._check_ranges(df)
            types = self._check_types(df)
            quality_score = self._calculate_score(duplicates, nulls, ranges, types)
            return {"quality_score": round(quality_score, 2), "valid": quality_score >= (self.min_confidence * 100), "duplicates": duplicates, "nulls": nulls, "ranges": ranges, "types": types, "issues": self.issues.copy(), "recommendations": self._get_recommendations(), "total_rows": len(df), "total_columns": len(df.columns)}
        except Exception as e:
            logger.error(f"Error en validacion: {e}")
            return {"quality_score": 0, "valid": False, "error": str(e)}

    def _check_duplicates(self, df):
        total_rows = len(df)
        if total_rows == 0:
            return {"count": 0, "percentage": 0.0}
        duplicates = int(df.duplicated().sum())
        pct = round(duplicates / total_rows * 100, 2)
        if duplicates > 0:
            self.issues.append(f"{duplicates} filas duplicadas ({pct}%)")
        return {"count": duplicates, "percentage": pct}

    def _check_nulls(self, df):
        null_counts = df.isnull().sum()
        total_cells = len(df) * len(df.columns)
        total_nulls = int(null_counts.sum())
        pct = round(total_nulls / total_cells * 100, 2) if total_cells > 0 else 0
        null_by_column = {}
        for col in df.columns:
            col_nulls = int(null_counts[col])
            if col_nulls > 0:
                null_by_column[col] = {"count": col_nulls, "percentage": round(col_nulls / len(df) * 100, 2)}
        if total_nulls > 0:
            self.issues.append(f"{total_nulls} valores nulos totales ({pct}%)")
        return {"total": total_nulls, "percentage": pct, "by_column": null_by_column}

    def _check_ranges(self, df):
        issues = {}
        numeric_checks = {"precio_venta": {"min": 0, "max": 1000000}, "costo": {"min": 0, "max": 1000000}, "cantidad": {"min": 0, "max": 100000}}
        for col, limits in numeric_checks.items():
            if col not in df.columns:
                continue
            col_data = pd.to_numeric(df[col], errors="coerce")
            negatives = int((col_data < limits["min"]).sum())
            excessive = int((col_data > limits["max"]).sum())
            if negatives > 0 or excessive > 0:
                issues[col] = {"negative_values": negatives, "excessive_values": excessive}
                if negatives > 0:
                    self.issues.append(f"Columna '{col}': {negatives} valores negativos")
                if excessive > 0:
                    self.issues.append(f"Columna '{col}': {excessive} valores excesivos")
        return {"issues": issues, "columns_checked": list(numeric_checks.keys())}

    def _check_types(self, df):
        expected = {"producto": "text", "precio_venta": "numeric", "cantidad": "numeric", "costo": "numeric", "sucursal": "text"}
        type_checks = {}
        for col, expected_type in expected.items():
            if col not in df.columns:
                self.issues.append(f"Columna faltante: '{col}'")
                type_checks[col] = {"status": "MISSING", "expected": expected_type}
            else:
                type_checks[col] = {"status": "OK", "dtype": str(df[col].dtype)}
        return type_checks

    def _calculate_score(self, duplicates, nulls, ranges, types):
        score = 100.0
        score -= min(duplicates.get("percentage", 0) * 2, 20)
        score -= min(nulls.get("percentage", 0) * 3, 30)
        for col_issues in ranges.get("issues", {}).values():
            total_bad = col_issues.get("negative_values", 0) + col_issues.get("excessive_values", 0)
            score -= min(total_bad * 2, 10)
        missing_cols = sum(1 for v in types.values() if v.get("status") == "MISSING")
        score -= missing_cols * 5
        return max(score, 0.0)

    def _get_recommendations(self):
        recs = []
        for issue in self.issues:
            if "duplicada" in issue:
                recs.append("Eliminar filas duplicadas")
            elif "nulo" in issue:
                recs.append("Revisar valores nulos")
            elif "negativo" in issue:
                recs.append("Corregir valores negativos")
            elif "faltante" in issue:
                recs.append("Verificar columnas requeridas")
        return list(set(recs))


def run():
    logger.info("DataValidator configurado correctamente")
    return {"status": "configured", "module": "DataValidator"}
""")

# SCRIPT 3
write_file("core/analyzer_ventas.py", """import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class AnalizadorVentas:
    def analyze(self, parsed_data: Dict) -> Dict:
        try:
            df = parsed_data.get("data")
            if df is None or df.empty:
                return {"status": "error", "error": "Datos vacios"}
            df = df.copy()
            df["total"] = df["precio_venta"] * df["cantidad"]
            total_ventas = float(df["total"].sum())
            num_transacciones = len(df)
            ticket_promedio = total_ventas / num_transacciones if num_transacciones > 0 else 0
            ventas_categoria = {}
            if "producto" in df.columns:
                for prod in df["producto"].dropna().unique():
                    df_prod = df[df["producto"] == prod]
                    ventas_categoria[str(prod)] = {"total": float(df_prod["total"].sum()), "transacciones": int(len(df_prod)), "ticket_promedio": float(df_prod["total"].mean())}
            ventas_sucursal = {}
            if "sucursal" in df.columns:
                for sucursal in df["sucursal"].dropna().unique():
                    df_suc = df[df["sucursal"] == sucursal]
                    ventas_sucursal[str(sucursal)] = {"total": float(df_suc["total"].sum()), "transacciones": int(len(df_suc)), "ticket_promedio": float(df_suc["total"].mean())}
            top_productos = []
            if "producto" in df.columns:
                top = df.nlargest(5, "total")
                top_productos = top[["producto", "precio_venta", "cantidad"]].to_dict("records")
            return {"status": "success", "total_ventas": total_ventas, "transacciones": num_transacciones, "ticket_promedio": round(ticket_promedio, 2), "ventas_por_categoria": ventas_categoria, "ventas_por_sucursal": ventas_sucursal, "top_productos": top_productos}
        except Exception as e:
            logger.error(f"Error en analisis de ventas: {e}")
            return {"status": "error", "error": str(e)}


def run():
    logger.info("AnalizadorVentas configurado correctamente")
    return {"status": "configured", "module": "AnalizadorVentas"}
""")

# SCRIPT 4
write_file("core/analyzer_rentabilidad.py", """import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class AnalizadorRentabilidad:
    def analyze(self, parsed_data: Dict) -> Dict:
        try:
            df = parsed_data.get("data")
            if df is None or df.empty:
                return {"status": "error", "error": "Datos vacios"}
            df = df.copy()
            df["margen_unitario"] = df["precio_venta"] - df["costo"]
            df["margen_porcentaje"] = (df["margen_unitario"] / df["costo"] * 100).fillna(0)
            df["total_venta"] = df["precio_venta"] * df["cantidad"]
            df["total_costo"] = df["costo"] * df["cantidad"]
            df["total_margen"] = df["total_venta"] - df["total_costo"]
            total_venta = float(df["total_venta"].sum())
            total_costo = float(df["total_costo"].sum())
            total_margen = float(df["total_margen"].sum())
            margen_promedio = (total_margen / total_venta * 100) if total_venta > 0 else 0
            productos_perdida = df[df["margen_unitario"] < 0]
            num_perdidas = len(productos_perdida)
            total_perdida = float(productos_perdida["total_margen"].sum())
            top_rentables = []
            if "producto" in df.columns:
                top = df.nlargest(5, "margen_porcentaje")
                top_rentables = top[["producto", "margen_unitario", "margen_porcentaje"]].to_dict("records")
            return {"status": "success", "total_venta": total_venta, "total_costo": total_costo, "total_margen": total_margen, "margen_promedio_porcentaje": round(margen_promedio, 2), "productos_con_perdida": num_perdidas, "total_perdida": round(total_perdida, 2), "top_rentables": top_rentables}
        except Exception as e:
            logger.error(f"Error en analisis de rentabilidad: {e}")
            return {"status": "error", "error": str(e)}


def run():
    logger.info("AnalizadorRentabilidad configurado correctamente")
    return {"status": "configured", "module": "AnalizadorRentabilidad"}
""")

# SCRIPT 5
write_file("core/analyzer_auditoria.py", """import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class AnalizadorAuditoria:
    def analyze(self, parsed_data: Dict) -> Dict:
        try:
            df = parsed_data.get("data")
            if df is None or df.empty:
                return {"status": "error", "error": "Datos vacios"}
            anomalias = []
            nulls = int(df.isnull().sum().sum())
            if nulls > 0:
                anomalias.append(f"{nulls} valores nulos encontrados")
            dups = int(df.duplicated().sum())
            if dups > 0:
                anomalias.append(f"{dups} filas duplicadas")
            if "precio_venta" in df.columns:
                negs = int((pd.to_numeric(df["precio_venta"], errors="coerce") < 0).sum())
                if negs > 0:
                    anomalias.append(f"{negs} precios de venta negativos")
            if "costo" in df.columns:
                negs_costo = int((pd.to_numeric(df["costo"], errors="coerce") < 0).sum())
                if negs_costo > 0:
                    anomalias.append(f"{negs_costo} costos negativos")
            if "cantidad" in df.columns:
                bad_qty = int((pd.to_numeric(df["cantidad"], errors="coerce") <= 0).sum())
                if bad_qty > 0:
                    anomalias.append(f"{bad_qty} cantidades invalidas (<=0)")
            confianza = max(100 - (len(anomalias) * 15), 0)
            return {"status": "success", "anomalias_detectadas": len(anomalias), "anomalias": anomalias, "filas_totales": len(df), "confianza_auditoria": confianza}
        except Exception as e:
            logger.error(f"Error en auditoria: {e}")
            return {"status": "error", "error": str(e)}


def run():
    logger.info("AnalizadorAuditoria configurado correctamente")
    return {"status": "configured", "module": "AnalizadorAuditoria"}
""")

# SCRIPT 6
write_file("core/analyzer_clientes.py", """import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class AnalizadorClientes:
    def analyze(self, parsed_data: Dict) -> Dict:
        try:
            df = parsed_data.get("data")
            if df is None or df.empty:
                return {"status": "error", "error": "Datos vacios"}
            df = df.copy()
            total_registros = len(df)
            precio = pd.to_numeric(df.get("precio_venta", 0), errors="coerce").fillna(0)
            cantidad = pd.to_numeric(df.get("cantidad", 0), errors="coerce").fillna(0)
            total_ventas = float((precio * cantidad).sum())
            promedio = total_ventas / total_registros if total_registros > 0 else 0
            segmentos = {}
            if "sucursal" in df.columns:
                for suc in df["sucursal"].dropna().unique():
                    df_suc = df[df["sucursal"] == suc]
                    p = pd.to_numeric(df_suc["precio_venta"], errors="coerce").fillna(0)
                    q = pd.to_numeric(df_suc["cantidad"], errors="coerce").fillna(0)
                    segmentos[str(suc)] = {"registros": len(df_suc), "total_ventas": float((p * q).sum())}
            return {"status": "success", "total_registros": total_registros, "total_ventas": round(total_ventas, 2), "promedio_por_registro": round(promedio, 2), "segmentos": segmentos}
        except Exception as e:
            logger.error(f"Error en analisis de clientes: {e}")
            return {"status": "error", "error": str(e)}


def run():
    logger.info("AnalizadorClientes configurado correctamente")
    return {"status": "configured", "module": "AnalizadorClientes"}
""")

# SCRIPT 7
write_file("core/analyzer_tendencias.py", """import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class AnalizadorTendencias:
    def analyze(self, parsed_data: Dict) -> Dict:
        try:
            df = parsed_data.get("data")
            if df is None or df.empty:
                return {"status": "error", "error": "Datos vacios"}
            df = df.copy()
            precio = pd.to_numeric(df.get("precio_venta", 0), errors="coerce").fillna(0)
            cantidad = pd.to_numeric(df.get("cantidad", 0), errors="coerce").fillna(0)
            total_ventas = float((precio * cantidad).sum())
            transacciones = len(df)
            promedio_precio = float(precio.mean())
            promedio_cantidad = float(cantidad.mean())
            distribucion = {}
            if "producto" in df.columns:
                for prod in df["producto"].dropna().unique():
                    count = int((df["producto"] == prod).sum())
                    distribucion[str(prod)] = {"frecuencia": count, "porcentaje": round(count / transacciones * 100, 2)}
            if transacciones > 1:
                mid = transacciones // 2
                primera_mitad = float((precio[:mid] * cantidad[:mid]).mean())
                segunda_mitad = float((precio[mid:] * cantidad[mid:]).mean())
                if segunda_mitad > primera_mitad * 1.05:
                    tendencia = "creciente"
                elif segunda_mitad < primera_mitad * 0.95:
                    tendencia = "decreciente"
                else:
                    tendencia = "estable"
            else:
                tendencia = "sin_datos_suficientes"
            return {"status": "success", "total_ventas": round(total_ventas, 2), "transacciones": transacciones, "promedio_precio": round(promedio_precio, 2), "promedio_cantidad": round(promedio_cantidad, 2), "tendencia": tendencia, "distribucion_productos": distribucion}
        except Exception as e:
            logger.error(f"Error en analisis de tendencias: {e}")
            return {"status": "error", "error": str(e)}


def run():
    logger.info("AnalizadorTendencias configurado correctamente")
    return {"status": "configured", "module": "AnalizadorTendencias"}
""")

# SCRIPT 8
write_file("validators/triple_validator.py", """import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TripleValidator:
    def validate(self, results: Dict) -> Dict:
        try:
            validaciones = {"capa_1_tipos_datos": True, "capa_2_reglas_negocio": True, "capa_3_anomalias": True}
            detalles = []
            for key, value in results.items():
                if isinstance(value, dict) and value.get("status") == "error":
                    validaciones["capa_1_tipos_datos"] = False
                    detalles.append(f"Capa 1 FALLO: {key} retorno error: {value.get('error')}")
            ventas = results.get("ventas", {})
            if isinstance(ventas, dict):
                total = ventas.get("total_ventas", 0)
                if total < 0:
                    validaciones["capa_2_reglas_negocio"] = False
                    detalles.append("Capa 2 FALLO: Total ventas negativo")
            rentabilidad = results.get("rentabilidad", {})
            if isinstance(rentabilidad, dict):
                margen = rentabilidad.get("margen_promedio_porcentaje", 0)
                if margen < -100 or margen > 1000:
                    validaciones["capa_2_reglas_negocio"] = False
                    detalles.append(f"Capa 2 FALLO: Margen fuera de rango ({margen}%)")
            auditoria = results.get("auditoria", {})
            if isinstance(auditoria, dict):
                anomalias = auditoria.get("anomalias_detectadas", 0)
                if anomalias > 5:
                    validaciones["capa_3_anomalias"] = False
                    detalles.append(f"Capa 3 ALERTA: {anomalias} anomalias detectadas")
            todas_pasan = all(validaciones.values())
            return {"status": "success", "validaciones": validaciones, "todas_pasan": todas_pasan, "capas_verificadas": 3, "detalles": detalles, "nivel_confianza": "ALTO" if todas_pasan else "MEDIO" if sum(validaciones.values()) >= 2 else "BAJO"}
        except Exception as e:
            logger.error(f"Error en triple validacion: {e}")
            return {"status": "error", "error": str(e)}


def run():
    logger.info("TripleValidator configurado correctamente")
    return {"status": "configured", "module": "TripleValidator"}
""")

# SCRIPT 9
write_file("validators/confidence_badge.py", """import logging
from typing import Dict

logger = logging.getLogger(__name__)


class ConfidenceBadge:
    def calculate(self, results: Dict, validation: Dict) -> Dict:
        try:
            score = 100.0
            validaciones = validation.get("validaciones", {})
            for capa, passed in validaciones.items():
                if not passed:
                    score -= 20
            for key, value in results.items():
                if isinstance(value, dict) and value.get("status") == "error":
                    score -= 15
            auditoria = results.get("auditoria", {})
            if isinstance(auditoria, dict):
                anomalias = auditoria.get("anomalias_detectadas", 0)
                score -= anomalias * 5
            score = max(score, 0)
            if score >= 80:
                badge, emoji, descripcion = "ALTO", "verde", "Datos confiables, analisis robusto"
            elif score >= 60:
                badge, emoji, descripcion = "MEDIO", "amarillo", "Datos aceptables, revisar anomalias"
            else:
                badge, emoji, descripcion = "BAJO", "rojo", "Datos con problemas, revision manual necesaria"
            return {"status": "success", "score": round(score, 2), "badge": badge, "nivel": emoji, "descripcion": descripcion, "confianza": badge}
        except Exception as e:
            logger.error(f"Error calculando confianza: {e}")
            return {"status": "error", "score": 0, "badge": "ERROR", "error": str(e)}


def run():
    logger.info("ConfidenceBadge configurado correctamente")
    return {"status": "configured", "module": "ConfidenceBadge"}
""")

# SCRIPT 10
write_file("api/main.py", """from fastapi import FastAPI
import uvicorn
import logging
from datetime import datetime
from pathlib import Path

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", handlers=[logging.FileHandler("logs/mvn_system.log"), logging.StreamHandler()])
logger = logging.getLogger("MVN-API")

mini_app = FastAPI(title="MVN Analytics API", version="2.0.0")

@mini_app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@mini_app.get("/")
async def root():
    return {"message": "MVN Analytics API v2.0.0", "status": "operational"}

if __name__ == "__main__":
    Path("uploads").mkdir(exist_ok=True)
    uvicorn.run(mini_app, host="0.0.0.0", port=8000)
""")

# SCRIPT 11
write_file("api/report_generator.py", """import json
import logging
from datetime import datetime
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportGenerator:
    def generate(self, results: Dict, confidence: Dict = None) -> Dict:
        try:
            report = {"resumen_ejecutivo": {"fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "analisis_realizados": list(results.keys()), "estado_general": self._get_estado(results)}, "resultados": {}, "confianza": confidence or {}, "recomendaciones": self._get_recommendations(results)}
            if "ventas" in results and results["ventas"].get("status") == "success":
                v = results["ventas"]
                report["resultados"]["ventas"] = {"total": v.get("total_ventas", 0), "transacciones": v.get("transacciones", 0), "ticket_promedio": v.get("ticket_promedio", 0)}
            if "rentabilidad" in results and results["rentabilidad"].get("status") == "success":
                r = results["rentabilidad"]
                report["resultados"]["rentabilidad"] = {"margen_total": r.get("total_margen", 0), "margen_porcentaje": r.get("margen_promedio_porcentaje", 0), "productos_en_perdida": r.get("productos_con_perdida", 0)}
            if "auditoria" in results and results["auditoria"].get("status") == "success":
                a = results["auditoria"]
                report["resultados"]["auditoria"] = {"anomalias": a.get("anomalias_detectadas", 0), "filas_totales": a.get("filas_totales", 0), "confianza": a.get("confianza_auditoria", 0)}
            return {"status": "success", "report": report}
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return {"status": "error", "error": str(e)}

    def save_report(self, report: Dict, output_dir: str = "results") -> str:
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"{output_dir}/report_{timestamp}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Reporte guardado: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
            return ""

    def _get_estado(self, results):
        errors = sum(1 for v in results.values() if isinstance(v, dict) and v.get("status") == "error")
        total = len(results)
        if errors == 0:
            return "completado_exitosamente"
        elif errors < total:
            return "completado_parcialmente"
        return "fallido"

    def _get_recommendations(self, results):
        recs = []
        ventas = results.get("ventas", {})
        if isinstance(ventas, dict) and ventas.get("status") == "success":
            recs.append("Revisar top productos para optimizar inventario")
        rentabilidad = results.get("rentabilidad", {})
        if isinstance(rentabilidad, dict) and rentabilidad.get("status") == "success":
            if rentabilidad.get("productos_con_perdida", 0) > 0:
                recs.append("URGENTE: Existen productos generando perdida, revisar precios")
        auditoria = results.get("auditoria", {})
        if isinstance(auditoria, dict) and auditoria.get("status") == "success":
            if auditoria.get("anomalias_detectadas", 0) > 0:
                recs.append("Corregir anomalias detectadas antes del siguiente analisis")
        if not recs:
            recs.append("Datos en buen estado, continuar con monitoreo regular")
        return recs


def run():
    logger.info("ReportGenerator configurado correctamente")
    return {"status": "configured", "module": "ReportGenerator"}
""")

print("="*50)
print("  11/11 SCRIPTS CREADOS OK")
print("="*50)
