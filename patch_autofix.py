print("Mejorando reglas de autofix...")

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

old_autofix = """def autofix_dataframe(df):
    if df is None or df.empty:
        return df
    df = df.copy()
    df = df.dropna(how="all")
    for col in ["precio_venta", "costo", "cantidad"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["precio_venta", "costo"]:
        if col in df.columns:
            mask = df[col] < 0
            if mask.any():
                df.loc[mask, col] = df.loc[mask, col].abs()
    if "cantidad" in df.columns:
        mask = df["cantidad"] <= 0
        if mask.any():
            df.loc[mask, "cantidad"] = 1
    for col in ["producto", "sucursal"]:
        if col in df.columns:
            df[col] = df[col].fillna("Sin datos")
    for col in ["precio_venta", "costo"]:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    return df"""

new_autofix = """def autofix_dataframe(df):
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

    # 11. Eliminar filas sin datos utiles
    if "precio_venta" in df.columns and "costo" in df.columns:
        mask = (df["precio_venta"] == 0) & (df["costo"] == 0)
        df = df[~mask]

    # 12. Eliminar duplicados exactos
    before = len(df)
    df = df.drop_duplicates()
    dupes = before - len(df)
    if dupes > 0:
        logger.info("AutoFix: {} duplicados eliminados".format(dupes))

    return df.reset_index(drop=True)"""

if old_autofix in content:
    content = content.replace(old_autofix, new_autofix)
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("OK - AutoFix mejorado con 12 reglas")
else:
    print("No se encontro el autofix original")
    print("Puede que ya este actualizado")
