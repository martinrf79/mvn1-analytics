# ⚡ INICIO RÁPIDO - Comienza AHORA (5 minutos)

## 🎯 Tu Objetivo Hoy

Validar que TODO funciona en tu PC **antes** de deployar a celular.

---

## 📋 Únicamente Necesitas Hacer Esto

### 1️⃣ Terminal (Abre terminal/PowerShell)

```bash
cd /home/claude/mvn1-analytics
```

### 2️⃣ Crea venv

```bash
python -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate
```

### 3️⃣ Instala dependencias

```bash
pip install -r requirements.txt
```

### 4️⃣ Inicia servidor

```bash
python -m uvicorn api.main:app --reload
```

**Deberías ver:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 5️⃣ Abre navegador (OTRA TERMINAL)

```bash
http://localhost:8000
```

---

## ✅ Si Ves JSON = ¡FUNCIONA!

Si vez algo como:
```json
{
  "nombre": "MVN1 Analytics API",
  "version": "1.0.0",
  "estado": "healthy"
}
```

**¡EXCELENTE!** Sistema funcionando ✅

---

## 🧪 Ahora Prueba Subirlo Archivo

En terminal nueva (con venv activado):

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@tests/fixtures/supermarket_sales.csv" \
  -F "modo=completo"
```

**Resultado:**
```json
{
  "job_id": "abc123...",
  "status": "queued"
}
```

---

## 📊 Ahora Obtén Resultados

Copia el `job_id` y ejecuta:

```bash
curl http://localhost:8000/results/abc123.../json
```

**Deberías ver:**
```json
{
  "ventas": {
    "total_ventas": 50575.0,
    "transacciones": 16,
    "ticket_promedio": 3160.94,
    ...
  },
  "rentabilidad": {
    "total_margen": 24827.5,
    ...
  },
  ...
}
```

**¡SI RECIBES ESTO = SISTEMA FUNCIONA 100%!** ✅

---

## 🎉 Próximo Paso

Lee uno de estos documentos:

- **TESTING_ESCRITORIO.md** - Testing completo paso a paso (1 hora)
- **SETUP_AUTOMATICO.md** - Deploy a Railway (30 min)

---

## 🚨 Si Algo Falla

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error: "Port already in use"
```bash
python -m uvicorn api.main:app --reload --port 8001
```

### Error: "Cannot find file"
```bash
# Verifica que estés en la carpeta correcta
pwd
# Deberías ver: /home/claude/mvn1-analytics
```

---

## 📞 Resumen en 1 Minuto

```
cd mvn1-analytics
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

Luego abre: `http://localhost:8000`

**¡Y listo!** 🚀

---

**Vuelve aquí cuando termines**
