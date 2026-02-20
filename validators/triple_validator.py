import logging
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
