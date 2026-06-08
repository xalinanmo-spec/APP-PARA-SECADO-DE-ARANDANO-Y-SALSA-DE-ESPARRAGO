import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="Balance de Masa",
    page_icon="🥫",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    .main-title {
        font-family: 'Space Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a2e;
        letter-spacing: -1px;
        margin-bottom: 0;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #555;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .resultado-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-top: 1rem;
    }
    .resultado-box h3 {
        font-family: 'Space Mono', monospace;
        font-size: 1rem;
        color: #a8d8ea;
        margin-bottom: 0.3rem;
    }
    .resultado-val {
        font-size: 2.2rem;
        font-weight: 700;
        font-family: 'Space Mono', monospace;
    }
    .badge-green { color: #4ade80; }
    .badge-red   { color: #f87171; }
    .badge-blue  { color: #60a5fa; }
    .info-box {
        border-left: 4px solid #4CAF50;
        background: #e8f5e9;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
        color: #2e7d32;
        margin-bottom: 1rem;
    }
    .info-box-blue {
        border-left: 4px solid #2196F3;
        background: #e3f2fd;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
        color: #1565c0;
        margin-bottom: 1rem;
    }
    .stSlider > div > div > div > div { background: #1a1a2e; }
    div[data-testid="stMetricValue"] { font-family: 'Space Mono', monospace; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIGURACIÓN DE PRODUCTOS
# ============================================================
PRODUCTOS = {
    "🫛 Espárrago (Salsa)": {
        "tipo": "aditivos",
        "rango_kg": (1.0, 5.0, 0.1, 2.5),
        "etapas": ["Corte", "Selección", "Pulpeado"],
        "aditivos": [("CMC", 0.2), ("GMS", 0.8), ("NaCl", 1.5), ("Ác. cítrico", 0.1)]
    },
    "🫐 Arándano (Deshidratado)": {
        "tipo": "humedad",
        "rango_kg": (0.5, 5.0, 0.1, 1.8),
        "etapas": ["Merma calidad", "Deshidratado", "Merma proceso"],
        "humedad": {"min": 75, "max": 90, "default": 85},
        "humedad_final": {"min": 8, "max": 25, "default": 12}
    }
}

# ============================================================
# FUNCIÓN PRINCIPAL DE CÁLCULO
# ============================================================
def calcular_balance(producto, F, valores):
    prod_key = producto.replace("🫛 ", "").replace("🫐 ", "")
    conf_key = next(k for k in PRODUCTOS if prod_key in k)
    conf = PRODUCTOS[conf_key]

    if conf["tipo"] == "aditivos":
        etapas = conf["etapas"]
        perdidas = [valores[f"perdida_{i}"] for i in range(len(etapas))]
        aditivos_pcts = valores["aditivos"]

        masas = [F]
        nombres = ["Espárrago fresco"]

        for i, (perdida, etapa) in enumerate(zip(perdidas, etapas)):
            if perdida < 0:
                st.error(f"❌ Error: Pérdida negativa en {etapa}"); return None
            if perdida > masas[-1]:
                st.error(f"❌ ERROR EN {etapa}: masa disponible {masas[-1]:.3f} kg, pérdida ingresada {perdida:.3f} kg")
                return None
            masas.append(masas[-1] - perdida)
            nombres.append(f"Después {etapa}")

        masa_base = masas[-1]
        aditivos_kg = [masa_base * (pct / 100) for _, pct in aditivos_pcts]
        producto_final = masa_base + sum(aditivos_kg)
        total_perdidas = sum(perdidas)

        etapas_graf = nombres + ["Salsa final"]
        valores_graf = masas + [producto_final]
        colores_graf = plt.cm.Blues(np.linspace(0.4, 0.9, len(etapas_graf)))
        titulo_graf = "Evolución del proceso (Salsa)"
        datos_pie = {
            'Producto final': producto_final,
            'Pérdidas': total_perdidas,
            'Aditivos': sum(aditivos_kg)
        }
        colores_pie = ['#4CAF50', '#F44336', '#2196F3']

        detalle = {
            "evolución": list(zip(nombres + ["Salsa final"], masas + [producto_final])),
            "aditivos": [(nom, kg) for (nom, _), kg in zip(aditivos_pcts, aditivos_kg)]
        }

    else:
        Mc = valores["Mc"]
        Hi = valores["Hi"]
        Hf = valores["Hf"]
        Mp = valores["Mp"]

        if Mc < 0:
            st.error("❌ Error: Merma calidad negativa"); return None
        if Mc > F:
            st.error(f"❌ ERROR EN MERMA CALIDAD: máximo {F:.3f} kg"); return None

        despues_calidad = F - Mc

        if not (0 <= Hi <= 100) or not (0 <= Hf <= 100):
            st.error("❌ Humedades deben estar entre 0-100%"); return None
        if Hf >= Hi:
            st.error(f"❌ Error: Humedad final ({Hf}%) debe ser menor que inicial ({Hi}%)"); return None

        solidos = despues_calidad * (1 - Hi / 100)
        peso_deshidratado = solidos / (1 - Hf / 100)
        agua_eliminada = despues_calidad - peso_deshidratado

        if agua_eliminada < 0:
            st.error("❌ Error: Cálculo de humedades inconsistente"); return None

        if Mp < 0:
            st.error("❌ Error: Merma proceso negativa"); return None
        if Mp > peso_deshidratado:
            st.error(f"❌ ERROR EN MERMA PROCESO: máximo {peso_deshidratado:.3f} kg"); return None

        producto_final = peso_deshidratado - Mp
        total_perdidas = Mc + agua_eliminada + Mp

        etapas_graf = ['Fresco', 'Después\ncalidad', 'Después\nsecado', 'Producto\nfinal']
        valores_graf = [F, despues_calidad, peso_deshidratado, producto_final]
        colores_graf = ['#4CAF50', '#8BC34A', '#FF9800', '#F44336']
        titulo_graf = "Evolución de la masa (Deshidratación)"
        datos_pie = {
            'Producto final': producto_final,
            'Agua eliminada': agua_eliminada,
            'Merma calidad': Mc,
            'Merma proceso': Mp
        }
        datos_pie = {k: v for k, v in datos_pie.items() if v > 0.001}
        colores_pie = ['#4CAF50', '#2196F3', '#9E9E9E', '#FF9800'][:len(datos_pie)]

        detalle = {
            "evolución": [
                ("Arándano fresco", F),
                ("Después merma calidad", despues_calidad),
                ("Después deshidratado", peso_deshidratado),
                ("Producto final", producto_final),
            ],
            "agua_eliminada": agua_eliminada
        }

    rendimiento = (producto_final / F) * 100

    return {
        "producto_final": producto_final,
        "total_perdidas": total_perdidas,
        "rendimiento": rendimiento,
        "etapas_graf": etapas_graf,
        "valores_graf": valores_graf,
        "colores_graf": colores_graf,
        "titulo_graf": titulo_graf,
        "datos_pie": datos_pie,
        "colores_pie": colores_pie,
        "detalle": detalle,
        "F": F
    }

# ============================================================
# INTERFAZ STREAMLIT
# ============================================================
st.markdown('<p class="main-title">⚗️ Balance de Masa</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Espárrago (Salsa) · Arándano (Deshidratado)</p>', unsafe_allow_html=True)

col_ctrl, col_res = st.columns([1, 2], gap="large")

with col_ctrl:
    producto = st.selectbox("Selecciona el producto", list(PRODUCTOS.keys()))
    conf = PRODUCTOS[producto]
    r = conf["rango_kg"]

    st.markdown("---")
    F = st.slider("📦 Masa inicial (kg)", min_value=r[0], max_value=r[1], step=r[2], value=r[3])

    valores = {}

    if conf["tipo"] == "aditivos":
        st.markdown('<div class="info-box">Pérdidas en <b>kg</b> · Aditivos en <b>%</b> sobre pulpa</div>', unsafe_allow_html=True)

        st.markdown("**Pérdidas por etapa**")
        for i, etapa in enumerate(conf["etapas"]):
            valores[f"perdida_{i}"] = st.slider(
                f"❌ {etapa} (kg)", min_value=0.0, max_value=5.0, step=0.05, value=0.3, key=f"perdida_{i}"
            )

        st.markdown("**Aditivos (%)**")
        aditivos_vals = []
        cols_ad = st.columns(2)
        for idx, (nom, pct) in enumerate(conf["aditivos"]):
            with cols_ad[idx % 2]:
                val = st.number_input(f"🧪 {nom} (%)", min_value=0.0, max_value=10.0,
                                      step=0.1, value=float(pct), key=f"ad_{idx}")
                aditivos_vals.append((nom, val))
        valores["aditivos"] = aditivos_vals

    else:
        st.markdown('<div class="info-box-blue">Mermas en <b>kg</b> · Humedades en <b>%</b></div>', unsafe_allow_html=True)

        valores["Mc"] = st.slider("❌ Merma calidad (kg)", 0.0, 2.0, 0.1, 0.05)
        valores["Hi"] = st.slider(
            "💧 Humedad inicial (%)",
            float(conf["humedad"]["min"]), float(conf["humedad"]["max"]),
            float(conf["humedad"]["default"]), 0.5
        )
        valores["Hf"] = st.slider(
            "🔥 Humedad final (%)",
            float(conf["humedad_final"]["min"]), float(conf["humedad_final"]["max"]),
            float(conf["humedad_final"]["default"]), 0.5
        )
        valores["Mp"] = st.slider("⚙️ Merma proceso (kg)", 0.0, 1.0, 0.05, 0.02)

    calcular = st.button("🔍 Calcular Balance", use_container_width=True, type="primary")

# ============================================================
# RESULTADOS
# ============================================================
with col_res:
    if calcular:
        res = calcular_balance(producto, F, valores)

        if res:
            # Métricas principales
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("✅ Producto final", f"{res['producto_final']:.3f} kg",
                          f"{res['producto_final']*1000:.0f} g")
            with m2:
                st.metric("📊 Rendimiento", f"{res['rendimiento']:.1f}%")
            with m3:
                st.metric("📉 Pérdidas totales", f"{res['total_perdidas']:.3f} kg")

            st.markdown("---")

            # Tabla evolución
            with st.expander("📋 Ver evolución detallada", expanded=True):
                for etapa, masa in res["detalle"]["evolución"]:
                    c1, c2 = st.columns([2, 1])
                    c1.write(etapa)
                    c2.write(f"**{masa:.3f} kg**")

                if "aditivos" in res["detalle"]:
                    st.markdown("**🧪 Aditivos añadidos:**")
                    for nom, kg in res["detalle"]["aditivos"]:
                        c1, c2 = st.columns([2, 1])
                        c1.write(f"  • {nom}")
                        c2.write(f"**{kg:.4f} kg**")

            # Gráficos
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
            fig.patch.set_facecolor('#f8f9fa')

            # Barras
            bars = ax1.bar(res["etapas_graf"], res["valores_graf"],
                           color=res["colores_graf"], edgecolor='white', linewidth=1.5)
            for bar, v in zip(bars, res["valores_graf"]):
                ax1.text(bar.get_x() + bar.get_width() / 2,
                         v + max(res["valores_graf"]) * 0.02,
                         f'{v:.3f} kg', ha='center', fontweight='bold', fontsize=8)
            ax1.set_ylabel('kg', fontsize=10)
            ax1.set_title(res["titulo_graf"], fontweight='bold', fontsize=11)
            ax1.grid(axis='y', alpha=0.3)
            ax1.tick_params(axis='x', rotation=25, labelsize=8)
            ax1.set_facecolor('#f8f9fa')
            for spine in ax1.spines.values():
                spine.set_visible(False)

            # Pastel
            explode = [0.1 if 'Producto' in k else 0 for k in res["datos_pie"].keys()]
            ax2.pie(
                res["datos_pie"].values(),
                labels=res["datos_pie"].keys(),
                autopct='%1.1f%%',
                colors=res["colores_pie"],
                explode=explode,
                textprops={'fontsize': 9}
            )
            ax2.set_title(f'Distribución (Base: {res["F"]} kg)', fontweight='bold', fontsize=11)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    else:
        st.markdown("""
        <div style='display:flex; align-items:center; justify-content:center;
                    height:300px; border:2px dashed #ddd; border-radius:12px;
                    color:#aaa; font-size:1.1rem; flex-direction:column; gap:10px;'>
            <span style='font-size:3rem;'>⚗️</span>
            <span>Ajusta los parámetros y presiona <b>Calcular</b></span>
        </div>
        """, unsafe_allow_html=True)
