import streamlit as st
import os
import tempfile
import json
import base64
from pathlib import Path
from asbestos_report_analyzer import AsbestosReportAnalyzer

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="Analyseur Amiante MVP", page_icon="⚠️", layout="wide")

st.markdown("""
    <style>
        .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .stButton>button { 
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%); 
            color: white; border: none; border-radius: 50px; padding: 15px 30px;
            font-weight: bold; width: 100%;
        }
        .zone-card {
            background: white; border-radius: 12px; padding: 20px;
            margin-bottom: 15px; border-left: 5px solid #ff9800; color: #333;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
        }
        .zone-card.critical { border-left-color: #ff4b2b; background-color: #fff5f5; }
        .header-custom {
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
            padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 25px;
        }
        .label-custom { font-weight: bold; color: #555; }
    </style>
    """, unsafe_allow_html=True)

# --- INTERFACE ---
st.markdown('<div class="header-custom"><h1>⚠️ Analyseur de Rapports Amiante</h1><p>Extraction automatique des zones dangereuses (DTA/RAAT)</p></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Glissez-déposez votre rapport PDF ici", type="pdf")

if uploaded_file is not None:
    st.info(f"Fichier prêt : {uploaded_file.name}")
    
    if st.button("🔍 LANCER L'ANALYSE DU DOCUMENT"):
        # Utilisation d'un dossier temporaire pour les sorties (PDF, Crops, JSON)
        with tempfile.TemporaryDirectory() as tmpdirname:
            input_path = os.path.join(tmpdirname, uploaded_file.name)
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            with st.spinner("Analyse du rapport en cours... Extraction des zones et des plans."):
                try:
                    # Initialisation et Analyse (en utilisant ton orchestrateur)
                    analyzer = AsbestosReportAnalyzer(input_path, output_dir=tmpdirname)
                    results = analyzer.analyser()
                    
                    if "error" in results:
                        st.error(f"Erreur : {results['error']}")
                    else:
                        # 1. AFFICHAGE DES STATS (Adapté à tes clés : zones_count, zones_with_plan)
                        st.markdown("### 📊 Résultats de l'analyse")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Zones détectées", results['zones_count'])
                        c2.metric("Localisées sur plan", results['zones_with_plan'])
                        c3.metric("Statut", "✅ Terminé")

                        # 2. LISTE DES ZONES
                        st.markdown("### 📍 Zones identifiées")
                        for zone in results['zones']:
                            # Détermination de la classe CSS selon le risque
                            is_crit = "critical" if zone.get('risque_niveau') == "CRITIQUE" else ""
                            
                            with st.container():
                                st.markdown(f"""
                                    <div class="zone-card {is_crit}">
                                        <h3 style="margin-top:0;">🔴 ZONE {zone['id_zone']} - {zone.get('risque_niveau', 'ÉLEVÉ')}</h3>
                                        <p><span class="label-custom">📍 Localisation :</span> {zone['localisation_texte']}</p>
                                        <p><span class="label-custom">🧱 Matériau :</span> {zone['materiau']}</p>
                                        <p><span class="label-custom">⚠️ État :</span> {zone['etat']}</p>
                                        <p><span class="label-custom">📄 Source :</span> Page {zone['page_source']}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                # Si ton script a généré un crop, on peut l'afficher ici
                                if zone.get('plan_crop_path') and os.path.exists(zone['plan_crop_path']):
                                    st.image(zone['plan_crop_path'], caption=f"Localisation Plan - Zone {zone['id_zone']}", width=400)

                        # 3. TÉLÉCHARGEMENTS
                        st.markdown("---")
                        st.markdown("### 💾 Télécharger les documents")
                        col_pdf, col_json = st.columns(2)
                        
                        # Téléchargement PDF
                        if os.path.exists(results['pdf_output']):
                            with open(results['pdf_output'], "rb") as f:
                                col_pdf.download_button(
                                    label="📑 Télécharger la Fiche Réflexe PDF",
                                    data=f,
                                    file_name="fiche_reflexe_amiante.pdf",
                                    mime="application/pdf"
                                )
                        
                        # Téléchargement JSON
                        json_data = json.dumps(results['zones'], indent=2, ensure_ascii=False)
                        col_json.download_button(
                            label="📊 Télécharger les données JSON",
                            data=json_data,
                            file_name="export_zones.json",
                            mime="application/json"
                        )

                except Exception as e:
                    st.error(f"Une erreur technique est survenue : {str(e)}")
                    st.info("Détails pour le débug : assurez-vous que toutes les dépendances (PyMuPDF, pdfplumber) sont installées.")
