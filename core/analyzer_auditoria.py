import pandas as pd
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
