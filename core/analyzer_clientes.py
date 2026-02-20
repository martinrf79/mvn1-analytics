import pandas as pd
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
