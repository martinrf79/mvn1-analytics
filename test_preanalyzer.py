import os

print("="*50)
print("  TEST: Archivo desordenado con PreAnalyzer")
print("="*50)

from core.pre_analyzer import PreAnalyzer

# Crear archivo desordenado
os.makedirs("data/test_samples", exist_ok=True)
test_content = """REPORTE DE VENTAS - FORMATO INCONSISTENTE
================================================

producto: Widget A | precio: 150.50 | cantidad: 5 | costo: 100 | sucursal: Centro
Venta #2045: Laptop Dell | Precio_Venta=2500.00 | Qty=2 | Costo_Unitario=1800 | Tienda:Norte

SKU,PRODUCTO,PRECIO,CANTIDAD,COSTO,SUCURSAL
ABC001|Widget B|75.99|10|50.00|Sur

producto=Monitor Samsung | venta=3200 | cantidad=3 | costo=2000 | sucursal=Este

DATOS MIXTOS:
ProductoPrecioCantidadCostoTienda
Teclado Mecanico120.00870Oeste
Monitor LG350022100Centro

Datos sueltos:
Monitor ASUS - $2800 - 3 unidades - costo $1600 - sucursal Centro
Cable HDMI, 45.99, 20, 20, Sur
"""

with open("data/test_samples/datos_desordenados.txt", "w", encoding="utf-8") as f:
    f.write(test_content)

pa = PreAnalyzer()
result = pa.analyze_and_fix("data/test_samples/datos_desordenados.txt")

print("\nStatus: {}".format(result["status"]))
print("Filas: {}".format(result.get("rows", 0)))
print("Columnas: {}".format(result.get("columns", [])))

if result.get("fixes_applied"):
    print("\nFixes aplicados:")
    for fix in result["fixes_applied"]:
        print("  -> {}".format(fix))

if result["status"] == "success":
    df = result["data"]
    print("\nPreview:")
    print(df.to_string(index=False))

    print("\n\nProbando analizadores...")
    from core.analyzer_ventas import AnalizadorVentas
    from core.analyzer_rentabilidad import AnalizadorRentabilidad

    r = AnalizadorVentas().analyze(result)
    print("  Ventas: {} | Total: ${:,.2f}".format(r["status"], r.get("total_ventas", 0)))

    r = AnalizadorRentabilidad().analyze(result)
    print("  Rentabilidad: {} | Margen: ${:,.2f}".format(r["status"], r.get("total_margen", 0)))

    print("\nPREANALYZER FUNCIONA OK")
else:
    print("\nError: {}".format(result.get("error")))

print("="*50)
