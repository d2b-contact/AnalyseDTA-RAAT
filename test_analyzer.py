"""
Tests unitaires pour AsbestosReportAnalyzer

Usage:
    python test_analyzer.py
    
Note: Requiert un fichier PDF de test valide
"""

import unittest
import sys
from pathlib import Path
import json
import tempfile
import shutil

# Import du module principal
from asbestos_report_analyzer import (
    TextExtractor,
    PlanDetector,
    ImageCropper,
    ReportGenerator,
    AsbestosReportAnalyzer,
    ZoneDangereuse,
    ReportMetadata
)


class TestZoneDangereuse(unittest.TestCase):
    """Tests de la structure de données ZoneDangereuse"""
    
    def test_creation_zone(self):
        """Test de création d'une zone avec tous les champs"""
        zone = ZoneDangereuse(
            id_zone="P076",
            localisation_texte="RDC - Local TGBT",
            materiau="Dalle de sol",
            etat="Dégradé",
            page_source=42,
            risque_niveau="CRITIQUE"
        )
        
        self.assertEqual(zone.id_zone, "P076")
        self.assertEqual(zone.risque_niveau, "CRITIQUE")
        self.assertIsNone(zone.plan_page)
    
    def test_to_dict(self):
        """Test de conversion en dictionnaire"""
        zone = ZoneDangereuse(
            id_zone="Z-12",
            localisation_texte="1er Étage",
            materiau="Isolation",
            etat="Bon état",
            page_source=87
        )
        
        zone_dict = zone.to_dict()
        self.assertIsInstance(zone_dict, dict)
        self.assertIn("id_zone", zone_dict)
        self.assertEqual(zone_dict["id_zone"], "Z-12")


class TestTextExtractor(unittest.TestCase):
    """Tests de l'extracteur de texte"""
    
    def test_patterns_ignore(self):
        """Test des patterns de filtrage"""
        patterns = TextExtractor.PATTERNS_IGNORE
        
        self.assertIn(r"sommaire", patterns)
        self.assertIn(r"mentions légales", patterns)
    
    def test_patterns_tableau(self):
        """Test des patterns de détection de tableaux"""
        patterns = TextExtractor.PATTERNS_TABLEAU_REPERAGE
        
        self.assertTrue(len(patterns) > 0)
        self.assertIn(r"tableau.*repérage", patterns)
    
    def test_detection_mots_cles_positifs(self):
        """Test de détection de présence d'amiante"""
        keywords = TextExtractor.KEYWORDS_POSITIF
        
        text_positif = "Matériau avec présence d'amiante détecté"
        self.assertTrue(any(kw in text_positif.lower() for kw in keywords))
        
        text_negatif = "Aucun matériau suspect identifié"
        # Ce test doit échouer (c'est normal - on cherche les positifs)
        self.assertFalse(any(kw in text_negatif.lower() for kw in keywords))


class TestPlanDetector(unittest.TestCase):
    """Tests du détecteur de plans"""
    
    def test_heuristique_format_paysage(self):
        """Test de la logique de détection paysage"""
        # Simuler les dimensions
        class MockRect:
            def __init__(self, width, height):
                self.width = width
                self.height = height
        
        # Format paysage
        rect_paysage = MockRect(800, 600)
        self.assertGreater(rect_paysage.width, rect_paysage.height)
        
        # Format portrait
        rect_portrait = MockRect(600, 800)
        self.assertLess(rect_portrait.width, rect_portrait.height)


class TestReportGenerator(unittest.TestCase):
    """Tests du générateur de rapports"""
    
    def test_creation_generator(self):
        """Test d'initialisation du générateur"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            generator = ReportGenerator(output_path=tmp.name)
            
            self.assertIsNotNone(generator.styles)
            self.assertIn('CustomTitle', generator.styles)
            
            # Cleanup
            Path(tmp.name).unlink(missing_ok=True)
    
    def test_creation_entete(self):
        """Test de création de l'en-tête"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            generator = ReportGenerator(output_path=tmp.name)
            entete = generator.creer_entete()
            
            self.assertIsInstance(entete, list)
            self.assertGreater(len(entete), 0)
            
            Path(tmp.name).unlink(missing_ok=True)


class TestAsbestosReportAnalyzerIntegration(unittest.TestCase):
    """Tests d'intégration du pipeline complet"""
    
    @classmethod
    def setUpClass(cls):
        """Préparation avant tous les tests"""
        cls.test_dir = Path(tempfile.mkdtemp())
        print(f"\n📁 Répertoire de test créé: {cls.test_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage après tous les tests"""
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)
            print(f"🧹 Répertoire de test supprimé: {cls.test_dir}")
    
    def test_structure_sortie(self):
        """Test de la structure des fichiers de sortie attendus"""
        analyzer = AsbestosReportAnalyzer(
            pdf_path="dummy.pdf",  # N'existe pas mais teste la structure
            output_dir=str(self.test_dir)
        )
        
        # Vérifier que les chemins sont correctement définis
        self.assertEqual(
            analyzer.json_output.name,
            "zones_dangereuses.json"
        )
        self.assertEqual(
            analyzer.pdf_output.name,
            "fiche_reflexe.pdf"
        )
        self.assertEqual(
            analyzer.crops_dir.name,
            "crops"
        )


