"""Script 9: CONFIDENCE BADGE"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class ConfidenceBadge:
    def calculate(self, results: Dict, validation: Dict) -> Dict:
        try:
            score = 100.0
            validation_result = validation.get('validaciones', {})
            for v in validation_result.values():
                if not v:
                    score -= 20
            score = max(score, 0)
            badge = "🟢 ALTO" if score >= 80 else "🟡 MEDIO" if score >= 60 else "🔴 BAJO"
            return {
                'score': score,
                'badge': badge,
                'confianza': 'ALTA' if score >= 80 else 'MEDIA' if score >= 60 else 'BAJA'
            }
        except Exception as e:
            return {'score': 0, 'badge': '❌ ERROR', 'error': str(e)}

def run():
    logger.info("✅ ConfidenceBadge configurado")
    return {'status': 'configured'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
