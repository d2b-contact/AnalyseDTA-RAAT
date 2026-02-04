#!/usr/bin/env python3
"""
Script d'exemple d'utilisation du MVP Document Intelligence Amiante

Ce script montre différents cas d'usage de l'analyseur.
"""

from pathlib import Path
import json
from asbestos_report_analyzer import AsbestosReportAnalyzer, ZoneDangereuse


def exemple_analyse_simple():
    """
    Cas d'usage 1: Analyse simple d'un rapport
    
    Le plus simple: un fichier PDF → génère fiche réflexe PDF + JSON
    """
    print("="*80)
    print("EXEMPLE 1: Analyse Simple")
    print("="*80)
    
    pdf_path = "test_data/exemple_rapport_dta.pdf"
    
    if not Path(pdf_path).exists():
        print(f"⚠️  Fichier non trouvé: {pdf_path}")
        print("   Placez un rapport DTA dans ce chemin pour tester.")
        return
    
    # Analyse en une ligne
    analyzer = AsbestosReportAnalyzer(pdf_path)
    result = analyzer.analyser()
    
    # Affichage résultats
    if result.get("success"):
        print(f"\n✅ Analyse réussie!")
        print(f"   📄 Zones détectées: {result['zones_count']}")
        print(f"   🗺️  Zones avec plan: {result['zones_with_plan']}")
        print(f"\n📥 Fichiers générés:")
        print(f"   • Fiche réflexe: {result['pdf_output']}")
        print(f"   • Données JSON: {result['json_output']}")
    else:
        print(f"❌ Erreur: {result.get('error', 'Inconnue')}")


def exemple_analyse_avec_options():
    """
    Cas d'usage 2: Analyse avec configuration personnalisée
    
    Permet de spécifier le répertoire de sortie, par exemple pour organiser
    les résultats par chantier ou par date.
    """
    print("\n" + "="*80)
    print("EXEMPLE 2: Analyse avec Répertoire Personnalisé")
    print("="*80)
    
    pdf_path = "test_data/exemple_rapport_dta.pdf"
    
    if not Path(pdf_path).exists():
        print(f"⚠️  Fichier non trouvé: {pdf_path}")
        return
    
    # Organisation par chantier
    chantier = "HOPITAL_NORD_2025"
    output_dir = f"/home/claude/rapports/{chantier}"
    
    analyzer = AsbestosReportAnalyzer(
        pdf_path=pdf_path,
        output_dir=output_dir
    )
    
    result = analyzer.analyser()
    
    if result.get("success"):
        print(f"\n✅ Rapport sauvegardé dans: {output_dir}")
        print(f"   Structure:")
        print(f"   {output_dir}/")
        print(f"   ├── fiche_reflexe.pdf")
        print(f"   ├── zones_dangereuses.json")
        print(f"   └── crops/")
        print(f"       ├── crop_P076.png")
        print(f"       ├── crop_Z-12.png")
        print(f"       └── ...")


