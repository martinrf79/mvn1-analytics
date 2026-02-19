# 🚀 SETUP AUTOMÁTICO - Deploy a Railway/Render

Después de completar `TESTING_ESCRITORIO.md`, sigue esta guía para deployar a celular.

## ⏱️ Tiempo Total: ~30 minutos

---

## PASO 1: Preparar Git (5 min)

```bash
# Entra a la carpeta
cd /home/claude/mvn1-analytics

# Configura Git (si es la primera vez)
git config --global user.email "tu-email@gmail.com"
git config --global user.name "Tu Nombre"

# Añade todos los archivos
git add .

# Crea primer commit
git commit -m "🚀 Inicial: MVN1 Analytics - Sistema completo con 11 scripts"

# Verifica commits
git log --oneline
```

**Resultado esperado:**
```
🚀 Inicial: MVN1 Analytics - Sistema completo con 11 scripts
```

---

## PASO 2: Crear Repositorio en GitHub (5 min)

1. Ve a https://github.com/new
2. **Repository name:** `mvn1-analytics`
3. **Description:** "Sistema de análisis para supermercados - Accesible desde celular"
4. **Public** (para GitHub Actions gratis)
5. **Create repository**

Obtendrás URL: `https://github.com/martinrf79/mvn1-analytics`

---

## PASO 3: Subir Código a GitHub (5 min)

En terminal (en la carpeta del proyecto):

```bash
# Añade el remoto
git remote add origin https://github.com/martinrf79/mvn1-analytics.git

# Cambia a rama main
git branch -M main

# Pushea el código
git push -u origin main

# Verifica en GitHub
# Ve a: https://github.com/martinrf79/mvn1-analytics
```

**Resultado esperado:**
- Código en GitHub
- Rama `main` visible
- Todos los archivos (.py, README.md, Dockerfile, etc)

---

## PASO 4: Deploy a Railway (5 min) - RECOMENDADO

Railway es MÁS fácil y MÁS rápido que Render.

### 4.1 Crear Cuenta en Railway

1. Ve a https://railway.app
2. Click "Login"
3. "Login with GitHub"
4. Autoriza acceso a tu GitHub
5. Selecciona tu organización

### 4.2 Crear Nuevo Proyecto

1. Click "+ New Project"
2. "Deploy from GitHub repo"
3. Autoriza Railway a acceder a GitHub
4. Selecciona: `martinrf79/mvn1-analytics`
5. Click "Deploy"

### 4.3 Esperar Deploy

Railway automáticamente:
1. Detecta el Dockerfile ✅
2. Instala dependencias ✅
3. Inicia el servidor ✅
4. Genera URL pública ✅

**Tiempo:** ~2-3 minutos

### 4.4 Obtener URL Pública

1. En dashboard de Railway
2. Click en tu servicio
3. En "Deployment"
4. Busca "Domains"
5. Copia URL: `https://mvn1-analytics-xxx.railway.app`

---

## PASO 5: Deploy a Render (5 min) - ALTERNATIVA

Si prefieres Render como alternativa:

### 5.1 Crear Cuenta en Render

1. Ve a https://render.com
2. Click "Get Started"
3. "Sign up with GitHub"
4. Autoriza acceso

### 5.2 Crear Web Service

1. Click "+ New" → "Web Service"
2. "Connect a repository"
3. Busca y selecciona: `mvn1-analytics`
4. Click "Connect"

### 5.3 Configurar Servicio

- **Name:** `mvn1-analytics`
- **Environment:** Docker
- **Region:** Deja por defecto
- **Branch:** main
- **Deja todo lo demás por defecto**

5. Click "Create Web Service"

### 5.4 Esperar Deploy

**Tiempo:** ~3-5 minutos

Obtén URL en el dashboard de Render.

---

## PASO 6: Probar en Celular (5 min)

Una vez que el deploy esté completo (Railway o Render):

### 6.1 Test 1: Health Check

Abre navegador del celular y ve a:
```
https://tu-url-publica/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-19T...",
  "total_analyses": 0
}
```

### 6.2 Test 2: Subir Archivo

