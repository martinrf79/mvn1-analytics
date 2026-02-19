"""Script 5: ANALYZER AUDITORIA"""
import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AnalizadorAuditoria:
    def analyze(self, parsed_data: Dict) -> Dict:
        try:
            df = parsed_data.get('data')
            if df is None or df.empty:
                return {'status': 'error', 'error': 'Datos vacíos'}
            
            anomalias = []
            nulls = df.isnull().sum().sum()
            if nulls > 0:
                anomalias.append(f"{nulls} valores nulos")
            
            dups = df.duplicated().sum()
            if dups > 0:
                anomalias.append(f"{dups} filas duplicadas")
            
            if 'precio_venta' in df.columns:
                negs = (df['precio_venta'] < 0).sum()
                if negs > 0:
                    anomalias.append(f"{negs} precios negativos")
            
            return {
                'status': 'success',
                'anomalias_detectadas': len(anomalias),
                'anomalias': anomalias,
                'filas_totales': len(df),
                'confianza_auditoria': max(100 - (len(anomalias) * 10), 0)
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

def run():
    logger.info("✅ AnalizadorAuditoria configurado")
    return {'status': 'configured'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
