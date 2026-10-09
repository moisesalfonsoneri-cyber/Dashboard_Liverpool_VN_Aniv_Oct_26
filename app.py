#Versión 2.0 con cambio sin Monterrey Valle
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Liverpool Venta Nocturna Aniversario 2026", layout="wide")

DATA_FILE = Path("notebooks/data/processed/Liverpool_VN_Aniv_Oct_26_consolidado_2.0_limpio.csv")
COLOR_VERDE = "#447D2E"
COLOR_MUJER = "#E83E8C"
COLOR_HOMBRE = "#1F77B4"
COLOR_OTRO = "#7F7F7F"


@st.cache_data
def cargar_datos(csv_path: Path) -> pd.DataFrame:
    """Carga el CSV consolidado y convierte fecha a datetime."""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    return df


def agrupar_suma(
    df: pd.DataFrame, group_cols: list[str], value_col: str, new_value_col: str
) -> pd.DataFrame:
    """Agrupación simple de suma para evitar repetir código."""
    out = df.groupby(group_cols, dropna=False)[value_col].sum().reset_index()
    out.columns = [*group_cols, new_value_col]
    return out


def normalizar_genero_dashboard(valor: str) -> str:
    """Normaliza género para coloreado robusto en dashboard."""
    v = str(valor).strip().upper()
    if v in {"MUJER", "M", "F", "FEMENINO"}:
        return "MUJER"
    if v in {"HOMBRE", "H", "MASCULINO"}:
        return "HOMBRE"
    return "OTRO"


if not DATA_FILE.exists():
    st.error("Primero ejecuta notebooks/EDA.ipynb para generar el CSV limpio.")
    st.stop()

df = cargar_datos(DATA_FILE)

columnas_requeridas = ["sucursal", "marca", "fecha", "genero", "grabado"]
faltantes = [col for col in columnas_requeridas if col not in df.columns]
if faltantes:
    st.error(f"Faltan columnas en el CSV: {faltantes}")
    st.stop()

# Cabecera visual compacta.
header_col_1, header_col_2, header_col_3 = st.columns([1, 4, 1])
with header_col_1:
    st.image("logotipos/GrabaPro.png", width=140)
with header_col_2:
    st.markdown(
        """
        <h1 style='text-align: center; margin-bottom: 0;'>
        Liverpool Venta Nocturna Aniversario 2026
        </h1>
        <p style='text-align: center; margin-top: 0; font-size: 20px;'>
        "Marcaremos Todo En Tu Vida"
        </p>
        """,
        unsafe_allow_html=True,
    )
with header_col_3:
    st.image("logotipos/Liverpool.png", width=140)

# Filtros en sidebar.
st.sidebar.header("Filtros")
opciones_sucursal = sorted(df["sucursal"].dropna().astype(str).unique().tolist())
opciones_marca = sorted(df["marca"].dropna().astype(str).unique().tolist())
opciones_genero = sorted(df["genero"].dropna().astype(str).unique().tolist())

filtro_sucursal = st.sidebar.multiselect(
    "sucursal", opciones_sucursal, default=opciones_sucursal
)
filtro_marca = st.sidebar.multiselect("marca", opciones_marca, default=opciones_marca)
filtro_genero = st.sidebar.multiselect(
    "genero", opciones_genero, default=opciones_genero
)

fecha_min = df["fecha"].min()
fecha_max = df["fecha"].max()
filtro_fecha = None
if pd.notna(fecha_min) and pd.notna(fecha_max):
    filtro_fecha = st.sidebar.date_input(
        "fecha",
        value=(fecha_min.date(), fecha_max.date()),
        min_value=fecha_min.date(),
        max_value=fecha_max.date(),
    )

df_filtrado = df.copy()
df_filtrado = df_filtrado[df_filtrado["sucursal"].astype(str).isin(filtro_sucursal)]
df_filtrado = df_filtrado[df_filtrado["marca"].astype(str).isin(filtro_marca)]
df_filtrado = df_filtrado[df_filtrado["genero"].astype(str).isin(filtro_genero)]

if filtro_fecha and len(filtro_fecha) == 2:
    fecha_inicio = pd.to_datetime(filtro_fecha[0])
    fecha_fin = pd.to_datetime(filtro_fecha[1])
    df_filtrado = df_filtrado[
        (df_filtrado["fecha"] >= fecha_inicio) & (df_filtrado["fecha"] <= fecha_fin)
    ]

