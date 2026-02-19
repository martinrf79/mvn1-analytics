"""Script 4: ANALYZER RENTABILIDAD"""
import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AnalizadorRentabilidad:
    def analyze(self, parsed_data: Dict) -> Dict:
        try:
            df = parsed_data.get('data')
            if df is None or df.empty:
                return {'status': 'error', 'error': 'Datos vacíos'}
            
            df['margen_unitario'] = df['precio_venta'] - df['costo']
            df['margen_porcentaje'] = (df['margen_unitario'] / df['costo'] * 100).fillna(0)
            df['total_venta'] = df['precio_venta'] * df['cantidad']
            df['total_costo'] = df['costo'] * df['cantidad']
            df['total_margen'] = df['total_venta'] - df['total_costo']
            
            total_margen = df['total_margen'].sum()
            total_venta = df['total_venta'].sum()
            margen_promedio = (total_margen / total_venta * 100) if total_venta > 0 else 0
            
            productos_perdida = df[df['margen_unitario'] < 0]
            num_perdidas = len(productos_perdida)
            total_perdida = productos_perdida['total_margen'].sum()
            
            top_rentables = df.nlargest(5, 'margen_porcentaje')[['producto', 'margen_unitario']].to_dict('records') if 'producto' in df.columns else []
            
            return {
                'status': 'success',
                'total_venta': float(total_venta),
                'total_costo': float(df['total_costo'].sum()),
                'total_margen': float(total_margen),
                'margen_promedio_porcentaje': float(margen_promedio),
                'productos_con_perdida': int(num_perdidas),
                'total_perdida': float(total_perdida),
                'top_rentables': top_rentables[:5]
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

def run():
    logger.info("✅ AnalizadorRentabilidad configurado")
    return {'status': 'configured'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
