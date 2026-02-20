import sys

print("Actualizando app.py...")

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Agregar import
old = "from core.pre_parser import PreParser"
new = "from core.pre_parser import PreParser\nfrom core.pre_analyzer import PreAnalyzer"

if "PreAnalyzer" not in content:
    content = content.replace(old, new)

    # Agregar instancia
    content = content.replace("parser = PreParser()", "parser = PreParser()\npre_analyzer = PreAnalyzer()")

    # Agregar fallback en upload
    old_parse = """        parsed = parser.parse(str(upload_path))
        if parsed["status"] != "success":
            raise ValueError("Error parseando: {}".format(parsed.get("error", "Unknown")))"""

    new_parse = """        parsed = parser.parse(str(upload_path))
        if parsed["status"] != "success" or parsed.get("rows", 0) == 0:
            logger.info("[{}] PreParser fallo, usando PreAnalyzer...".format(job_id))
            parsed = pre_analyzer.analyze_and_fix(str(upload_path))
            if parsed["status"] != "success":
                raise ValueError("Error parseando: {}".format(parsed.get("error", "Unknown")))
            logger.info("[{}] PreAnalyzer OK: {} filas".format(job_id, parsed.get("rows", 0)))"""

    content = content.replace(old_parse, new_parse)

    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("  app.py actualizado con PreAnalyzer")
else:
    print("  PreAnalyzer ya estaba en app.py")

print("LISTO")
