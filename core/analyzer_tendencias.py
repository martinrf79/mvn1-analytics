import pandas as pd
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
