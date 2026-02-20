from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import numpy as np
import uuid
import os
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict

from core.pre_parser import PreParser
from core.pre_analyzer import PreAnalyzer
from core.data_validator import DataValidator
from core.analyzer_ventas import AnalizadorVentas
from core.analyzer_rentabilidad import AnalizadorRentabilidad
from core.analyzer_auditoria import AnalizadorAuditoria
from core.analyzer_clientes import AnalizadorClientes
from core.analyzer_tendencias import AnalizadorTendencias
from validators.triple_validator import TripleValidator
from validators.confidence_badge import ConfidenceBadge
from api.report_generator import ReportGenerator

for d in ["logs", "uploads", "results"]:
    Path(d).mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()]
)
logger = logging.getLogger("MVN")

app = FastAPI(title="MVN Analytics", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

JOBS: Dict[str, Dict] = {}
parser = PreParser()
pre_analyzer = PreAnalyzer()
validator = DataValidator()
analyzer_ventas = AnalizadorVentas()
analyzer_rentabilidad = AnalizadorRentabilidad()
analyzer_auditoria = AnalizadorAuditoria()
analyzer_clientes = AnalizadorClientes()
analyzer_tendencias = AnalizadorTendencias()
triple_validator = TripleValidator()
confidence_badge = ConfidenceBadge()
report_generator = ReportGenerator()


def autofix_dataframe(df):
    if df is None or df.empty:
        return df
    df = df.copy()

    # 1. Eliminar filas y columnas vacias
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    # 2. Limpiar nombres de columnas
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    # 3. Mapeo inteligente de columnas
    column_map = {}
    aliases = {
        "producto": ["producto","product","product_line","item","articulo","descripcion","nombre","name","categoria","category"],
        "precio_venta": ["precio_venta","precio","price","unit_price","precio_unitario","valor","value","pvp","monto","amount","selling_price"],
        "cantidad": ["cantidad","quantity","qty","cant","unidades","units","count","piezas"],
        "costo": ["costo","cost","cogs","costo_unitario","unit_cost","precio_compra","gasto"],
        "sucursal": ["sucursal","branch","store","tienda","sede","local","location","ubicacion","oficina","city","ciudad"],
    }
    for std_name, alias_list in aliases.items():
        if std_name not in df.columns:
            for col in df.columns:
                if col in alias_list:
                    column_map[col] = std_name
                    break
    if column_map:
        df = df.rename(columns=column_map)
        logger.info("AutoFix: columnas mapeadas {}".format(column_map))

    # 4. Limpiar simbolos en numeros
    for col in ["precio_venta", "costo"]:
        if col in df.columns and df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace("$", "", regex=False)
            df[col] = df[col].str.replace(",", "", regex=False)
            df[col] = df[col].str.replace("EUR", "", regex=False)
            df[col] = df[col].str.strip()

    # 5. Convertir a numerico
    for col in ["precio_venta", "costo", "cantidad"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 6. Corregir negativos
    for col in ["precio_venta", "costo"]:
        if col in df.columns:
            mask = df[col] < 0
            if mask.any():
                df.loc[mask, col] = df.loc[mask, col].abs()

    # 7. Cantidad minima 1
    if "cantidad" in df.columns:
        mask = (df["cantidad"].isna()) | (df["cantidad"] <= 0)
        if mask.any():
            df.loc[mask, "cantidad"] = 1
        df["cantidad"] = df["cantidad"].astype(int)

    # 8. Rellenar texto faltante
    for col in ["producto", "sucursal"]:
        if col in df.columns:
            df[col] = df[col].fillna("Sin datos")
            df[col] = df[col].replace({"nan": "Sin datos", "": "Sin datos"})
        else:
            df[col] = "Sin datos"

    # 9. Rellenar numeros con mediana
    for col in ["precio_venta", "costo"]:
        if col in df.columns:
            median_val = df[col].median()
            if pd.notna(median_val):
                df[col] = df[col].fillna(median_val)
            else:
                df[col] = df[col].fillna(0)
        else:
            df[col] = 0.0

    if "cantidad" not in df.columns:
        df["cantidad"] = 1

    # 10. Eliminar filas basura (headers repetidos, separadores)
    if "producto" in df.columns:
        garbage = ["producto","product","item","nombre","---","===","***","nan","none"]
        mask = df["producto"].str.lower().str.strip().isin(garbage)
        df = df[~mask]

    # 11. Eliminar filas sin datos utiles (pero NUNCA eliminar todo)
    if "precio_venta" in df.columns and "costo" in df.columns:
        mask = (df["precio_venta"] == 0) & (df["costo"] == 0)
        if mask.any() and not mask.all():
            df = df[~mask]

    # 12. Eliminar duplicados exactos
    before = len(df)
    df = df.drop_duplicates()
    dupes = before - len(df)
    if dupes > 0:
        logger.info("AutoFix: {} duplicados eliminados".format(dupes))

    return df.reset_index(drop=True)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML


@app.get("/health")
async def health():
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "jobs_total": len(JOBS),
        "jobs_ok": sum(1 for j in JOBS.values() if j.get("status") == "completed")
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())[:8]
    try:
        upload_path = Path("uploads") / "{}_{}".format(job_id, file.filename)
        contents = await file.read()
        upload_path.write_bytes(contents)
        logger.info("[{}] Recibido: {} ({} bytes)".format(job_id, file.filename, len(contents)))

        parsed = parser.parse(str(upload_path))
        if parsed["status"] != "success" or parsed.get("rows", 0) == 0:
            logger.info("[{}] PreParser fallo, usando PreAnalyzer...".format(job_id))
            parsed = pre_analyzer.analyze_and_fix(str(upload_path))
            if parsed["status"] != "success":
                raise ValueError("Error parseando: {}".format(parsed.get("error", "Unknown")))
            logger.info("[{}] PreAnalyzer OK: {} filas".format(job_id, parsed.get("rows", 0)))

        df = parsed["data"]
        df_fixed = autofix_dataframe(df)
        quality = validator.validate(df_fixed)
        preview = df_fixed.head(20).fillna("").to_dict("records")

        JOBS[job_id] = {
            "status": "preview_ready",
            "filename": file.filename,
            "format": parsed["format_detected"],
            "rows": len(df_fixed),
            "columns": list(df_fixed.columns),
            "quality_score": quality.get("quality_score", 0),
            "issues": quality.get("issues", []),
            "data": df_fixed,
            "created_at": datetime.now().isoformat(),
        }

        return {
            "status": "success",
            "job_id": job_id,
            "file_info": {
                "filename": file.filename,
                "format": parsed["format_detected"],
                "rows": len(df_fixed),
                "columns": list(df_fixed.columns),
                "columns_original": parsed.get("columns_original", []),
            },
            "quality": {
                "score": quality.get("quality_score", 0),
                "valid": quality.get("valid", False),
                "issues": quality.get("issues", []),
            },
            "preview": preview,
        }
    except Exception as e:
        logger.error("[{}] Error: {}".format(job_id, e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/analyze/{job_id}")
async def run_analysis(job_id: str, analysis_type: str = Form(default="completo")):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    job = JOBS[job_id]
    start = time.time()
    try:
        df = job["data"]
        parsed_data = {"data": df, "status": "success"}
        results = {}
        analyzers = {
            "ventas": analyzer_ventas,
            "rentabilidad": analyzer_rentabilidad,
            "auditoria": analyzer_auditoria,
            "clientes": analyzer_clientes,
            "tendencias": analyzer_tendencias,
        }
        if analysis_type != "completo" and analysis_type in analyzers:
            analyzers = {analysis_type: analyzers[analysis_type]}
        elif analysis_type != "completo":
            raise HTTPException(status_code=400, detail="Tipo no valido")

        for key, az in analyzers.items():
            try:
                results[key] = az.analyze(parsed_data)
            except Exception as e:
                results[key] = {"status": "error", "error": str(e)}

        validation = triple_validator.validate(results)
        confidence = confidence_badge.calculate(results, validation)
        report_result = report_generator.generate(results, confidence)
        report_path = ""
        if report_result.get("status") == "success":
            report_path = report_generator.save_report(report_result["report"])

        duration = round(time.time() - start, 2)
        final = {
            "status": "completed",
            "job_id": job_id,
            "analysis_type": analysis_type,
            "duration": duration,
            "results": results,
            "validation": validation,
            "confidence": confidence,
            "report": report_result.get("report", {}),
            "report_file": report_path,
        }
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["result"] = final
        return final
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[{}] Error analisis: {}".format(job_id, e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/results/{job_id}")
async def get_results(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    job = JOBS[job_id]
    return {k: v for k, v in job.items() if k != "data"}


@app.get("/download/{job_id}")
async def download_report(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    result = JOBS[job_id].get("result", {})
    report = result.get("report", {})
    if not report:
        raise HTTPException(status_code=400, detail="No hay reporte")
    return JSONResponse(content=report, headers={"Content-Disposition": "attachment; filename=reporte_{}.json".format(job_id)})


@app.get("/system/check")
async def system_check():
    modules = {"PreParser": parser, "DataValidator": validator, "AnalizadorVentas": analyzer_ventas, "AnalizadorRentabilidad": analyzer_rentabilidad, "AnalizadorAuditoria": analyzer_auditoria, "AnalizadorClientes": analyzer_clientes, "AnalizadorTendencias": analyzer_tendencias, "TripleValidator": triple_validator, "ConfidenceBadge": confidence_badge, "ReportGenerator": report_generator}
    checks = {}
    for name, mod in modules.items():
        try:
            has_method = hasattr(mod, "parse") or hasattr(mod, "analyze") or hasattr(mod, "validate") or hasattr(mod, "calculate") or hasattr(mod, "generate")
            checks[name] = "OK" if has_method else "WARN"
        except Exception as e:
            checks[name] = "FAIL: {}".format(e)
    return {"status": "healthy", "modules": checks, "total": len(checks), "ok": sum(1 for v in checks.values() if v == "OK")}


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MVN Analytics</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;padding:16px}
.container{max-width:600px;margin:0 auto}
h1{text-align:center;font-size:1.5rem;margin-bottom:8px;color:#60a5fa}
.subtitle{text-align:center;color:#94a3b8;font-size:.85rem;margin-bottom:24px}
.card{background:#1e293b;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid #334155}
.card h2{font-size:1rem;color:#60a5fa;margin-bottom:12px}
.upload-area{border:2px dashed #475569;border-radius:12px;padding:32px 16px;text-align:center;cursor:pointer;transition:all .3s}
.upload-area:hover{border-color:#60a5fa;background:#1e3a5f}
.upload-area input{display:none}
.btn{display:block;width:100%;padding:14px;border:none;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;margin-top:12px;transition:all .3s}
.btn-primary{background:#2563eb;color:#fff}
.btn-primary:hover{background:#1d4ed8}
.btn-primary:disabled{background:#334155;color:#64748b;cursor:not-allowed}
.btn-success{background:#059669;color:#fff}
.status{padding:12px;border-radius:8px;margin-top:12px;font-size:.9rem}
.status-info{background:#1e3a5f;border:1px solid #2563eb}
.status-error{background:#450a0a;border:1px solid #dc2626}
.preview-table{width:100%;border-collapse:collapse;font-size:.75rem;margin-top:12px;display:block;overflow-x:auto}
.preview-table th{background:#334155;padding:8px 6px;text-align:left}
.preview-table td{padding:6px;border-bottom:1px solid #334155;white-space:nowrap}
.badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:.8rem;font-weight:600}
.badge-alto{background:#059669}
.badge-medio{background:#d97706}
.badge-bajo{background:#dc2626}
.result-section{margin-top:12px;padding:12px;background:#0f172a;border-radius:8px}
.result-section h3{font-size:.9rem;color:#60a5fa;margin-bottom:8px}
.result-item{display:flex;justify-content:space-between;padding:4px 0;font-size:.85rem}
.result-label{color:#94a3b8}
.result-value{color:#e2e8f0;font-weight:600}
.quality-bar{width:100%;height:8px;background:#334155;border-radius:4px;margin-top:8px;overflow:hidden}
.quality-fill{height:100%;border-radius:4px;transition:width .5s}
.loader{display:none;text-align:center;padding:20px}
.loader.active{display:block}
.spinner{width:40px;height:40px;border:4px solid #334155;border-top:4px solid #60a5fa;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 12px}
@keyframes spin{to{transform:rotate(360deg)}}
.analysis-options{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}
.analysis-option{padding:10px;background:#0f172a;border:1px solid #334155;border-radius:8px;text-align:center;cursor:pointer;font-size:.8rem;transition:all .2s}
.analysis-option:hover,.analysis-option.selected{border-color:#60a5fa;background:#1e3a5f}
.hidden{display:none}
#systemStatus{position:fixed;top:8px;right:8px;width:12px;height:12px;border-radius:50%;background:#059669}
</style>
</head>
<body>
<div id="systemStatus"></div>
<div class="container">
<h1>MVN Analytics</h1>
<p class="subtitle">Sistema de analisis de datos</p>

<div class="card" id="uploadCard">
<h2>1. Subir Archivo</h2>
<div class="upload-area" onclick="document.getElementById('fileInput').click()">
<input type="file" id="fileInput" accept=".csv,.json,.xlsx,.xls,.txt,.tsv">
<div style="font-size:2.5rem">📁</div>
<div style="color:#94a3b8;font-size:.9rem">Toca para seleccionar archivo</div>
<div style="color:#64748b;font-size:.75rem;margin-top:8px">CSV - Excel - JSON - TXT - TSV</div>
</div>
<div id="fileInfo" class="status status-info hidden"></div>
<button class="btn btn-primary" id="uploadBtn" disabled onclick="uploadFile()">Subir y Procesar</button>
</div>

<div class="loader" id="loader"><div class="spinner"></div><div id="loaderText">Procesando...</div></div>

<div class="card hidden" id="previewCard">
<h2>2. Datos Procesados</h2>
<div id="qualityInfo"></div>
<div style="overflow-x:auto;max-height:300px"><table class="preview-table" id="previewTable"></table></div>
<h2 style="margin-top:16px">Tipo de Analisis</h2>
<div class="analysis-options">
<div class="analysis-option selected" data-type="completo" onclick="selectAnalysis(this)"><div style="font-size:1.2rem">📊</div>Completo</div>
<div class="analysis-option" data-type="ventas" onclick="selectAnalysis(this)"><div style="font-size:1.2rem">💰</div>Ventas</div>
<div class="analysis-option" data-type="rentabilidad" onclick="selectAnalysis(this)"><div style="font-size:1.2rem">📈</div>Rentabilidad</div>
<div class="analysis-option" data-type="auditoria" onclick="selectAnalysis(this)"><div style="font-size:1.2rem">🔍</div>Auditoria</div>
<div class="analysis-option" data-type="clientes" onclick="selectAnalysis(this)"><div style="font-size:1.2rem">👥</div>Clientes</div>
<div class="analysis-option" data-type="tendencias" onclick="selectAnalysis(this)"><div style="font-size:1.2rem">📉</div>Tendencias</div>
</div>
<button class="btn btn-success" onclick="runAnalysis()">Ejecutar Analisis</button>
</div>

<div class="card hidden" id="resultsCard">
<h2>3. Resultados</h2>
<div id="confidenceBadge"></div>
<div id="resultsContent"></div>
<button class="btn btn-primary" onclick="downloadReport()" style="margin-top:16px">Descargar Reporte</button>
<button class="btn btn-primary" onclick="location.reload()" style="background:#475569;margin-top:8px">Nuevo Analisis</button>
</div>

<div class="card hidden" id="errorCard">
<h2>Error</h2>
<div id="errorContent" class="status status-error"></div>
<button class="btn btn-primary" onclick="location.reload()" style="margin-top:12px">Reintentar</button>
</div>
</div>

<script>
let currentJobId=null,selectedAnalysis="completo",selectedFile=null;
setInterval(async()=>{try{const r=await fetch("/health");const d=await r.json();document.getElementById("systemStatus").style.background=d.status==="operational"?"#059669":"#dc2626"}catch(e){document.getElementById("systemStatus").style.background="#dc2626"}},30000);
document.getElementById("fileInput").addEventListener("change",function(e){selectedFile=e.target.files[0];if(selectedFile){document.getElementById("fileInfo").textContent="📄 "+selectedFile.name+" ("+(selectedFile.size/1024).toFixed(1)+" KB)";document.getElementById("fileInfo").classList.remove("hidden");document.getElementById("uploadBtn").disabled=false}});
function selectAnalysis(el){document.querySelectorAll(".analysis-option").forEach(o=>o.classList.remove("selected"));el.classList.add("selected");selectedAnalysis=el.dataset.type}
async function uploadFile(){if(!selectedFile)return;showLoader("Procesando archivo...");document.getElementById("uploadCard").classList.add("hidden");const fd=new FormData();fd.append("file",selectedFile);try{const r=await fetch("/upload",{method:"POST",body:fd});if(!r.ok){const e=await r.json();throw new Error(e.detail||"Error")}const d=await r.json();currentJobId=d.job_id;showPreview(d)}catch(e){showError(e.message)}hideLoader()}
function showPreview(d){const s=d.quality.score;const c=s>=80?"#059669":s>=60?"#d97706":"#dc2626";document.getElementById("qualityInfo").innerHTML='<div class="result-item"><span class="result-label">Calidad</span><span class="result-value" style="color:'+c+'">'+s+'/100</span></div><div class="quality-bar"><div class="quality-fill" style="width:'+s+'%;background:'+c+'"></div></div><div class="result-item" style="margin-top:4px"><span class="result-label">Filas: '+d.file_info.rows+'</span><span class="result-label">Formato: '+d.file_info.format.toUpperCase()+'</span></div>'+(d.quality.issues.length>0?'<div class="status" style="background:#451a03;border:1px solid #d97706;margin-top:8px;font-size:.8rem">'+d.quality.issues.join("<br>")+"</div>":"");if(d.preview&&d.preview.length>0){const cols=Object.keys(d.preview[0]);let t="<thead><tr>"+cols.map(c=>"<th>"+c+"</th>").join("")+"</tr></thead><tbody>";d.preview.forEach(row=>{t+="<tr>"+cols.map(c=>"<td>"+(row[c]!=null?row[c]:"")+"</td>").join("")+"</tr>"});t+="</tbody>";document.getElementById("previewTable").innerHTML=t}document.getElementById("previewCard").classList.remove("hidden")}
async function runAnalysis(){if(!currentJobId)return;showLoader("Ejecutando analisis...");document.getElementById("previewCard").classList.add("hidden");const fd=new FormData();fd.append("analysis_type",selectedAnalysis);try{const r=await fetch("/analyze/"+currentJobId,{method:"POST",body:fd});if(!r.ok){const e=await r.json();throw new Error(e.detail||"Error")}const d=await r.json();showResults(d)}catch(e){showError(e.message)}hideLoader()}
function showResults(d){const c=d.confidence||{};const bc=(c.badge||"").toLowerCase();document.getElementById("confidenceBadge").innerHTML='<div style="text-align:center;margin-bottom:16px"><span class="badge badge-'+bc+'">Confianza: '+(c.badge||"N/A")+" ("+(c.score||0)+'%)</span><div style="color:#94a3b8;font-size:.8rem;margin-top:4px">'+(c.descripcion||"")+"</div></div>";let h="";const v=d.results||{};if(v.ventas&&v.ventas.status==="success"){const r=v.ventas;h+='<div class="result-section"><h3>💰 Ventas</h3><div class="result-item"><span class="result-label">Total</span><span class="result-value">$'+fmt(r.total_ventas)+'</span></div><div class="result-item"><span class="result-label">Transacciones</span><span class="result-value">'+r.transacciones+'</span></div><div class="result-item"><span class="result-label">Ticket Promedio</span><span class="result-value">$'+fmt(r.ticket_promedio)+"</span></div></div>"}if(v.rentabilidad&&v.rentabilidad.status==="success"){const r=v.rentabilidad;h+='<div class="result-section"><h3>📈 Rentabilidad</h3><div class="result-item"><span class="result-label">Margen Total</span><span class="result-value">$'+fmt(r.total_margen)+'</span></div><div class="result-item"><span class="result-label">Margen %</span><span class="result-value">'+r.margen_promedio_porcentaje+'%</span></div><div class="result-item"><span class="result-label">En Perdida</span><span class="result-value" style="color:'+(r.productos_con_perdida>0?"#dc2626":"#059669")+'">'+r.productos_con_perdida+"</span></div></div>"}if(v.auditoria&&v.auditoria.status==="success"){const r=v.auditoria;h+='<div class="result-section"><h3>🔍 Auditoria</h3><div class="result-item"><span class="result-label">Anomalias</span><span class="result-value">'+r.anomalias_detectadas+'</span></div><div class="result-item"><span class="result-label">Confianza</span><span class="result-value">'+r.confianza_auditoria+"%</span></div></div>"}if(v.tendencias&&v.tendencias.status==="success"){const r=v.tendencias;h+='<div class="result-section"><h3>📉 Tendencias</h3><div class="result-item"><span class="result-label">Tendencia</span><span class="result-value">'+r.tendencia+'</span></div><div class="result-item"><span class="result-label">Precio Prom</span><span class="result-value">$'+fmt(r.promedio_precio)+"</span></div></div>"}const vl=d.validation;if(vl&&vl.status==="success"){const vv=vl.validaciones;h+='<div class="result-section"><h3>Validacion Triple</h3><div class="result-item"><span class="result-label">Tipos</span><span class="result-value">'+(vv.capa_1_tipos_datos?"✅":"❌")+'</span></div><div class="result-item"><span class="result-label">Reglas</span><span class="result-value">'+(vv.capa_2_reglas_negocio?"✅":"❌")+'</span></div><div class="result-item"><span class="result-label">Anomalias</span><span class="result-value">'+(vv.capa_3_anomalias?"✅":"❌")+"</span></div></div>"}h+='<div class="result-item" style="margin-top:12px"><span class="result-label">Duracion</span><span class="result-value">'+d.duration+'s</span></div>';document.getElementById("resultsContent").innerHTML=h;document.getElementById("resultsCard").classList.remove("hidden")}
function downloadReport(){if(currentJobId)window.open("/download/"+currentJobId,"_blank")}
function showError(m){document.getElementById("errorContent").textContent=m;document.getElementById("errorCard").classList.remove("hidden")}
function showLoader(t){document.getElementById("loaderText").textContent=t;document.getElementById("loader").classList.add("active")}
function hideLoader(){document.getElementById("loader").classList.remove("active")}
function fmt(n){return(n||0).toLocaleString("es-AR",{minimumFractionDigits:2,maximumFractionDigits:2})}
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("="*50)
    print("  MVN Analytics v2.0")
    print("  http://localhost:8000")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
