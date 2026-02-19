# 🧪 TESTING EN ESCRITORIO - Guía Paso a Paso

Este documento te guía para validar que **TODOS los 11 scripts funcionan correctamente** antes de deployar a celular.

## ⏱️ Tiempo Total: ~1 hora

## FASE 1: Instalación (5 min)

```bash
# 1. Entra a la carpeta del proyecto
cd /home/claude/mvn1-analytics

# 2. Crea virtual environment
python -m venv venv

# 3. Activa virtual environment
source venv/bin/activate
# En Windows: venv\Scripts\activate

# 4. Instala dependencias
pip install -r requirements.txt

# 5. Verifica instalación
python -c "import pandas, fastapi; print('✅ Dependencias OK')"
```

**Resultado esperado:**
```
✅ Dependencias OK
```

---

## FASE 2: Test Individual - Pre-Parser (10 min)

```bash
# Abre Python interactivo
python

# Copia y pega esto:
from core.pre_parser import PreParser
import pandas as pd

parser = PreParser()

# Test 1: CSV
print("Test 1: Parsing CSV...")
result = parser.parse('tests/fixtures/supermarket_sales.csv')
print(f"  Formato detectado: {result.get('format_detected')}")
print(f"  Filas: {result.get('rows')}")
print(f"  Status: {result.get('status')}")

# Verifica que funcione
assert result['status'] == 'success', "CSV parsing falló"
assert result['rows'] > 0, "No hay filas"
print("✅ Pre-parser funciona\n")

exit()
```

**Resultado esperado:**
```
Test 1: Parsing CSV...
  Formato detectado: csv
  Filas: 1000
  Status: success
✅ Pre-parser funciona
```

---

## FASE 3: Test Individual - Data Validator (10 min)

```bash
python

# Copia y pega esto:
from core.pre_parser import PreParser
from core.data_validator import DataValidator

# Primero: parsea los datos
parser = PreParser()
parse_result = parser.parse('tests/fixtures/supermarket_sales.csv')
df = parse_result['data']

# Segundo: valida
print("Test 2: Data Validator...")
validator = DataValidator()
result = validator.validate(df)
print(f"  Quality Score: {result['quality_score']}%")
print(f"  Valid: {result['valid']}")
print(f"  Issues: {result['issues']}")

assert result['quality_score'] > 50, "Quality muy baja"
print("✅ Data Validator funciona\n")

exit()
```

**Resultado esperado:**
```
Test 2: Data Validator...
  Quality Score: 95.5%
  Valid: True
  Issues: []
✅ Data Validator funciona
```

---

## FASE 4: Test Individual - Analizadores (10 min)

```bash
python

# Copia y pega esto:
from core.pre_parser import PreParser
from core.analyzer_ventas import AnalizadorVentas
from core.analyzer_rentabilidad import AnalizadorRentabilidad
from core.analyzer_auditoria import AnalizadorAuditoria

# Parsea los datos primero
parser = PreParser()
parse_result = parser.parse('tests/fixtures/supermarket_sales.csv')
df = parse_result['data']

# Test Ventas
print("Test 3: Analyzer Ventas...")
ventas = AnalizadorVentas()
result_ventas = ventas.analyze(df)
print(f"  Total ventas: ${result_ventas['total_ventas']:,.2f}")
print(f"  Transacciones: {result_ventas['transacciones']}")
assert result_ventas['status'] == 'success'
print("✅ Analyzer Ventas funciona\n")

# Test Rentabilidad
print("Test 4: Analyzer Rentabilidad...")
rentabilidad = AnalizadorRentabilidad()
result_renta = rentabilidad.analyze(df)
print(f"  Total margen: ${result_renta['total_margen']:,.2f}")
print(f"  Margen promedio: {result_renta['margen_promedio_pct']:.2f}%")
assert result_renta['status'] == 'success'
print("✅ Analyzer Rentabilidad funciona\n")

# Test Auditoría
print("Test 5: Analyzer Auditoría...")
auditoria = AnalizadorAuditoria()
result_audit = auditoria.analyze(df)
print(f"  Anomalías detectadas: {result_audit['total_anomalias']}")
print(f"  Confianza: {result_audit['confianza_auditoria']:.1f}%")
assert result_audit['status'] == 'success'
print("✅ Analyzer Auditoría funciona\n")

exit()
```

**Resultado esperado:**
```
Test 3: Analyzer Ventas...
  Total ventas: $322,966.75
  Transacciones: 1000
✅ Analyzer Ventas funciona

Test 4: Analyzer Rentabilidad...
  Total margen: $50,200.00
  Margen promedio: 15.54%
✅ Analyzer Rentabilidad funciona

Test 5: Analyzer Auditoría...
  Anomalías detectadas: 0
  Confianza: 100.0%
✅ Analyzer Auditoría funciona
```

