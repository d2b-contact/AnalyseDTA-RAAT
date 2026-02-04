#!/usr/bin/env python3
"""
DÉMO INTERACTIVE - Analyseur de Rapports Amiante
=================================================

Ce script attend que vous uploadiez votre PDF et l'analyse automatiquement.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

print("="*80)
print("🚀 DÉMO INTERACTIVE - ANALYSEUR DE RAPPORTS AMIANTE")
print("="*80)
print()
print("📋 Instructions:")
print("   1. Uploadez votre rapport amiante PDF")
print("   2. Le système l'analysera automatiquement")
print("   3. Vous recevrez une fiche réflexe + données JSON")
print()
print("⏳ En attente de votre fichier PDF...")
print("   Le fichier doit être placé dans: /mnt/user-data/uploads/")
print()

# Attendre et détecter le PDF uploadé
import time
upload_dir = Path("/mnt/user-data/uploads")

# Lister les PDFs disponibles
pdf_files = list(upload_dir.glob("*.pdf"))

if not pdf_files:
    print("❌ Aucun fichier PDF trouvé dans /mnt/user-data/uploads/")
    print()
    print("💡 Pour tester la démo:")
    print("   1. Cliquez sur le bouton 📎 (trombone) en bas de l'interface")
    print("   2. Uploadez un rapport amiante PDF")
    print("   3. Relancez ce script")
    print()
    sys.exit(0)

# Prendre le premier PDF trouvé
pdf_path = pdf_files[0]

print(f"✅ PDF détecté: {pdf_path.name}")
print(f"   Taille: {pdf_path.stat().st_size / 1024:.1f} KB")
print()

# ============================================================================
# ANALYSE DU PDF
# ============================================================================

print("="*80)
print("🔍 DÉBUT DE L'ANALYSE")
print("="*80)
print()

try:
    import pdfplumber
    import re
    
    zones_detectees = []
    pages_plans = []
    
    print("📖 ÉTAPE 1: Ouverture et scan du document...")
    print("-"*80)
    
    with pdfplumber.open(str(pdf_path)) as pdf:
        total_pages = len(pdf.pages)
        print(f"   Document ouvert: {total_pages} pages")
        print()
        
        print("📊 ÉTAPE 2: Analyse page par page...")
        print("-"*80)
        
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text_lower = text.lower()
            
            # FILTRAGE INTELLIGENT
            is_cover = page_num <= 3 and any(kw in text_lower for kw in ["sommaire", "table des matières", "mentions légales"])
            
            if is_cover:
                print(f"   Page {page_num:3d}: 🚫 Page de garde/sommaire (ignorée)")
                continue
            
            # DÉTECTION TABLEAUX DE REPÉRAGE
            is_table_page = any(kw in text_lower for kw in [
                "tableau", "repérage", "résultats", "échantillon", 
                "analyses", "matériau", "localisation"
            ])
            
            if is_table_page:
                print(f"   Page {page_num:3d}: 📋 Tableau de repérage détecté")
                
                # Extraction ligne par ligne
                lignes = text.split('\n')
                
                for ligne in lignes:
                    ligne_lower = ligne.lower()
                    
                    # Chercher présence d'amiante
                    has_asbestos = any(kw in ligne_lower for kw in [
                        "présence", "détecté", "positif", "amiante", 
                        "amianté", "trace", "matériau"
                    ])
                    
                    # Vérifier que ce n'est PAS négatif
                    is_negative = any(kw in ligne_lower for kw in [
                        "absence", "négatif", "non détecté", "aucun"
                    ])
                    
                    if has_asbestos and not is_negative:
                        # Chercher ID zone
                        id_patterns = [
                            r'\b(P[\-_]?\d+)\b',           # P076, P-076
                            r'\b(Z[\-_]?\d+)\b',           # Z-12, Z12
                            r'\b(LOCAL[\-_]?\d+)\b',       # LOCAL-04
                            r'\b(ZONE[\-_]?\d+)\b',        # ZONE-23
                            r'\b(EXT[\-_]?\d+)\b',         # EXT-05
                            r'\b([A-Z]{2,4}[\-_]?\d+)\b', # RDC-01, TGBT-3
                        ]
                        
                        id_zone = None
                        for pattern in id_patterns:
                            match = re.search(pattern, ligne, re.IGNORECASE)
                            if match:
                                id_zone = match.group(1).upper()
                                break
                        
                        if id_zone:
                            # Extraire informations
                            localisation = ligne[:100] if len(ligne) > 10 else "Non spécifiée"
                            
                            # Chercher matériau
                            materiau = "Non spécifié"
                            materiaux_cles = [
                                "dalle", "plafond", "cloison", "isolation", 
                                "flocage", "tuyau", "conduit", "gaine",
                                "fibrociment", "amiante-ciment", "vinyle",
                                "enduit", "colle", "joint", "bardage"
                            ]
                            
                            for mat in materiaux_cles:
                                if mat in ligne_lower:
                                    # Extraire contexte
                                    idx = ligne_lower.find(mat)
                                    materiau = ligne[max(0, idx-5):min(len(ligne), idx+50)].strip()
                                    break
                            
                            # Chercher état
                            etat = "Non évalué"
                            etats = {
                                "dégradé": "Dégradé",
                                "détérioré": "Détérioré", 
                                "bon état": "Bon état",
                                "moyen": "Moyen",
                                "friable": "Friable",
                                "altéré": "Altéré"
                            }
                            
                            for etat_key, etat_val in etats.items():
                                if etat_key in ligne_lower:
                                    etat = etat_val
                                    break
                            
                            # Déterminer risque
                            risque = "ÉLEVÉ"
                            if any(kw in etat.lower() for kw in ["dégradé", "détérioré", "friable"]):
                                risque = "CRITIQUE"
                            
                            zone = {
                                "id_zone": id_zone,
                                "localisation": localisation,
                                "materiau": materiau,
                                "etat": etat,
                                "page_source": page_num,
                                "risque_niveau": risque
                            }
                            
                            # Éviter doublons
                            if not any(z['id_zone'] == id_zone for z in zones_detectees):
                                zones_detectees.append(zone)
                                symbole = "🔴" if risque == "CRITIQUE" else "🟠"
                                print(f"            {symbole} Zone détectée: {id_zone} ({etat})")
            
            # DÉTECTION PLANS
            is_plan = page.width > page.height
            if is_plan:
                pages_plans.append(page_num)
                print(f"   Page {page_num:3d}: 🗺️  Plan architectural (format paysage)")
        
        print()
        print(f"✅ Scan terminé:")
        print(f"   • {len(zones_detectees)} zones dangereuses identifiées")
        print(f"   • {len(pages_plans)} pages de plans détectées")
        print()

except Exception as e:
    print(f"❌ Erreur lors de l'analyse: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# AFFICHAGE RÉSULTATS
# ============================================================================

print("="*80)
print("📋 RÉSULTATS DÉTAILLÉS")
print("="*80)
print()

if zones_detectees:
    for i, zone in enumerate(zones_detectees, 1):
        symbole = "🔴" if zone['risque_niveau'] == "CRITIQUE" else "🟠"
        print(f"{symbole} ZONE DANGEREUSE #{i}")
        print(f"   {'='*70}")
        print(f"   ID:              {zone['id_zone']}")
        print(f"   Localisation:    {zone['localisation'][:70]}")
        print(f"   Matériau:        {zone['materiau'][:70]}")
        print(f"   État:            {zone['etat']}")
        print(f"   Risque:          {zone['risque_niveau']}")
        print(f"   Page source:     {zone['page_source']}")
        print()
else:
    print("⚠️  Aucune zone dangereuse détectée dans ce document")
    print()
    print("💡 Cela peut signifier:")
    print("   • Le document ne contient pas de zones avec amiante")
    print("   • Le format du tableau n'a pas été reconnu")
    print("   • Les mots-clés de détection ne correspondent pas")
    print()

# ============================================================================
# GÉNÉRATION JSON
# ============================================================================

print("="*80)
print("💾 GÉNÉRATION DES FICHIERS DE SORTIE")
print("="*80)
print()

try:
    # Créer répertoire de sortie
    output_dir = Path("/mnt/user-data/outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Générer nom de fichier basé sur le PDF source
    base_name = pdf_path.stem
    
    # JSON
    output_json = output_dir / f"{base_name}_zones.json"
    
    rapport = {
        "metadata": {
            "date_analyse": datetime.now().isoformat(),
            "fichier_source": pdf_path.name,
            "total_pages": total_pages,
            "zones_detectees": len(zones_detectees),
            "zones_critiques": sum(1 for z in zones_detectees if z['risque_niveau'] == 'CRITIQUE'),
            "pages_plans": pages_plans,
            "analyseur_version": "1.0.0-demo"
        },
        "zones": zones_detectees,
        "statistiques": {
            "repartition_risques": {
                "CRITIQUE": sum(1 for z in zones_detectees if z['risque_niveau'] == 'CRITIQUE'),
                "ÉLEVÉ": sum(1 for z in zones_detectees if z['risque_niveau'] == 'ÉLEVÉ')
            }
        },
        "recommandations": [
            "⚠️  Port obligatoire des EPI (combinaison, gants, masque FFP3)",
            "🚫 Interdiction d'intervention sans validation coordinateur SPS",
            "📄 Consulter rapport complet avant tout travaux invasifs",
            "🔒 Balisage des zones obligatoire pendant intervention",
            "☎️  En cas de doute: STOP TRAVAUX et contacter HSE"
        ]
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Rapport JSON créé: {output_json.name}")
    print()
    
    # ========================================================================
    # GÉNÉRATION FICHE RÉFLEXE PDF
    # ========================================================================
    
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as pdf_canvas
    
    output_pdf = output_dir / f"{base_name}_fiche_reflexe.pdf"
    
    c = pdf_canvas.Canvas(str(output_pdf), pagesize=A4)
    width, height = A4
    
    # En-tête avec fond rouge
    c.setFillColorRGB(0.85, 0.1, 0.1)
    c.rect(0, height - 110, width, 110, fill=1, stroke=0)
    
    # Titre
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, height - 50, "⚠ FICHE RÉFLEXE AMIANTE ⚠")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 75, f"Document source: {pdf_path.name[:50]}")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 95, 
                       f"Analyse du {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    
    # Compteur zones
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    zones_text = f"{len(zones_detectees)} ZONE(S) DANGEREUSE(S) IDENTIFIÉE(S)"
    if len(zones_detectees) > 0:
        c.setFillColorRGB(0.8, 0, 0)
    c.drawCentredString(width/2, height - 135, zones_text)
    c.setFillColorRGB(0, 0, 0)
    
    # Zones
    y = height - 170
    
    if zones_detectees:
        for i, zone in enumerate(zones_detectees[:8], 1):  # Max 8 zones
            if y < 100:
                c.showPage()
                y = height - 80
            
            # Encadré
            couleur_fond = (1, 0.8, 0.8) if zone['risque_niveau'] == 'CRITIQUE' else (1, 0.93, 0.88)
            c.setFillColorRGB(*couleur_fond)
            c.rect(35, y - 100, width - 70, 95, fill=1, stroke=1)
            
            # En-tête zone
            couleur_titre = (0.8, 0, 0) if zone['risque_niveau'] == 'CRITIQUE' else (0.9, 0.5, 0)
            c.setFillColorRGB(*couleur_titre)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(45, y - 22, f"#{i} - ZONE {zone['id_zone']} - {zone['risque_niveau']}")
            
            # Détails
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 9)
            
            c.drawString(45, y - 42, "📍 Localisation:")
            c.setFont("Helvetica-Bold", 9)
            localisation_text = zone['localisation'][:75]
            c.drawString(130, y - 42, localisation_text)
            
            c.setFont("Helvetica", 9)
            c.drawString(45, y - 58, "🧱 Matériau:")
            c.setFont("Helvetica-Bold", 9)
            materiau_text = zone['materiau'][:75]
            c.drawString(130, y - 58, materiau_text)
            
            c.setFont("Helvetica", 9)
            c.drawString(45, y - 74, "⚠  État:")
            c.setFont("Helvetica-Bold", 9)
            etat_couleur = (0.8, 0, 0) if "dégradé" in zone['etat'].lower() or "friable" in zone['etat'].lower() else (0, 0, 0)
            c.setFillColorRGB(*etat_couleur)
            c.drawString(130, y - 74, zone['etat'])
            
            c.setFillColorRGB(0, 0, 0)
            c.setFont("Helvetica", 8)
            c.drawString(45, y - 90, f"📄 Source: page {zone['page_source']} du rapport complet")
            
            y -= 115
        
        # Si plus de 8 zones
        if len(zones_detectees) > 8:
            c.setFont("Helvetica-Bold", 10)
            c.setFillColorRGB(0.8, 0, 0)
            c.drawCentredString(width/2, y - 20, 
                               f"⚠ {len(zones_detectees) - 8} zone(s) supplémentaire(s) non affichée(s)")
            c.drawCentredString(width/2, y - 35,
                               "Consulter le fichier JSON pour la liste complète")
    else:
        # Message si aucune zone
        c.setFont("Helvetica", 12)
        c.drawCentredString(width/2, height - 250,
                           "✅ Aucune zone avec amiante détectée dans ce document")
        c.setFont("Helvetica", 10)
        c.drawCentredString(width/2, height - 280,
                           "Document analysé mais aucun matériau amianté identifié")
    
    # Footer
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawCentredString(width/2, 40,
                       "⚠ ATTENTION: Ce document est une aide à la décision - Toujours consulter le rapport complet")
    c.drawCentredString(width/2, 28,
                       "En cas de doute: ARRÊT IMMÉDIAT des travaux + Contact coordinateur SPS")
    
    c.save()
    
    print(f"✅ Fiche réflexe PDF créée: {output_pdf.name}")
    print()

except Exception as e:
    print(f"❌ Erreur génération fichiers: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================

print()
print("="*80)
print("✅ ANALYSE TERMINÉE")
print("="*80)
print()
print("📦 Fichiers générés et disponibles en téléchargement:")
print(f"   1. 📊 Données JSON:      {output_json.name}")
print(f"   2. 📑 Fiche réflexe PDF: {output_pdf.name}")
print()

if zones_detectees:
    print("📈 Résumé:")
    print(f"   • Total zones: {len(zones_detectees)}")
    print(f"   • Zones CRITIQUES: {sum(1 for z in zones_detectees if z['risque_niveau'] == 'CRITIQUE')}")
    print(f"   • Zones ÉLEVÉ: {sum(1 for z in zones_detectees if z['risque_niveau'] == 'ÉLEVÉ')}")
    print(f"   • Pages avec plans: {len(pages_plans)}")
    print()
    print("⚠️  RAPPEL SÉCURITÉ:")
    print("   • Port des EPI obligatoire (FFP3 minimum)")
    print("   • Validation SPS avant intervention")
    print("   • Balisage de toutes les zones")
else:
    print("ℹ️  Aucune zone avec amiante détectée")
    print()

print("="*80)
print()
