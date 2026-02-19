"""Script 3: ANALYZER VENTAS"""
import pandas as pd
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AnalizadorVentas:
    def analyze(self, parsed_data: Dict) -> Dict:
        try:
            df = parsed_data.get('data')
            if df is None or df.empty:
                return {'status': 'error', 'error': 'Datos vacíos'}
            
            df['total'] = df['precio_venta'] * df['cantidad']
            total_ventas = df['total'].sum()
            num_transacciones = len(df)
            
            ventas_categoria = {}
            if 'producto' in df.columns:
                for prod in df['producto'].unique():
                    df_prod = df[df['producto'] == prod]
                    ventas_categoria[str(prod)] = {
                        'total': float(df_prod['total'].sum()),
                        'transacciones': int(len(df_prod)),
                        'ticket_promedio': float(df_prod['total'].mean())
                    }
            
            ventas_sucursal = {}
            if 'sucursal' in df.columns:
                for sucursal in df['sucursal'].unique():
                    df_sucursal = df[df['sucursal'] == sucursal]
                    ventas_sucursal[str(sucursal)] = {
                        'total': float(df_sucursal['total'].sum()),
                        'transacciones': int(len(df_sucursal)),
                        'ticket_promedio': float(df_sucursal['total'].mean())
                    }
            
            top_productos = df.nlargest(5, 'total')[['producto', 'precio_venta', 'cantidad']].to_dict('records') if 'producto' in df.columns else []
            
            return {
                'status': 'success',
                'total_ventas': float(total_ventas),
                'transacciones': int(num_transacciones),
                'ticket_promedio': float(total_ventas / num_transacciones) if num_transacciones > 0 else 0,
                'ventas_por_categoria': ventas_categoria,
                'ventas_por_sucursal': ventas_sucursal,
                'top_productos': top_productos[:5]
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

def run():
    logger.info("✅ AnalizadorVentas configurado")
    return {'status': 'configured'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