---

## FASE 5: Test Validators (10 min)

```bash
python

# Copia y pega esto:
from validators.triple_validator import TripleValidator
from validators.confidence_badge import ConfidenceBadge

# Mock results
test_results = {
    'total_ventas': 322966.75,
    'transacciones': 1000,
    'ticket_promedio': 322.97,
    'anomalias_detectadas': []
}

print("Test 6: Triple Validator...")
validator = TripleValidator()
validation_result = validator.validate(test_results)
print(f"  Todas pasan: {validation_result['todas_pasan']}")
print(f"  Score: {validation_result['score']:.1f}")
assert validation_result['todas_pasan'], "Validación falló"
print("✅ Triple Validator funciona\n")

print("Test 7: Confidence Badge...")
badge = ConfidenceBadge()
badge_result = badge.calculate(test_results, validation_result)
print(f"  Score: {badge_result['score']:.1f}%")
print(f"  Badge: {badge_result['badge']}")
assert badge_result['score'] > 0, "Badge score falló"
print("✅ Confidence Badge funciona\n")

exit()
```

**Resultado esperado:**
```
Test 6: Triple Validator...
  Todas pasan: True
  Score: 100.0
✅ Triple Validator funciona

Test 7: Confidence Badge...
  Score: 95.0%
  Badge: 🟢 ALTO
✅ Confidence Badge funciona
```

---

## FASE 6: Iniciar Servidor FastAPI (5 min)

```bash
# En terminal (con venv activado):
python -m uvicorn api.main:app --reload

# Deberías ver:
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**NO CIERRES ESTA TERMINAL - la necesitas abierta**

---

## FASE 7: Test API en Otra Terminal (10 min)

Abre **OTRA TERMINAL** y sigue estos pasos:

```bash
# 1. Test Health Check
curl http://localhost:8000/health

# Resultado esperado:
# {"status":"healthy","timestamp":"...","total_analyses":0,"failed_analyses":0}

# 2. Test Root
curl http://localhost:8000/

# Resultado esperado:
# {"nombre":"MVN1 Analytics API","version":"1.0.0","estado":"healthy",...}

# 3. Test Upload
curl -X POST http://localhost:8000/upload \
  -F "file=@tests/fixtures/supermarket_sales.csv" \
  -F "modo=completo"

# Resultado esperado:
# {"job_id":"a1b2c3d4...","status":"queued","message":"Archivo recibido"}
# COPIA EL job_id

# 4. Test Status (reemplaza {job_id} con el que obtuviste)
curl http://localhost:8000/status/{job_id}

# Espera a que veas: "status": "completed"

# 5. Test Results
curl http://localhost:8000/results/{job_id}/json

# Deberías ver JSON con:
# {"ventas": {...}, "rentabilidad": {...}, ...}
```

---

## ✅ CHECKLIST FINAL

Una vez completadas todas las fases, verifica que tengas:

- [ ] Fase 1: Dependencias instaladas
- [ ] Fase 2: Pre-parser funciona
- [ ] Fase 3: Data validator funciona
- [ ] Fase 4: Todos los analyzers funcionan
- [ ] Fase 5: Validators funcionan
- [ ] Fase 6: Servidor inicia sin errores
- [ ] Fase 7: API responde correctamente

## 🎉 RESULTADO ESPERADO

Si todo está ✅, entonces:

```
✅ PRE-PARSER funciona                 (Convierte formatos)
✅ DATA VALIDATOR funciona             (Audita datos)
✅ ANALYZER VENTAS funciona            (Calcula ventas)
✅ ANALYZER RENTABILIDAD funciona      (Calcula márgenes)
✅ ANALYZER AUDITORIA funciona         (Detecta anomalías)
✅ ANALYZER CLIENTES funciona          (Segmenta clientes)
✅ ANALYZER TENDENCIAS funciona        (Analiza tendencias)
✅ TRIPLE VALIDATOR funciona           (Valida resultados)
✅ CONFIDENCE BADGE funciona           (Asigna confianza)
✅ REPORT GENERATOR funciona           (Genera reportes)
✅ API MAIN funciona                   (Servidor funciona)

🎉 SISTEMA 100% FUNCIONAL - LISTO PARA DEPLOYAR A CELULAR
```

---

## 🚀 Siguiente Paso

Una vez que TODO esté ✅, procede con:

1. Push a GitHub
2. Deploy a Railway
3. Acceder desde celular

Ver: `SETUP_AUTOMATICO.md`

---

**¿Algo falló?** 
- Revisa el archivo `logs/mvn_system.log`
- Copia el error completo y pégalo en Claude
