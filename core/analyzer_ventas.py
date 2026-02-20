import pandas as pd
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