if df_filtrado.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

df_filtrado["genero_dashboard"] = df_filtrado["genero"].apply(normalizar_genero_dashboard)

# Agrupaciones base.
df_grabados_por_tienda = agrupar_suma(
    df_filtrado, ["sucursal"], "grabado", "total_grabados"
).sort_values("total_grabados", ascending=False)

df_grabados_por_marca = agrupar_suma(
    df_filtrado, ["marca"], "grabado", "total_grabados"
).sort_values("total_grabados", ascending=False)

df_grabados_por_fecha = agrupar_suma(
    df_filtrado, ["fecha"], "grabado", "total_grabados"
).sort_values("fecha", ascending=True)
df_grabados_por_fecha["fecha_texto"] = (
    df_grabados_por_fecha["fecha"].dt.strftime("%Y-%m-%d").fillna("SIN FECHA")
)

df_genero_total = agrupar_suma(
    df_filtrado, ["genero_dashboard"], "grabado", "total_grabados"
).sort_values("total_grabados", ascending=False)

total_grabados = int(df_filtrado["grabado"].sum())
total_tiendas = int(df_filtrado["sucursal"].nunique())
total_marcas = int(df_filtrado["marca"].nunique())

tienda_lider = df_grabados_por_tienda.iloc[0]["sucursal"]
marca_lider = df_grabados_por_marca.iloc[0]["marca"]
registro_dia_lider = df_grabados_por_fecha.sort_values("total_grabados", ascending=False).iloc[0]
dia_lider = str(registro_dia_lider["fecha_texto"])

tiendas_nombres = ", ".join(sorted(df_filtrado["sucursal"].dropna().astype(str).unique().tolist()))

