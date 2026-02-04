import streamlit as st
import os
import tempfile
import json
import base64
from asbestos_report_analyzer import AsbestosReportAnalyzer

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="Analyseur Amiante MVP", page_icon="⚠️", layout="wide")

# Injection du CSS de ton fichier HTML pour garder le même look
st.markdown("""
    <style>
        .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .stButton>button { 
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%); 
            color: white; border: none; border-radius: 50px; padding: 10px 25px;
        }
        .zone-card {
            background: white; border-radius: 12px; padding: 20px;
            margin-bottom: 15px; border-left: 5px solid #ff9800; color: #333;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
        }
        .zone-card.critical { border-left-color: #ff4b2b; background-color: #fff5f5; }
        .stat-card {
            background: white; padding: 20px; border-radius: 10px;
            text-align: center; color: #333; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header-custom {
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
            padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 25px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- INTERFACE ---
st.markdown('<div class="header-custom"><h1>⚠️ Analyseur de Rapports Amiante</h1><p>Extraction automatique des zones dangereuses (DTA/RAAT)</p></div>', unsafe_allow_html=True)

# Zone d'upload
uploaded_file = st.file_uploader("Glissez-déposez votre rapport PDF ici", type="pdf")

if uploaded_file is not None:
    # Infos fichier
    st.success(f"Fichier sélectionné : {uploaded_file.name} ({round(uploaded_file.size/1024/1024, 2)} MB)")
    
    if st.button("🔍 LANCER L'ANALYSE DU DOCUMENT"):
        with tempfile.TemporaryDirectory() as tmpdirname:
            # 1. Sauvegarde du fichier uploadé
            input_path = os.path.join(tmpdirname, uploaded_file.name)
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 2. Appel de ton script Python
            with st.spinner("Analyse en cours... (Extraction des 500 pages)"):
                try:
                    analyzer = AsbestosReportAnalyzer(input_path, output_dir=tmpdirname)
                    results = analyzer.analyser()
                    
                    # 3. Affichage des Statistiques (Comme ton HTML)
                    st.markdown("### 📊 Résultats de l'analyse")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Zones détectées", results['metadata']['zones_detectees'])
                    col2.metric("Critiques", results['metadata']['zones_critiques'], delta_color="inverse")
                    col3.metric("Élevées", results['metadata']['zones_detectees'] - results['metadata']['zones_critiques'])
                    col4.metric("Pages", results['metadata']['total_pages'])

                    # 4. Liste des Zones (Comme tes cartes HTML)
                    st.markdown("### 📍 Localisation des dangers")
                    for zone in results['zones']:
                        is_crit = "critical" if zone['risque_niveau'] == "CRITIQUE" else ""
                        st.markdown(f"""
                            <div class="zone-card {is_crit}">
                                <h3>🔴 ZONE {zone['id_zone']} - {zone['risque_niveau']}</h3>
                                <p><b>📍 Localisation:</b> {zone['localisation']}</p>
                                <p><b>🧱 Matériau:</b> {zone['materiau']}</p>
                                <p><b>⚠️ État:</b> {zone['etat']}</p>
                                <p><b>📄 Source:</b> Page {zone['page_source']}</p>
                            </div>
                        """, unsafe_allow_html=True)

                    # 5. Téléchargements
                    st.markdown("### 💾 Télécharger les livrables")
                    c1, c2 = st.columns(2)
                    
                    with open(results['pdf_output'], "rb") as f:
                        c1.download_button("📑 Télécharger la Fiche Réflexe PDF", f, file_name="fiche_reflexe.pdf")
                    
                    json_str = json.dumps(results, indent=2)
                    c2.download_button("📊 Télécharger les données JSON", json_str, file_name="data.json")

                except Exception as e:
                    st.error(f"Une erreur est survenue lors de l'analyse : {e}")
