# Este archivo usa Streamlit y debe ejecutarse localmente.
# Ejecuta en tu terminal: pip install streamlit plotly
# Luego corre: streamlit run app.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
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

    estatus_disponibles = df["ESTATUS DE USUARIO"].dropna().unique() if "ESTATUS DE USUARIO" in df.columns else []
    estatus_usuario = st.sidebar.multiselect("Estatus de Usuario", estatus_disponibles)

    df_filtrado = df.copy()
    if "TIPO DE ORDEN" in df.columns and tipo_orden:
        df_filtrado = df_filtrado[df_filtrado["TIPO DE ORDEN"].isin(tipo_orden)]
    if "FECHA DE CREACIÓN" in df.columns:
        df_filtrado = df_filtrado[(df_filtrado["FECHA DE CREACIÓN"].dt.year == anio) & (df_filtrado["FECHA DE CREACIÓN"].dt.month.isin(meses))]
    if "PROVEEDOR" in df.columns and proveedores:
        df_filtrado = df_filtrado[df_filtrado["PROVEEDOR"].isin(proveedores)]
    if "ESTATUS DE USUARIO" in df.columns and estatus_usuario:
        df_filtrado = df_filtrado[df_filtrado["ESTATUS DE USUARIO"].isin(estatus_usuario)]

    if df_filtrado.empty:
        st.warning("⚠️ No hay datos para mostrar con los filtros seleccionados. Revisa el archivo y los criterios.")
    else:
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
        st.dataframe(tabla_ordenes.style.apply(lambda x: ["background-color: #dfeaf4; font-weight: bold" if x.name == "TOTAL GENERAL" else "" for _ in x], axis=1))

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
        st.dataframe(tabla_importes.style.format("${:,.0f}").apply(lambda x: ["background-color: #dfeaf4; font-weight: bold" if x.name == "TOTAL GENERAL" else "" for _ in x], axis=1))

        st.subheader("📋 Detalle de Órdenes del Proveedor")
        proveedor_detalle = st.selectbox("Selecciona un proveedor para ver el detalle:", df_filtrado["PROVEEDOR"].dropna().unique())
        estatus_detalle = st.multiselect("Filtrar por estatus de usuario:", estatus_disponibles)

        df_detalle = df_filtrado[df_filtrado["PROVEEDOR"] == proveedor_detalle]
        if estatus_detalle:
            df_detalle = df_detalle[df_detalle["ESTATUS DE USUARIO"].isin(estatus_detalle)]

        st.dataframe(df_detalle.reset_index(drop=True))

        st.subheader("📈 Visualizaciones Interactivas")
        st.markdown("---")

        st.markdown("#### Órdenes por Estatus y Proveedor")
        df_bar = df_filtrado.groupby(["PROVEEDOR", "ESTATUS DE USUARIO"]).size().reset_index(name="ORDENES")
        fig_bar = px.bar(df_bar, x="PROVEEDOR", y="ORDENES", color="ESTATUS DE USUARIO", barmode="group")
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("#### Distribución del Importe por Estatus")
        df_pie = df_filtrado.groupby("ESTATUS DE USUARIO")["IMPORTE"].sum().reset_index()
        fig_pie = px.pie(df_pie, names="ESTATUS DE USUARIO", values="IMPORTE")
        st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("#### Órdenes por Mes y Proveedor")
        df_filtrado["MES"] = df_filtrado["FECHA DE CREACIÓN"].dt.month
        df_line = df_filtrado.groupby(["MES", "PROVEEDOR"]).size().reset_index(name="ORDENES")
        fig_line = px.line(df_line, x="MES", y="ORDENES", color="PROVEEDOR", markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

        st.sidebar.markdown("---")
        if st.sidebar.button("📥 Descargar resumen en Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                tabla_ordenes.to_excel(writer, sheet_name='Ordenes')
                tabla_importes.to_excel(writer, sheet_name='Importes')
                df_filtrado.to_excel(writer, sheet_name='Detalle')
                df_detalle.to_excel(writer, sheet_name='Detalle_Proveedor')
            st.sidebar.download_button(
                label="Descargar archivo .xlsx",
                data=output.getvalue(),
                file_name="resumen_mantenimiento.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
