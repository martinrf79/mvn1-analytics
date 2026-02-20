import pandas as pd
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