# KPIs superiores fuera de tabs (formato ejecutivo más visible).
st.markdown(
    """
    <style>
    .kpi-card {
        border: 1px solid #d9dee3;
        border-left: 6px solid #2E7D32;
        border-radius: 10px;
        padding: 10px 12px;
        background-color: #f8faf9;
        min-height: 86px;
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #4b5563;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.45rem;
        font-weight: 700;
        color: #111827;
        line-height: 1.1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Indicadores principales")
kpi_cols = st.columns(6)
kpi_data = [
    ("Total de Grabados", f"{total_grabados:,}"),
    ("Marcas participantes", f"{total_marcas:,}"),
    ("Tienda líder", str(tienda_lider)),
    ("Marca líder", str(marca_lider)),
    ("Día líder", dia_lider),
    ("Tiendas participantes", f"{total_tiendas} tiendas"),
]

for col, (label, value) in zip(kpi_cols, kpi_data):
    col.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(f"Tiendas incluidas: {tiendas_nombres}")

tabs = st.tabs(["Resumen Grabados", "Análsis Género", "Análisis Emociones", "Conclusión"])

with tabs[0]:
    st.markdown("## Grabados por fecha")
    st.write("Evolución diaria de grabados en el rango seleccionado.")

    fig_fecha = px.line(
        df_grabados_por_fecha,
        x="fecha",
        y="total_grabados",
        markers=True,
        title="Evolución de grabados por fecha.",
        labels={"fecha": "Fecha", "total_grabados": "Total de grabados"},
    )
    fig_fecha.update_traces(line_color=COLOR_VERDE, marker_color=COLOR_VERDE)
    st.plotly_chart(fig_fecha, use_container_width=True)
    with st.expander("Ver tabla de grabados por fecha", expanded=False):
        st.dataframe(
            df_grabados_por_fecha[["fecha_texto", "total_grabados"]],
            use_container_width=True,
        )

    st.markdown("## Total de grabados por tienda")
    st.write("Distribución total de grabados por sucursal (todas las tiendas).")
    fig_tienda = px.bar(
        df_grabados_por_tienda,
        x="sucursal",
        y="total_grabados",
        text="total_grabados",
        title="Total de grabados por tienda",
        labels={"sucursal": "Sucursal", "total_grabados": "Total de grabados"},
        color_discrete_sequence=[COLOR_VERDE],
    )
    fig_tienda.update_traces(textposition="outside")
    st.plotly_chart(fig_tienda, use_container_width=True)
    with st.expander("Ver tabla de grabados por tienda", expanded=False):
        st.dataframe(df_grabados_por_tienda, use_container_width=True)

    st.markdown("## Grabados por marca")
    st.write("Total de grabados por marca, mostrando todas las marcas.")
    df_grabados_por_marca_plot = df_grabados_por_marca.sort_values(
        "total_grabados", ascending=True
    )
    altura_dinamica_marca = max(500, 26 * len(df_grabados_por_marca_plot))
    fig_marca = px.bar(
        df_grabados_por_marca_plot,
        x="total_grabados",
        y="marca",
        orientation="h",
        text="total_grabados",
        title="Grabados por marca (todas las marcas)",
        height=altura_dinamica_marca,
        labels={"marca": "Marca", "total_grabados": "Total de grabados"},
        color_discrete_sequence=[COLOR_VERDE],
    )
    fig_marca.update_traces(textposition="outside")
    st.plotly_chart(fig_marca, use_container_width=True)
    with st.expander("Ver tabla de grabados por marca", expanded=False):
        st.dataframe(df_grabados_por_marca, use_container_width=True)

with tabs[1]:
    st.markdown("## Género total")
    st.write("Participación total de género en los registros filtrados.")
    fig_genero_total = px.pie(
        df_genero_total,
        names="genero_dashboard",
        values="total_grabados",
        title="Distribución de género total",
        color="genero_dashboard",
        color_discrete_map={
            "MUJER": COLOR_MUJER,
            "HOMBRE": COLOR_HOMBRE,
            "OTRO": COLOR_OTRO,
        },
    )
    st.plotly_chart(fig_genero_total, use_container_width=True)
    with st.expander("Ver tabla de género total", expanded=False):
        st.dataframe(df_genero_total, use_container_width=True)

    st.markdown("## Grabados por género y tienda")
    st.write("Comparación de género por sucursal para todas las tiendas.")
    df_genero_tienda = agrupar_suma(
        df_filtrado, ["sucursal", "genero_dashboard"], "grabado", "total_grabados"
    )
    orden_tiendas = df_grabados_por_tienda["sucursal"].tolist()
    fig_genero_tienda = px.bar(
        df_genero_tienda,
        x="sucursal",
        y="total_grabados",
        color="genero_dashboard",
        barmode="group",
        title="Grabados por género y tienda",
        labels={
            "sucursal": "Sucursal",
            "total_grabados": "Total de grabados",
            "genero_dashboard": "Género",
        },
        category_orders={
            "sucursal": orden_tiendas,
            "genero_dashboard": ["MUJER", "HOMBRE", "OTRO"],
        },
        color_discrete_map={
            "MUJER": COLOR_MUJER,
            "HOMBRE": COLOR_HOMBRE,
            "OTRO": COLOR_OTRO,
        },
    )
    st.plotly_chart(fig_genero_tienda, use_container_width=True)
    with st.expander("Ver tabla de género por tienda", expanded=False):
        st.dataframe(df_genero_tienda, use_container_width=True)

    st.markdown("## Grabados por género y marca")
    st.write("Distribución de género por marca con barras horizontales apiladas.")
    df_genero_marca = agrupar_suma(
        df_filtrado, ["marca", "genero_dashboard"], "grabado", "total_grabados"
    )
    orden_marcas = df_grabados_por_marca["marca"].tolist()
    altura_dinamica_genero_marca = max(500, 24 * len(orden_marcas))
    fig_genero_marca = px.bar(
        df_genero_marca,
        y="marca",
        x="total_grabados",
        color="genero_dashboard",
        orientation="h",
        barmode="stack",
        title="Grabados por género y marca",
        height=altura_dinamica_genero_marca,
        labels={
            "marca": "Marca",
            "total_grabados": "Total de grabados",
            "genero_dashboard": "Género",
        },
        category_orders={
            "marca": orden_marcas[::-1],
            "genero_dashboard": ["MUJER", "HOMBRE", "OTRO"],
        },
        color_discrete_map={
            "MUJER": COLOR_MUJER,
            "HOMBRE": COLOR_HOMBRE,
            "OTRO": COLOR_OTRO,
        },
    )
    st.plotly_chart(fig_genero_marca, use_container_width=True)
    with st.expander("Ver tabla de género por marca", expanded=False):
        st.dataframe(df_genero_marca, use_container_width=True)

with tabs[2]:
    st.markdown("## Insights desempeño y emoción")
    st.write(
        "Esta matriz permite identificar qué combinaciones marca-tienda "
        "tuvieron mayor actividad durante el fin de semana."
    )

    st.markdown("### Mapa de calor: concentración de grabados por marca y tienda")
    matriz_tienda_marca = df_filtrado.pivot_table(
        index="marca",
        columns="sucursal",
        values="grabado",
        aggfunc="sum",
        fill_value=0,
    ).sort_index()
    altura_dinamica_matriz = max(500, 24 * len(matriz_tienda_marca))
    fig_matriz = px.imshow(
        matriz_tienda_marca,
        aspect="auto",
        color_continuous_scale="Blues",
        labels={"x": "Sucursal", "y": "Marca", "color": "Grabados"},
    )
    fig_matriz.update_layout(height=altura_dinamica_matriz)
    fig_matriz.update_xaxes(side="top")
    st.plotly_chart(fig_matriz, use_container_width=True)

    st.markdown("### Análisis emocional")
    if "categoria_emocional" not in df_filtrado.columns:
        st.warning(
            "Primero ejecuta notebooks/EDA.ipynb para generar la clasificación emocional."
        )
    else:
        df_emocional = agrupar_suma(
            df_filtrado,
            ["categoria_emocional", "marca"],
            "grabado",
            "total_grabados",
        )
        df_emocional["categoria_emocional_dashboard"] = df_emocional[
            "categoria_emocional"
        ].apply(
            lambda x: "OTROS"
            if str(x).upper() in {"MIXTO", "LIBERTAD", "SIN CLASIFICAR"}
            else x
        )
        df_emocional_dashboard = agrupar_suma(
            df_emocional,
            ["categoria_emocional_dashboard", "marca"],
            "total_grabados",
            "total_grabados",
        )
        altura_dinamica_emocional = max(
            500, 24 * df_emocional_dashboard["categoria_emocional_dashboard"].nunique()
        )
        fig_emocional = px.bar(
            df_emocional_dashboard,
            y="categoria_emocional_dashboard",
            x="total_grabados",
            color="marca",
            orientation="h",
            barmode="stack",
            title="Categoría emocional vs marcas",
            height=altura_dinamica_emocional,
            labels={
                "categoria_emocional_dashboard": "Categoría emocional",
                "total_grabados": "Total de grabados",
                "marca": "Marca",
            },
        )
        st.plotly_chart(fig_emocional, use_container_width=True)
        with st.expander("Ver tabla de análisis emocional", expanded=False):
            st.dataframe(df_emocional_dashboard, use_container_width=True)

    with st.expander("Ver tabla matriz marca-tienda", expanded=False):
        st.dataframe(matriz_tienda_marca.reset_index(), use_container_width=True)

    st.markdown("### Ranking marca-tienda")
    st.write("¿En qué tienda funcionó mejor cada marca?")
    df_marca_tienda = agrupar_suma(
        df_filtrado, ["marca", "sucursal"], "grabado", "grabados_marca_sucursal"
    )
    df_total_marca = agrupar_suma(
        df_filtrado, ["marca"], "grabado", "total_grabados_marca"
    )
    idx_lider = df_marca_tienda.groupby("marca")["grabados_marca_sucursal"].idxmax()
    df_lider_marca = df_marca_tienda.loc[idx_lider].copy().rename(
        columns={
            "sucursal": "sucursal_lider",
            "grabados_marca_sucursal": "grabados_sucursal_lider",
        }
    )
    df_ranking_marca_tienda = df_lider_marca.merge(
        df_total_marca, on="marca", how="left"
    )
    df_ranking_marca_tienda["participacion_sucursal_lider"] = (
        df_ranking_marca_tienda["grabados_sucursal_lider"]
        / df_ranking_marca_tienda["total_grabados_marca"]
        * 100
    ).round(2)
    df_ranking_marca_tienda = df_ranking_marca_tienda[
        [
            "marca",
            "sucursal_lider",
            "grabados_sucursal_lider",
            "total_grabados_marca",
            "participacion_sucursal_lider",
        ]
    ].sort_values("total_grabados_marca", ascending=False)
    st.dataframe(df_ranking_marca_tienda, use_container_width=True)

with tabs[3]:
    st.markdown(
        """
        ### Observaciones y comentarios

        - Escribe aquí las observaciones comerciales más relevantes del evento.
        - Agrega comentarios sobre desempeño por tienda, marca, género o categoría emocional.
        - Incluye recomendaciones para futuras activaciones.
        """
    )