En el celular:
1. Ve a `https://tu-url-publica`
2. Busca botón de "Upload"
3. Selecciona un archivo CSV
4. Click "Analizar"

**Resultado:** Recibiste JSON con análisis completo ✅

### 6.3 Test 3: Ver Resultados

El JSON debería incluir:
- `ventas` - Total ventas, transacciones, top productos
- `rentabilidad` - Márgenes, productos con pérdida
- `auditoria` - Anomalías detectadas
- `confianza` - Badge y score

---

## 🌐 URLs Públicas

Una vez deployado, tienes:

```
Railway:  https://mvn1-analytics-xxx.railway.app
Render:   https://mvn1-analytics-xxx.onrender.com
```

Ambas son accesibles desde:
- ✅ Navegador escritorio
- ✅ Navegador celular
- ✅ Apps móviles (Si haces wrapper)
- ✅ cURL, Postman, etc

---

## 📱 USO DESDE CELULAR

### Opción 1: Navegador

Abre en celular:
```
https://tu-url-publica
```

Flujo:
1. Home page con info
2. Upload file
3. Select from phone
4. Wait (≈8 segundos)
5. See results in JSON

### Opción 2: cURL (Si tienes terminal en celular)

```bash
# Upload
curl -X POST https://tu-url-publica/upload \
  -F "file=@archivo.csv" \
  -F "modo=completo"

# Get results
curl https://tu-url-publica/results/{job_id}/json
```

### Opción 3: App Nativa (Futuro)

Puedes crear:
- React Native app
- Flutter app
- SwiftUI app

Todas conectan a la misma API.

---

## 🔧 Monitoreo y Logs

### Railway

1. Dashboard → Tu servicio
2. "Logs" → Ver logs en tiempo real
3. "Metrics" → CPU, memoria, requests

### Render

1. Dashboard → Tu servicio
2. "Logs" → Ver logs en tiempo real

---

## 🐛 Solución de Problemas

### Error: "Build failed"

```
Solución: Revisa que el Dockerfile esté correcto
Ver: /home/claude/mvn1-analytics/Dockerfile
```

### Error: "Port 8000 already in use"

```
Railway/Render auto-detectan el puerto correcto
No es un problema
```

### Error: "ModuleNotFoundError"

```
Solución: Revisa requirements.txt tiene todas las dependencias
pip freeze > requirements.txt
git push
```

### El servidor inicia pero returns 500

```
Ve a Logs y busca el error específico
Copia el error completo y búscalo en Google
```

---

## ✅ CHECKLIST DEPLOY

- [ ] Código en GitHub (rama main)
- [ ] Dockerfile funciona localmente
- [ ] Deploy a Railway completado (o Render)
- [ ] URL pública obtenida
- [ ] Health check responde
- [ ] Upload desde celular funciona
- [ ] Resultados JSON recibidos

---

## 🎉 LISTO PARA PRODUCCIÓN

Si todos los checks están ✅, entonces:

```
✅ Sistema funciona en escritorio
✅ Sistema deployado en Railway/Render
✅ Sistema accesible desde celular
✅ Flujo cliente funciona completo

🚀 LISTO PARA USO EN PRODUCCIÓN
```

---

## 📚 Próximos Pasos

1. **Interface mejorada** - Crear UI HTML/CSS/JS
2. **App móvil** - React Native o Flutter
3. **Bases de datos** - Guardar resultados históricos
4. **Autenticación** - Login y sesiones
5. **Reportes PDF** - Exportar análisis a PDF

---

## 💬 Dudas Frecuentes

**¿Puedo cambiar la URL?**  
En Railway/Render → Settings → puedes cambiar el nombre del dominio

**¿Puedo usar mi dominio?**  
Sí, ambas soportan dominios custom (requiere configurar DNS)

**¿Cuánto cuesta?**  
- Railway: $5/mes (primeros $5 gratis)
- Render: Gratis con limitaciones (o $7/mes sin límites)

**¿Qué pasa si se cae?**  
Ambas tienen monitoring y alertas. Se reinicia automáticamente.

---

**¿Necesitas ayuda?** Contacta al soporte de Railway o Render
