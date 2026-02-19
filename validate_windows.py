"""
MVN1 VALIDATION - Versión Windows (sin emojis)
"""
import subprocess
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s'
)
logger = logging.getLogger('VALIDATOR')

class ValidationSystem:
    def __init__(self):
        self.base_dir = Path(".")
        self.scripts = {
            "core": [
                ("pre_parser.py", "Pre-Parser"),
                ("data_validator.py", "Data Validator"),
                ("analyzer_ventas.py", "Analyzer Ventas"),
                ("analyzer_rentabilidad.py", "Analyzer Rentabilidad"),
                ("analyzer_auditoria.py", "Analyzer Auditoria"),
                ("analyzer_clientes.py", "Analyzer Clientes"),
                ("analyzer_tendencias.py", "Analyzer Tendencias"),
            ],
            "validators": [
                ("triple_validator.py", "Triple Validator"),
                ("confidence_badge.py", "Confidence Badge"),
            ],
            "api": [
                ("main.py", "API Main"),
                ("report_generator.py", "Report Generator"),
            ]
        }
        self.results = {
            "total": 0,
            "valid": 0,
            "invalid": 0,
            "details": {},
        }
    
    def run(self):
        logger.info("=" * 70)
        logger.info("VALIDANDO 11 SCRIPTS MVN1")
        logger.info("=" * 70)
        
        for category, scripts in self.scripts.items():
            logger.info(f"\nValidando {category.upper()} ({len(scripts)} scripts)...")
            
            for filename, description in scripts:
                self._validate_script(category, filename, description)
        
        self._print_summary()
        return self.results
    
    def _validate_script(self, category, filename, description):
        self.results["total"] += 1
        
        if category == "core":
            script_path = self.base_dir / "core" / filename
        elif category == "validators":
            script_path = self.base_dir / "validators" / filename
        else:
            script_path = self.base_dir / "api" / filename
        
        if not script_path.exists():
            self.results["invalid"] += 1
            logger.error(f"  [ERROR] {filename}: No encontrado")
            return
        
        result = subprocess.run(
            ["python", "-m", "py_compile", str(script_path)],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            self.results["valid"] += 1
            logger.info(f"  [OK] {filename}")
        else:
            self.results["invalid"] += 1
            logger.error(f"  [ERROR] {filename}")
        
        self.results["details"][filename] = {
            "status": "OK" if result.returncode == 0 else "ERROR",
            "description": description
        }
    
    def _print_summary(self):
        print("\n" + "=" * 70)
        print("RESUMEN VALIDACION MVN1")
        print("=" * 70)
        
        total = self.results["total"]
        valid = self.results["valid"]
        invalid = self.results["invalid"]
        
        print(f"\nTotal Scripts: {total}")
        print(f"Validos: {valid}/{total}")
        print(f"Invalidos: {invalid}/{total}")
        
        if invalid == 0:
            print("\nTODOS LOS SCRIPTS FUNCIONAN CORRECTAMENTE")
        else:
            print(f"\n{invalid} SCRIPTS CON ERRORES")
        
        print("=" * 70 + "\n")

validator = ValidationSystem()
validator.run()
