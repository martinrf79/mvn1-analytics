"""Script 2: DATA VALIDATOR"""
import pandas as pd
import numpy as np
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self, min_confidence: float = 0.60):
        self.min_confidence = min_confidence
        self.issues = []
    
    def validate(self, df: pd.DataFrame) -> Dict:
        self.issues = []
        if df is None or df.empty:
            return {'quality_score': 0, 'valid': False, 'error': 'DataFrame vacío', 'issues': ['Datos vacíos']}
        
        try:
            duplicates = self._check_duplicates(df)
            nulls = self._check_nulls(df)
            ranges = self._check_ranges(df)
            types = self._check_types(df)
            quality_score = self._calculate_score(duplicates, nulls, ranges, types)
            
            return {
                'quality_score': quality_score,
                'valid': quality_score >= (self.min_confidence * 100),
                'duplicates': duplicates,
                'nulls': nulls,
                'ranges': ranges,
                'types': types,
                'issues': self.issues,
                'recommendations': self._get_recommendations()
            }
        except Exception as e:
            return {'quality_score': 0, 'valid': False, 'error': str(e)}
    
    def _check_duplicates(self, df: pd.DataFrame) -> Dict:
        total_rows = len(df)
        duplicates = df.duplicated().sum()
        pct = (duplicates / total_rows * 100) if total_rows > 0 else 0
        if duplicates > 0:
            self.issues.append(f"❌ {duplicates} filas duplicadas")
        return {'count': int(duplicates), 'percentage': float(pct)}
    
    def _check_nulls(self, df: pd.DataFrame) -> Dict:
        null_counts = df.isnull().sum()
        total_cells = len(df) * len(df.columns)
        total_nulls = null_counts.sum()
        pct = (total_nulls / total_cells * 100) if total_cells > 0 else 0
        if total_nulls > 0:
            self.issues.append(f"⚠️ {total_nulls} valores nulos")
        return {'total': int(total_nulls), 'percentage': float(pct)}
    
    def _check_ranges(self, df: pd.DataFrame) -> Dict:
        issues = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            if col in ['precio_venta', 'costo', 'cantidad']:
                negatives = (df[col] < 0).sum()
                if negatives > 0:
                    issues[col] = {'negative_values': int(negatives)}
                    self.issues.append(f"❌ Columna {col}: {negatives} negativos")
        return {'issues': issues}
    
    def _check_types(self, df: pd.DataFrame) -> Dict:
        type_checks = {}
        expected = {'producto': 'object', 'precio_venta': 'number', 'cantidad': 'number', 'costo': 'number', 'sucursal': 'object'}
        for col, exp in expected.items():
            if col not in df.columns:
                self.issues.append(f"⚠️ Columna faltante: {col}")
                type_checks[col] = {'status': 'MISSING'}
        return type_checks
    
    def _calculate_score(self, duplicates, nulls, ranges, types) -> float:
        score = 100.0
        score -= min(duplicates.get('percentage', 0), 20)
        score -= min(nulls.get('percentage', 0), 30)
        if ranges.get('issues'):
            score -= 15
        return max(score, 0.0)
    
    def _get_recommendations(self):
        recs = []
        if any('duplicadas' in i for i in self.issues):
            recs.append('🔧 Eliminar duplicados')
        if any('nulos' in i for i in self.issues):
            recs.append('🔧 Rellenar o eliminar nulos')
        return recs

def run():
    logger.info("✅ DataValidator configurado")
    return {'status': 'configured'}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
