import pandas as pd
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
