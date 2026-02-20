import logging
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
