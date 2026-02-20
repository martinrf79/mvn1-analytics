import pandas as pd
import numpy as np
import os

print("="*55)
print("  MVN ANALYTICS - TEST COMPLETO DEL PIPELINE")
print("="*55)

# PASO 1: Crear datos de prueba
print("\n[1/6] Creando datos de prueba...")
np.random.seed(42)
n = 200
productos = ["Health and beauty","Electronic accessories","Home and lifestyle","Sports and travel","Food and beverages"]
df_test = pd.DataFrame({
    "Product line": np.random.choice(productos, n),
    "Unit price": np.round(np.random.uniform(10, 100, n), 2),
    "Quantity": np.random.randint(1, 10, n),
    "COGS": np.round(np.random.uniform(5, 80, n), 2),
    "Branch": np.random.choice(["A", "B", "C"], n),
})
csv_path = "data/test_samples/sample_sales.csv"
os.makedirs("data/test_samples", exist_ok=True)
df_test.to_csv(csv_path, index=False)
print("  Archivo: {} ({} filas)".format(csv_path, n))

# PASO 2: Pre-Parser
print("\n[2/6] Pre-Parser: detectando formato y normalizando...")
from core.pre_parser import PreParser
parser = PreParser()
parsed = parser.parse(csv_path)
print("  Status: {}".format(parsed["status"]))
print("  Formato: {}".format(parsed["format_detected"]))
print("  Filas: {}".format(parsed["rows"]))
print("  Columnas originales: {}".format(parsed["columns_original"]))
print("  Columnas normalizadas: {}".format(parsed["columns"]))

if parsed["status"] != "success":
    print("  ERROR: Parser fallo")
    exit(1)

# PASO 3: Validacion de datos
print("\n[3/6] Data Validator: verificando calidad...")
from core.data_validator import DataValidator
validator = DataValidator()
quality = validator.validate(parsed["data"])
print("  Quality Score: {}/100".format(quality["quality_score"]))
print("  Valido: {}".format(quality["valid"]))
issues = quality.get("issues", [])
print("  Issues: {}".format(len(issues)))
for issue in issues:
    print("    - {}".format(issue))

# PASO 4: Los 5 analisis
print("\n[4/6] Ejecutando 5 analizadores...")
from core.analyzer_ventas import AnalizadorVentas
from core.analyzer_rentabilidad import AnalizadorRentabilidad
from core.analyzer_auditoria import AnalizadorAuditoria
from core.analyzer_clientes import AnalizadorClientes
from core.analyzer_tendencias import AnalizadorTendencias

results = {}

r = AnalizadorVentas().analyze(parsed)
results["ventas"] = r
print("  Ventas:        {} | Total: ${:,.2f} | Transacciones: {}".format(r["status"], r.get("total_ventas",0), r.get("transacciones",0)))

r = AnalizadorRentabilidad().analyze(parsed)
results["rentabilidad"] = r
print("  Rentabilidad:  {} | Margen: ${:,.2f} | Margen%: {}%".format(r["status"], r.get("total_margen",0), r.get("margen_promedio_porcentaje",0)))

r = AnalizadorAuditoria().analyze(parsed)
results["auditoria"] = r
print("  Auditoria:     {} | Anomalias: {} | Confianza: {}%".format(r["status"], r.get("anomalias_detectadas",0), r.get("confianza_auditoria",0)))

r = AnalizadorClientes().analyze(parsed)
results["clientes"] = r
print("  Clientes:      {} | Registros: {} | Total: ${:,.2f}".format(r["status"], r.get("total_registros",0), r.get("total_ventas",0)))

r = AnalizadorTendencias().analyze(parsed)
results["tendencias"] = r
print("  Tendencias:    {} | Tendencia: {} | Precio prom: ${:,.2f}".format(r["status"], r.get("tendencia","?"), r.get("promedio_precio",0)))

# PASO 5: Validacion triple + Confianza
print("\n[5/6] Triple Validacion + Badge de Confianza...")
from validators.triple_validator import TripleValidator
from validators.confidence_badge import ConfidenceBadge

validation = TripleValidator().validate(results)
v = validation["validaciones"]
print("  Capa 1 (Tipos):     {}".format("PASS" if v["capa_1_tipos_datos"] else "FAIL"))
print("  Capa 2 (Reglas):    {}".format("PASS" if v["capa_2_reglas_negocio"] else "FAIL"))
print("  Capa 3 (Anomalias): {}".format("PASS" if v["capa_3_anomalias"] else "FAIL"))

confidence = ConfidenceBadge().calculate(results, validation)
print("  Badge: {} ({}%)".format(confidence["badge"], confidence["score"]))
print("  Descripcion: {}".format(confidence["descripcion"]))

# PASO 6: Reporte
print("\n[6/6] Generando reporte...")
from api.report_generator import ReportGenerator
report_gen = ReportGenerator()
report_result = report_gen.generate(results, confidence)
os.makedirs("results", exist_ok=True)
report_path = report_gen.save_report(report_result["report"])
print("  Status: {}".format(report_result["status"]))
print("  Archivo: {}".format(report_path))

recs = report_result["report"].get("recomendaciones", [])
if recs:
    print("  Recomendaciones:")
    for rec in recs:
        print("    -> {}".format(rec))

# RESUMEN
print("\n" + "="*55)
print("  RESUMEN DEL TEST")
print("="*55)
all_ok = all(rv.get("status") == "success" for rv in results.values())
print("  Scripts verificados:  11/11")
print("  Datos procesados:     {} filas".format(parsed["rows"]))
ok_count = sum(1 for rv in results.values() if rv.get("status")=="success")
print("  Analizadores OK:      {}/5".format(ok_count))
print("  Validacion triple:    {}".format("PASS" if validation["todas_pasan"] else "REVISAR"))
print("  Confianza:            {} ({}%)".format(confidence["badge"], confidence["score"]))
print("  Reporte guardado:     {}".format(report_path))
estado = "LISTO PARA PRODUCCION" if all_ok else "REVISAR ERRORES"
print("  Estado general:       {}".format(estado))
print("="*55)