def exemple_traitement_batch():
    """
    Cas d'usage 3: Traitement de plusieurs rapports
    
    Utile pour analyser tous les rapports d'un projet ou d'un client.
    """
    print("\n" + "="*80)
    print("EXEMPLE 3: Traitement Batch de Plusieurs Rapports")
    print("="*80)
    
    # Liste de rapports à traiter
    rapports = [
        "test_data/rapport_batiment_A.pdf",
        "test_data/rapport_batiment_B.pdf",
        "test_data/rapport_batiment_C.pdf"
    ]
    
    # Filtrer seulement les fichiers existants
    rapports_existants = [r for r in rapports if Path(r).exists()]
    
    if not rapports_existants:
        print("⚠️  Aucun fichier trouvé. Exemple de structure:")
        print("   test_data/")
        print("   ├── rapport_batiment_A.pdf")
        print("   ├── rapport_batiment_B.pdf")
        print("   └── rapport_batiment_C.pdf")
        return
    
    print(f"📂 {len(rapports_existants)} rapports à traiter...\n")
    
    resultats = []
    
    for i, pdf_path in enumerate(rapports_existants, 1):
        print(f"[{i}/{len(rapports_existants)}] Traitement: {Path(pdf_path).name}")
        
        # Répertoire de sortie basé sur le nom du fichier
        nom_fichier = Path(pdf_path).stem
        output_dir = f"/home/claude/batch_output/{nom_fichier}"
        
        analyzer = AsbestosReportAnalyzer(pdf_path, output_dir)
        result = analyzer.analyser()
        
        resultats.append({
            "fichier": Path(pdf_path).name,
            "success": result.get("success", False),
            "zones": result.get("zones_count", 0)
        })
        
        print(f"   → {'✅' if result.get('success') else '❌'} "
              f"{result.get('zones_count', 0)} zones détectées\n")
    
    # Résumé global
    print("\n" + "="*80)
    print("RÉSUMÉ DU TRAITEMENT BATCH")
    print("="*80)
    total_zones = sum(r['zones'] for r in resultats)
    succes = sum(1 for r in resultats if r['success'])
    
    print(f"📊 Statistiques:")
    print(f"   • Rapports traités: {len(resultats)}")
    print(f"   • Succès: {succes}/{len(resultats)}")
    print(f"   • Total zones détectées: {total_zones}")
    
    print(f"\n📄 Détails:")
    for r in resultats:
        status = "✅" if r['success'] else "❌"
        print(f"   {status} {r['fichier']}: {r['zones']} zones")


def exemple_exploitation_json():
    """
    Cas d'usage 4: Exploitation des données JSON
    
    Montre comment lire et exploiter les données structurées générées.
    """
    print("\n" + "="*80)
    print("EXEMPLE 4: Exploitation des Données JSON")
    print("="*80)
    
    json_path = "/home/claude/zones_dangereuses.json"
    
    if not Path(json_path).exists():
        print(f"⚠️  Fichier JSON non trouvé: {json_path}")
        print("   Exécutez d'abord une analyse pour générer le JSON.")
        return
    
    # Lecture du JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        zones = json.load(f)
    
    print(f"📊 Analyse de {len(zones)} zones...\n")
    
    # Statistiques
    zones_critiques = [z for z in zones if z['risque_niveau'] == 'CRITIQUE']
    zones_avec_plan = [z for z in zones if z['plan_page'] is not None]
    
    print(f"📈 Statistiques:")
    print(f"   • Zones CRITIQUES: {len(zones_critiques)} ({len(zones_critiques)/len(zones)*100:.1f}%)")
    print(f"   • Zones avec plan localisé: {len(zones_avec_plan)} ({len(zones_avec_plan)/len(zones)*100:.1f}%)")
    
    # Top 3 zones critiques
    print(f"\n⚠️  TOP 3 Zones à Risque CRITIQUE:")
    for i, zone in enumerate(zones_critiques[:3], 1):
        print(f"   {i}. {zone['id_zone']} - {zone['localisation_texte']}")
        print(f"      Matériau: {zone['materiau']}")
        print(f"      État: {zone['etat']}")
    
    # Liste des matériaux détectés
    materiaux = list(set(z['materiau'] for z in zones))
    print(f"\n🧱 Matériaux amiantés détectés ({len(materiaux)}):")
    for materiau in sorted(materiaux):
        count = sum(1 for z in zones if z['materiau'] == materiau)
        print(f"   • {materiau}: {count} occurrence(s)")
    
    # Export pour tableau Excel (exemple)
    print(f"\n💾 Export possible vers Excel:")
    print(f"   import pandas as pd")
    print(f"   df = pd.DataFrame(zones)")
    print(f"   df.to_excel('rapport_zones_amiante.xlsx', index=False)")


