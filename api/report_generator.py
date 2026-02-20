import json
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
