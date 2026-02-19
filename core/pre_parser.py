"""
Script 1: PRE-PARSER - Convertidor Universal de Formatos
Detecta y convierte: CSV, JSON, TSV, TXT, Excel → CSV normalizado
"""

import pandas as pd
import json
import re
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PreParser:
    """Convertidor universal de formatos a CSV estándar"""
    
    STANDARD_COLUMNS = {
        'producto': str,
        'precio_venta': float,
        'cantidad': int,
        'costo': float,
        'sucursal': str
    }
    
    def parse(self, file_path: str) -> Dict:
        """Parse un archivo en cualquier formato"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.csv':
                return self._parse_csv(file_path)
            elif file_ext == '.json':
                return self._parse_json(file_path)
            elif file_ext in ['.txt', '']:
                return self._parse_txt(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                return self._parse_excel(file_path)
            else:
                return self._parse_csv(file_path)
                
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return {'status': 'error', 'error': str(e), 'format_detected': 'unknown'}
    
    def _parse_csv(self, file_path: str) -> Dict:
        """Parse CSV"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            normalized = self._normalize_columns(df)
            return {
                'data': normalized,
                'format_detected': 'csv',
                'rows': len(normalized),
                'columns': list(normalized.columns),
                'status': 'success'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'format_detected': 'csv'}
    
    def _parse_json(self, file_path: str) -> Dict:
        """Parse JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                raise ValueError("JSON debe ser lista de objetos o un objeto")
            
            normalized = self._normalize_columns(df)
            return {
                'data': normalized,
                'format_detected': 'json',
                'rows': len(normalized),
                'columns': list(normalized.columns),
                'status': 'success'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'format_detected': 'json'}
    
    def _parse_txt(self, file_path: str) -> Dict:
        """Parse TXT con formatos mixtos"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            records = []
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('-') or line.startswith('#'):
                    continue
                record = self._parse_line(line)
                if record:
                    records.append(record)
            
            if records:
                df = pd.DataFrame(records)
                normalized = self._normalize_columns(df)
                return {
                    'data': normalized,
                    'format_detected': 'txt',
                    'rows': len(normalized),
                    'columns': list(normalized.columns),
                    'status': 'success'
                }
            else:
                return {'status': 'error', 'error': 'No data found in TXT', 'format_detected': 'txt'}
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'format_detected': 'txt'}
    
    def _parse_excel(self, file_path: str) -> Dict:
        """Parse Excel"""
        try:
            df = pd.read_excel(file_path)
            normalized = self._normalize_columns(df)
            return {
                'data': normalized,
                'format_detected': 'excel',
                'rows': len(normalized),
                'columns': list(normalized.columns),
                'status': 'success'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'format_detected': 'excel'}
    
    def _parse_line(self, line: str) -> Optional[Dict]:
        """Parsea una línea"""
        record = {}
        patterns = [
            r'(\w+)\s*[=:]\s*([^\|,]+)',
            r'(\w+)\s+([^|,]+)',
        ]
        
        line = line.replace('€', '').replace('ñ', 'n').replace('é', 'e')
        
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            for part in parts:
                for pattern in patterns:
                    match = re.search(pattern, part)
                    if match:
                        key = match.group(1).lower().replace(' ', '_')
                        value = match.group(2).strip().replace('$', '')
                        record[key] = value
        
        elif ':' in line or '=' in line:
            for pattern in patterns:
                for match in re.finditer(pattern, line):
                    key = match.group(1).lower().replace(' ', '_')
                    value = match.group(2).strip().replace('$', '')
                    record[key] = value
        
        return record if record else None
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza nombres de columnas"""
        column_map = {
            'product line': 'producto', 'Product line': 'producto', 'PRODUCTO': 'producto',
            'unit price': 'precio_venta', 'Unit price': 'precio_venta', 'price': 'precio_venta',
            'quantity': 'cantidad', 'Quantity': 'cantidad', 'Qty': 'cantidad',
            'cogs': 'costo', 'costo': 'costo', 'Costo': 'costo', 'cost': 'costo',
            'branch': 'sucursal', 'Branch': 'sucursal', 'sucursal': 'sucursal', 'tienda': 'sucursal',
        }
        
        df.rename(columns=column_map, inplace=True)
        valid_cols = [col for col in df.columns if col in self.STANDARD_COLUMNS]
        if valid_cols:
            df = df[valid_cols]
        
        for col in df.columns:
            if col in self.STANDARD_COLUMNS:
                try:
                    if self.STANDARD_COLUMNS[col] == float:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    elif self.STANDARD_COLUMNS[col] == int:
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                except:
                    pass
        
        return df

def run():
    """Función requerida"""
    logger.info("✅ PreParser configurado")
    return {'status': 'configured'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