def exemple_integration_workflow():
    """
    Cas d'usage 5: Intégration dans un workflow métier
    
    Exemple d'intégration dans un processus d'entreprise.
    """
    print("\n" + "="*80)
    print("EXEMPLE 5: Intégration Workflow Métier")
    print("="*80)
    
    print("""
Scénario: Workflow de chantier automatisé

1. UPLOAD
   ┌────────────────────────────────────┐
   │ Diagnostic amiante reçu par email  │
   │ → Sauvegarde automatique dans NAS  │
   └────────────┬───────────────────────┘
                │
2. ANALYSE    ▼
   ┌────────────────────────────────────┐
   │ Script déclenché par cron/webhook  │
   │ → AsbestosReportAnalyzer.analyser()│
   └────────────┬───────────────────────┘
                │
3. VALIDATION ▼
   ┌────────────────────────────────────┐
   │ Coordonnateur SPS reçoit email     │
   │ avec fiche réflexe PDF en PJ       │
   └────────────┬───────────────────────┘
                │
4. DIFFUSION  ▼
   ┌────────────────────────────────────┐
   │ Si validation OK:                  │
   │ → Upload vers plateforme chantier  │
   │ → Notification équipes terrain     │
   │ → Archivage JSON dans BDD          │
   └────────────────────────────────────┘

Code d'intégration:
    """)
    
    code = '''
def workflow_automatise(pdf_path: str, projet_id: str):
    """Workflow complet automatisé"""
    
    # 1. Analyse
    analyzer = AsbestosReportAnalyzer(
        pdf_path=pdf_path,
        output_dir=f"/nas/projets/{projet_id}/amiante"
    )
    result = analyzer.analyser()
    
    if not result.get("success"):
        # Notification équipe SI en cas d'échec
        envoyer_alerte_echec(pdf_path, result.get("error"))
        return
    
    # 2. Validation manuelle (email au SPS)
    envoyer_email_validation(
        destinataire="sps@entreprise.com",
        sujet=f"Validation requise - Projet {projet_id}",
        fichier_pdf=result["pdf_output"],
        fichier_json=result["json_output"]
    )
    
    # 3. Enregistrement BDD
    enregistrer_rapport_bdd(
        projet_id=projet_id,
        zones=result["zones"],
        pdf_path=result["pdf_output"]
    )
    
    # 4. Notification équipes
    if result["zones_count"] > 0:
        envoyer_notification_terrain(
            projet_id=projet_id,
            message=f"⚠️ {result['zones_count']} zones amiante identifiées",
            lien_fiche=generer_lien_partage(result["pdf_output"])
        )
'''
    
    print(code)


def main():
    """Point d'entrée - Menu interactif"""
    print("\n" + "="*80)
    print("MVP DOCUMENT INTELLIGENCE AMIANTE - EXEMPLES D'UTILISATION")
    print("="*80)
    
    exemples = [
        ("Analyse Simple", exemple_analyse_simple),
        ("Analyse avec Options", exemple_analyse_avec_options),
        ("Traitement Batch", exemple_traitement_batch),
        ("Exploitation JSON", exemple_exploitation_json),
        ("Intégration Workflow", exemple_integration_workflow)
    ]
    
    print("\nExemples disponibles:")
    for i, (nom, _) in enumerate(exemples, 1):
        print(f"   {i}. {nom}")
    print(f"   0. Exécuter tous les exemples")
    
    try:
        choix = input("\nVotre choix (0-5): ").strip()
        
        if choix == "0":
            # Exécuter tous les exemples
            for nom, fonction in exemples:
                fonction()
        elif choix.isdigit() and 1 <= int(choix) <= len(exemples):
            # Exécuter l'exemple choisi
            exemples[int(choix) - 1][1]()
        else:
            print("Choix invalide.")
    except KeyboardInterrupt:
        print("\n\nInterruption utilisateur.")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")


if __name__ == "__main__":
    main()
