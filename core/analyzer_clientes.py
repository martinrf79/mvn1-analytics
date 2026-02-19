"""Script 6: ANALYZER CLIENTES"""
import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AnalizadorClientes:
    def analyze(self, parsed_data: Dict) -> Dict:
        try:
            df = parsed_data.get('data')
            if df is None or df.empty:
                return {'status': 'error', 'error': 'Datos vacíos'}
            total_clientes = len(df)
            total_ventas = (df['precio_venta'] * df['cantidad']).sum()
            return {
                'status': 'success',
                'total_clientes': total_clientes,
                'total_ventas': float(total_ventas),
                'promedio_por_cliente': float(total_ventas / total_clientes) if total_clientes > 0 else 0
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

def run():
    logger.info("✅ AnalizadorClientes configurado")
    return {'status': 'configured'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
