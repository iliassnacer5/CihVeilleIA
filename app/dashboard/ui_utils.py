import streamlit as st

def apply_cih_theme():
    """Applique le thème visuel CIH Bank à l'interface Streamlit."""
    st.markdown("""
        <style>
        /* Couleurs CIH Bank */
        :root {
            --cih-blue: #004687;
            --cih-orange: #FF8200;
            --cih-white: #FFFFFF;
        }

        /* En-tête et titres */
        h1, h2, h3 {
            color: var(--cih-blue) !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* Sidebar personnalisée */
        [data-testid="stSidebar"] {
            background-color: #f0f2f6;
            border-right: 2px solid var(--cih-blue);
        }

        /* Boutons */
        div.stButton > button {
            background-color: var(--cih-blue);
            color: white;
            border-radius: 5px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
            transition: all 0.3s;
        }
        div.stButton > button:hover {
            background-color: var(--cih-orange);
            color: white;
        }

        /* Alertes et Info */
        .stAlert {
            border-left: 5px solid var(--cih-orange) !important;
        }

        /* Cartes de statistiques */
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-top: 4px solid var(--cih-blue);
            text-align: center;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: var(--cih-blue);
        }
        .metric-label {
            font-size: 1rem;
            color: #666;
        }
        </style>
    """, unsafe_allow_html=True)

def cih_metric(label, value, delta=None):
    """Affiche une métrique stylisée CIH."""
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {"<div style='color: green;'>↑ " + delta + "</div>" if delta else ""}
        </div>
    """, unsafe_allow_html=True)

def render_logo():
    """Affiche un placeholder pour le logo CIH ou un titre stylisé."""
    st.sidebar.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            <h2 style="color: #004687; margin-bottom: 0;">CIH BANK</h2>
            <div style="color: #FF8200; font-weight: bold; font-size: 0.8rem;">VEILLE IA STRATÉGIQUE</div>
        </div>
        <hr style="margin-top: 0; border-color: #004687;">
    """, unsafe_allow_html=True)