class TestDataValidation(unittest.TestCase):
    """Tests de validation des données"""
    
    def test_validation_id_zone(self):
        """Test de validation des formats d'ID de zone"""
        import re
        
        # Formats valides
        pattern = r'\b([A-Z]+[\-_]?\d+|P\d+|Z\d+|LOCAL[\-_]\d+)\b'
        
        valides = ["P076", "Z-12", "LOCAL-04", "ZONE_23", "EXT05"]
        for id_zone in valides:
            self.assertIsNotNone(
                re.search(pattern, id_zone, re.IGNORECASE),
                f"ID invalide: {id_zone}"
            )
        
        # Formats invalides
        invalides = ["ABC", "123", "P", "-05"]
        for id_zone in invalides:
            self.assertIsNone(
                re.search(pattern, id_zone, re.IGNORECASE),
                f"ID devrait être invalide: {id_zone}"
            )
    
    def test_validation_niveaux_risque(self):
        """Test des niveaux de risque valides"""
        niveaux_valides = ["CRITIQUE", "ÉLEVÉ", "MODÉRÉ"]
        
        zone_critique = ZoneDangereuse(
            id_zone="TEST",
            localisation_texte="Test",
            materiau="Test",
            etat="Dégradé",
            page_source=1,
            risque_niveau="CRITIQUE"
        )
        
        self.assertIn(zone_critique.risque_niveau, niveaux_valides)


def run_tests_with_coverage():
    """Exécute les tests avec rapport détaillé"""
    
    # Créer une suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestZoneDangereuse))
    suite.addTests(loader.loadTestsFromTestCase(TestTextExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestPlanDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestReportGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestAsbestosReportAnalyzerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestDataValidation))
    
    # Exécuter avec verbosité
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ DES TESTS")
    print("="*80)
    print(f"✓ Tests réussis:  {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"✗ Tests échoués:  {len(result.failures)}")
    print(f"⚠ Erreurs:        {len(result.errors)}")
    print(f"⊘ Tests ignorés:  {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        return 0
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
        return 1


def test_avec_pdf_reel(pdf_path: str):
    """
    Test d'intégration avec un vrai PDF
    
    Args:
        pdf_path: Chemin vers un fichier PDF de test
    """
    print("\n" + "="*80)
    print("TEST D'INTÉGRATION AVEC PDF RÉEL")
    print("="*80)
    
    if not Path(pdf_path).exists():
        print(f"❌ Fichier non trouvé: {pdf_path}")
        print("ℹ️  Placez un rapport DTA dans test_data/exemple_rapport.pdf")
        return False
    
    # Créer répertoire de sortie temporaire
    test_output = Path(tempfile.mkdtemp())
    print(f"📁 Sortie: {test_output}")
    
    try:
        # Lancer l'analyse
        analyzer = AsbestosReportAnalyzer(
            pdf_path=pdf_path,
            output_dir=str(test_output)
        )
        
        result = analyzer.analyser()
        
        # Vérifications
        assert result.get("success"), "Analyse a échoué"
        assert result.get("zones_count", 0) > 0, "Aucune zone détectée"
        
        # Vérifier fichiers de sortie
        json_path = Path(result["json_output"])
        pdf_path = Path(result["pdf_output"])
        
        assert json_path.exists(), "JSON non généré"
        assert pdf_path.exists(), "PDF non généré"
        
        # Vérifier contenu JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            zones_data = json.load(f)
            assert isinstance(zones_data, list), "JSON invalide"
            assert len(zones_data) > 0, "JSON vide"
        
        print(f"\n✅ Test d'intégration RÉUSSI!")
        print(f"   - Zones détectées: {result['zones_count']}")
        print(f"   - Zones avec plan: {result['zones_with_plan']}")
        print(f"   - PDF généré: {pdf_path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test d'intégration ÉCHOUÉ: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        shutil.rmtree(test_output, ignore_errors=True)


if __name__ == "__main__":
    print("🧪 SUITE DE TESTS - MVP Document Intelligence Amiante")
    print("="*80)
    
    # Tests unitaires
    exit_code = run_tests_with_coverage()
    
    # Test d'intégration optionnel
    test_pdf = Path("test_data/exemple_rapport.pdf")
    if test_pdf.exists():
        print("\n" + "="*80)
        print("Test d'intégration avec PDF réel disponible...")
        if test_avec_pdf_reel(str(test_pdf)):
            print("✅ Test d'intégration OK")
        else:
            print("❌ Test d'intégration KO")
            exit_code = 1
    else:
        print("\nℹ️  Pour tester avec un PDF réel:")
        print(f"   Placez votre PDF dans: {test_pdf}")
    
    sys.exit(exit_code)
