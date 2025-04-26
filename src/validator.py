import pandas as pd
import streamlit as st

# --- Inicialización del estado ---
if "df" not in st.session_state:
    st.session_state.df = pd.read_csv("../datasets/RAG-HPO/Test_Cases.csv")
    st.session_state.index = 0

# --- Atajo al dataframe y al índice ---
df = st.session_state.df
idx = st.session_state.index

st.title("Editor de Traducciones")

if idx < len(df):
    fila = df.iloc[idx]

    col1, col2 = st.columns([2, 3])
    col1.markdown("**Texto original (eng):**")
    col1.text(fila["eng"])

    # Campo editable
    nueva_esp = col2.text_area(
        "Traducción (esp):",
        value=fila["esp"],
        key=f"esp_{idx}",
        height=100
    )

    if st.button("✅ Validar y siguiente"):
        # Guardar directamente sobre session_state
        st.session_state.df.at[idx, 'esp'] = nueva_esp
        st.session_state.index += 1
        st.rerun()

else:
    st.success("🎉 ¡Has terminado de revisar todas las traducciones!")

# Guardar archivo final
if st.button("💾 Guardar archivo"):
    st.session_state.df.to_csv("datos_actualizados.csv", index=False)
    st.success("Archivo guardado como 'datos_actualizados.csv'")
