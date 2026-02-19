"""
API FastAPI MVN - Servidor principal
Reemplaza Google Colab, accesible desde celular
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import uuid
import asyncio
from datetime import datetime
from typing import Optional
import json
import traceback
import logging
from pathlib import Path

# Importar módulos de análisis
try:
    from core.pre_parser import PreParser
    from core.data_validator import DataValidator
    from core.analyzer_ventas import AnalizadorVentas
    from core.analyzer_rentabilidad import AnalizadorRentabilidad
    from core.analyzer_auditoria import AnalizadorAuditoria
except ImportError as e:
    print(f"⚠️ Import error: {e}")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/mvn_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MVN-API')

# FastAPI app
app = FastAPI(
    title="MVN Analytics API",
    description="Sistema de análisis de datos para supermercados",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado global
system_state = {
    "status": "healthy",
    "last_check": None,
    "total_analyses": 0,
    "failed_analyses": 0,
    "uptime_start": datetime.now().isoformat(),
    "active_jobs": {},
    "error_log": []
}


@app.get("/health")
async def health_check():
    """Health check para Railway/Render"""
    try:
        system_state["last_check"] = datetime.now().isoformat()
        system_state["status"] = "healthy"
        
        return {
            "status": "healthy",
            "timestamp": system_state["last_check"],
            "total_analyses": system_state["total_analyses"],
            "failed_analyses": system_state["failed_analyses"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "error": str(e)}
        )


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "nombre": "MVN Analytics API",
        "version": "1.0.0",
        "estado": system_state["status"],
        "endpoints": {
            "/health": "Health check",
            "/upload": "Subir archivo (POST)",
            "/status/{job_id}": "Estado del análisis",
            "/results/{job_id}": "Obtener resultados"
        }
    }


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    modo: str = "completo"
):
    """
    Sube un archivo y ejecuta análisis
    
    Modos: ventas, rentabilidad, auditoria, completo
    """
    job_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.info(f"[JOB-{job_id}] Archivo recibido: {file.filename} | Modo: {modo}")
    
    # Crear directorios
    os.makedirs(f"uploads/{job_id}", exist_ok=True)
    os.makedirs(f"results/{job_id}", exist_ok=True)
    
    try:
        # Guardar archivo
        file_path = f"uploads/{job_id}/{file.filename}"
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"[JOB-{job_id}] Archivo guardado: {len(content)} bytes")
        
        # Registrar job
        system_state["active_jobs"][job_id] = {
            "status": "processing",
            "file": file.filename,
            "modo": modo,
            "created_at": timestamp,
            "progress": 0
        }
        
        # Ejecutar análisis en background
        asyncio.create_task(run_analysis(job_id, file_path, modo))
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": f"Análisis '{modo}' iniciado",
            "check_status_url": f"/status/{job_id}",
            "get_results_url": f"/results/{job_id}"
        }
        
    except Exception as e:
        logger.error(f"[JOB-{job_id}] Error: {e}")
        system_state["failed_analyses"] += 1
        
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


async def run_analysis(job_id: str, file_path: str, modo: str):
    """Ejecuta pipeline de análisis"""
    job = system_state["active_jobs"][job_id]
    
    try:
        system_state["total_analyses"] += 1
        
        # Paso 1: Pre-parsing
        job["progress"] = 20
        logger.info(f"[JOB-{job_id}] Pre-parsing...")
        
        parser = PreParser()
        parsed_data = parser.parse(file_path)
        
        if parsed_data.get('status') == 'error':
            raise Exception(f"Parse error: {parsed_data.get('error')}")
        
        # Paso 2: Validación
        job["progress"] = 40
        logger.info(f"[JOB-{job_id}] Validando datos...")
        
        validator = DataValidator()
        validation = validator.validate(parsed_data.get('data'))
        
        # Paso 3: Análisis según modo
        job["progress"] = 60
        results = {}
        
        if modo in ["ventas", "completo"]:
            logger.info(f"[JOB-{job_id}] Analizando ventas...")
            analyzer = AnalizadorVentas()
            results["ventas"] = analyzer.analyze(parsed_data)
        
        if modo in ["rentabilidad", "completo"]:
            logger.info(f"[JOB-{job_id}] Analizando rentabilidad...")
            analyzer = AnalizadorRentabilidad()
            results["rentabilidad"] = analyzer.analyze(parsed_data)
        
        if modo in ["auditoria", "completo"]:
            logger.info(f"[JOB-{job_id}] Ejecutando auditoría...")
            analyzer = AnalizadorAuditoria()
            results["auditoria"] = analyzer.analyze(parsed_data)
        
        # Agregar validación
        results["validation"] = validation
        
        # Guardar resultados
        job["progress"] = 90
        result_path = f"results/{job_id}/analysis_result.json"
        
        with open(result_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        job["status"] = "completed"
        job["progress"] = 100
        job["result_path"] = result_path
        
        logger.info(f"[JOB-{job_id}] ✅ Completado")
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        system_state["failed_analyses"] += 1
        
        logger.error(f"[JOB-{job_id}] ❌ Error: {e}")
        logger.error(traceback.format_exc())


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Obtener estado de un análisis"""
    job = system_state["active_jobs"].get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "file": job["file"],
        "modo": job["modo"]
    }


@app.get("/results/{job_id}")
async def get_results(job_id: str):
    """Obtener resultados de un análisis"""
    job = system_state["active_jobs"].get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=202,
            detail=f"Analysis still {job['status']}"
        )
    
    result_path = job.get("result_path")
    if not result_path or not os.path.exists(result_path):
        raise HTTPException(status_code=500, detail="Results not found")
    
    return FileResponse(result_path, media_type="application/json")


@app.get("/results/{job_id}/json")
async def get_results_json(job_id: str):
    """Obtener resultados como JSON"""
    job = system_state["active_jobs"].get(job_id)
    
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=404, detail="Results not ready")
    
    result_path = job.get("result_path")
    with open(result_path, "r") as f:
        return json.load(f)


if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False
    )
