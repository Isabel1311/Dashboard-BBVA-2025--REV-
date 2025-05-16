# Este archivo usa Streamlit y debe ejecutarse localmente.
# Ejecuta en tu terminal: pip install streamlit
# Luego corre: streamlit run app.py


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Dashboard Mantenimiento Correctivo", layout="wide")

st.title("🔧 Dashboard de Mantenimiento Correctivo 2025")
archivo = st.file_uploader("Sube tu archivo Excel", type=[".xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip().str.upper()

    df["FECHA DE CREACIÓN"] = pd.to_datetime(df.get("FECHA DE CREACIÓN"), errors="coerce")
    df["IMPORTE"] = pd.to_numeric(df.get("IMPORTE"), errors="coerce")

    st.sidebar.header("Filtros")

    tipo_orden = []
    if "TIPO DE ORDEN" in df.columns:
        tipos_disponibles = df["TIPO DE ORDEN"].dropna().unique().tolist()
        valor_default = ["CORRECTIVO"] if "CORRECTIVO" in tipos_disponibles else []
        if tipos_disponibles:
            tipo_orden = st.sidebar.multiselect("Tipo de orden", tipos_disponibles, default=valor_default)
        else:
            st.sidebar.warning("⚠️ No hay tipos de orden disponibles en el archivo cargado.")
    else:
        st.sidebar.warning("⚠️ La columna 'TIPO DE ORDEN' no existe en el archivo cargado.")

    anios_disponibles = df["FECHA DE CREACIÓN"].dt.year.dropna().unique() if "FECHA DE CREACIÓN" in df.columns else []
    anio = st.sidebar.selectbox("Año", sorted(anios_disponibles, reverse=True), index=0)
    meses_disponibles = list(range(1, 13))
    meses = st.sidebar.multiselect("Mes(es)", meses_disponibles, default=[datetime.now().month])

    proveedores_disponibles = df["PROVEEDOR"].dropna().unique() if "PROVEEDOR" in df.columns else []
    proveedores = st.sidebar.multiselect("Proveedor", proveedores_disponibles)

    df_filtrado = df.copy()
    if "TIPO DE ORDEN" in df.columns and tipo_orden:
        df_filtrado = df_filtrado[df_filtrado["TIPO DE ORDEN"].isin(tipo_orden)]
    if "FECHA DE CREACIÓN" in df.columns:
        df_filtrado = df_filtrado[(df_filtrado["FECHA DE CREACIÓN"].dt.year == anio) & (df_filtrado["FECHA DE CREACIÓN"].dt.month.isin(meses))]
    if "PROVEEDOR" in df.columns and proveedores:
        df_filtrado = df_filtrado[df_filtrado["PROVEEDOR"].isin(proveedores)]

    if df_filtrado.empty:
        st.warning("⚠️ No hay datos para mostrar con los filtros seleccionados. Revisa el archivo y los criterios.")
    else:
        # --- KPIs ---
        st.subheader("📌 Indicadores clave del mes")
        total_ordenes = df_filtrado.shape[0]
        total_importe = df_filtrado["IMPORTE"].sum()
        proveedor_top = df_filtrado["PROVEEDOR"].value_counts().idxmax() if not df_filtrado.empty else "-"
        ordenes_prom = df_filtrado.shape[0] / df_filtrado["PROVEEDOR"].nunique() if df_filtrado["PROVEEDOR"].nunique() > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🗂 Total de Órdenes", f"{total_ordenes:,}")
        col2.metric("💰 Importe Total", f"${total_importe:,.0f}")
        col3.metric("🥇 Proveedor con Más Órdenes", proveedor_top)
        col4.metric("📊 Órdenes Promedio por Proveedor", f"{ordenes_prom:.2f}")

        st.subheader("📊 Recuento de Órdenes por Proveedor y Estatus")
        tabla_ordenes = pd.pivot_table(
            df_filtrado,
            index="PROVEEDOR",
            columns="ESTATUS DE USUARIO",
            values="ORDEN",
            aggfunc="count",
            fill_value=0
        )
        tabla_ordenes["TOTAL_ORDENES"] = tabla_ordenes.sum(axis=1)
        fila_total = pd.DataFrame([tabla_ordenes.sum()], index=["TOTAL GENERAL"])
        tabla_ordenes = pd.concat([tabla_ordenes, fila_total])
        tabla_ordenes = tabla_ordenes.sort_values(by="TOTAL_ORDENES", ascending=False)
        st.dataframe(tabla_ordenes.style.format("{:,.0f}").apply(
            lambda x: ["background-color: #dfeaf4; font-weight: bold" if x.name == "TOTAL GENERAL" else "" for _ in x],
            axis=1))

        st.subheader("💰 Importe Total por Proveedor y Estatus")
        tabla_importes = pd.pivot_table(
            df_filtrado,
            index="PROVEEDOR",
            columns="ESTATUS DE USUARIO",
            values="IMPORTE",
            aggfunc="sum",
            fill_value=0
        )
        tabla_importes["IMPORTE_TOTAL"] = tabla_importes.sum(axis=1)
        fila_total_importe = pd.DataFrame([tabla_importes.sum()], index=["TOTAL GENERAL"])
        tabla_importes = pd.concat([tabla_importes, fila_total_importe])
        tabla_importes = tabla_importes.round(2)
        tabla_importes = tabla_importes.sort_values(by="IMPORTE_TOTAL", ascending=False)
        st.dataframe(tabla_importes.style.format("${:,.0f}").apply(
            lambda x: ["background-color: #dfeaf4; font-weight: bold" if x.name == "TOTAL GENERAL" else "" for _ in x],
            axis=1))

        st.sidebar.markdown("---")
        if st.sidebar.button("📥 Descargar resumen en Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                tabla_ordenes.to_excel(writer, sheet_name='Ordenes')
                tabla_importes.to_excel(writer, sheet_name='Importes')
            st.sidebar.download_button(
                label="Descargar archivo .xlsx",
                data=output.getvalue(),
                file_name="resumen_mantenimiento.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

