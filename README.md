# 🚀 MVN1 Analytics - Sistema de Análisis para Supermercados

**MVN1** es un sistema de análisis de datos diseñado para funcionar completamente desde **celular**. Cliente sube archivo, sistema convierte, analiza y devuelve resultados en JSON.

## ✨ Características

✅ **Conversor Universal** - CSV, Excel, JSON, TXT desordenado  
✅ **7 Analizadores** - Ventas, rentabilidad, tendencias, clientes, auditoría  
✅ **2 Validadores** - Triple validación + confidence badges  
✅ **API REST** - FastAPI accesible desde celular  
✅ **Reporte Ejecutivo** - Recomendaciones accionables  
✅ **Docker Ready** - Railway/Render con 1 click  

## 🎯 Flujo de Uso (Cliente → Servidor → Resultados)

```
1. Cliente abre URL en celular
2. Selecciona archivo (cualquier formato)
3. Sistema convierte a formato estándar
4. Sistema valida calidad de datos
5. Sistema ejecuta 7 análisis en paralelo
6. Sistema valida resultados (triple validator)
7. Sistema asigna confianza (badges)
8. Cliente recibe JSON + recomendaciones

⏱️ TIEMPO TOTAL: ~8 segundos
```

## 📦 Los 11 Scripts

### **CORE - ANÁLISIS (7 scripts)**
- `pre_parser.py` - Conversor universal de formatos
- `data_validator.py` - Auditoría de calidad de datos
- `analyzer_ventas.py` - Análisis de ventas
- `analyzer_rentabilidad.py` - Cálculo de márgenes
- `analyzer_auditoria.py` - Detección de anomalías
- `analyzer_clientes.py` - Segmentación RFM
- `analyzer_tendencias.py` - Análisis de tendencias

### **VALIDATORS - CONFIANZA (2 scripts)**
- `triple_validator.py` - Validación en 3 capas
- `confidence_badge.py` - Sistema de badges

### **API & REPORTS (2 scripts)**
- `main.py` - Servidor FastAPI
- `report_generator.py` - Generador de reportes

## 🛠️ Instalación Local (Escritorio)

```bash
# 1. Clonar repo (cuando esté en GitHub)
git clone https://github.com/martinrf79/mvn1-analytics.git
cd mvn1-analytics

# 2. Crear virtual environment
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar servidor
python -m uvicorn api.main:app --reload

# 5. Abrir navegador
http://localhost:8000
```

## 🌐 Endpoints API

```
GET  /health                     - Health check
GET  /                          - Info del servidor
POST /upload                     - Subir archivo
GET  /status/{job_id}           - Estado del análisis
GET  /results/{job_id}/json     - Obtener resultados JSON
GET  /results/{job_id}/csv      - Descargar resultados CSV
```

### Ejemplo: Subir archivo

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@supermarket_sales.csv" \
  -F "modo=completo"

# Respuesta:
{
  "job_id": "a1b2c3d4",
  "status": "queued",
  "message": "Archivo recibido"
}
```

### Ejemplo: Obtener resultados

```bash
curl http://localhost:8000/results/a1b2c3d4/json

# Respuesta:
{
  "ventas": {
    "total_ventas": 322966.75,
    "transacciones": 1000,
    "ticket_promedio": 322.97,
    "top_5_productos": [...]
  },
  "rentabilidad": {
    "total_margen": 50200.00,
    "margen_promedio_pct": 15.54,
    "productos_con_perdida": [...]
  },
  ...
}
```

## 🚀 Deploy a Celular (Railway)

### Paso 1: Push a GitHub (5 min)

```bash
git add .
git commit -m "Inicial: MVN1 Analytics sistema completo"
git push origin main
```

### Paso 2: Deploy a Railway (5 min)

1. Ve a https://railway.app
2. Login con GitHub
3. "+ New Project" → "Deploy from GitHub repo"
4. Selecciona: `martinrf79/mvn1-analytics`
5. Click "Deploy"
6. Espera ~2 minutos
7. ¡Obtén URL pública!

### Paso 3: Acceder desde celular

Abre en navegador del celular:
```
https://tu-app-railway.app
```

¡El flujo es IDÉNTICO al escritorio!

## 🌐 Deploy a Render (Alternativa)

1. Ve a https://render.com
2. "+ New" → "Web Service"
3. "Connect a repository" → `mvn1-analytics`
4. Deja todas las configuraciones por defecto
5. Click "Create Web Service"
6. Espera ~3 minutos

URL: `https://mvn1-analytics-xxx.onrender.com`

## 📱 Uso desde Celular

### Opción 1: Navegador
1. Abre URL pública en navegador del celular
2. Sube archivo
3. Espera ~8 segundos
4. Recibe resultados en JSON

### Opción 2: App nativa (Futuro)
- Crear interface React Native
- Conectar a API
- Acceso offline con caché

## 🧪 Testing en Escritorio

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Test 2: Ver info
curl http://localhost:8000/

# Test 3: Subir archivo CSV
curl -X POST http://localhost:8000/upload \
  -F "file=@tests/fixtures/supermarket_sales.csv" \
  -F "modo=completo"

# Test 4: Ver resultados
curl http://localhost:8000/results/{job_id}/json
```

## 📊 Datos de Prueba Incluidos

En `tests/fixtures/`:
- `supermarket_sales.csv` - 1000 transacciones reales
- `datos_desordenados.txt` - Formato mixto para probar parser

## ⚙️ Configuración (Opcional)

Crear archivo `.env`:
```
DEBUG=False
LOG_LEVEL=INFO
MAX_FILE_SIZE=50MB
TIMEOUT=30
```

## 🔧 Solución de Problemas

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error: "Address already in use"
```bash
# Cambia el puerto
python -m uvicorn api.main:app --reload --port 8001
```

### Error: "Permission denied"
```bash
chmod +x main.py
python -m uvicorn api.main:app --reload
```

## 📚 Documentación Adicional

- `TESTING_ESCRITORIO.md` - Guía paso a paso para testing local
- `SETUP_AUTOMATICO.md` - Automatización de deploy
- `FLUJO_CLIENTE_FINAL.md` - Flujo completo del cliente

## 🤝 Contribuir

Este proyecto está en desarrollo activo. Las mejoras son bienvenidas.

## 📄 Licencia

MIT License - Libre para uso personal y comercial

---

**Preguntas o problemas?** Abre un issue en GitHub

**Versión:** 1.0.0  
**Última actualización:** 2026-02-19  
**Estado:** Ready for Production ✅
