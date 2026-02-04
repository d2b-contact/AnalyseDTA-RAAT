"""
MVP - Document Intelligence pour Rapports Amiante
=================================================
Application critique pour la sécurité des électriciens en BTP.

Architecture modulaire pour extraire les zones dangereuses des rapports DTA/RAAT
et générer des fiches réflexes avec plans annotés.

Author: Lead Dev Python & IA Expert
Version: 1.1.0 MVP (Amélioré pour rapports Institut Galilé)

AMÉLIORATIONS v1.1.0:
- ✅ Support format "Prélèvement positif/négatif" (Institut Galilé)
- ✅ Détection IDs format "(P49)" et "n°49"
- ✅ Exclusion explicite des résultats négatifs
- ✅ Analyse ligne par ligne si pas de tableau structuré
- ✅ Patterns de détection élargis (20+ mots-clés)
"""

import json
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

# Imports PDF
import pdfplumber
import fitz  # PyMuPDF pour manipulation avancée des images et coordonnées

# Imports Image Processing
from PIL import Image, ImageDraw, ImageFont
import io

# Imports pour génération de rapport
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# STRUCTURES DE DONNÉES
# ============================================================================

@dataclass
class ZoneDangereuse:
    """Structure représentant une zone avec amiante détectée"""
    id_zone: str
    localisation_texte: str
    materiau: str
    etat: str
    page_source: int
    risque_niveau: str = "ÉLEVÉ"  # Par défaut
    
    # Coordonnées du plan (ajoutées après recherche visuelle)
    plan_page: Optional[int] = None
    plan_bbox: Optional[Tuple[float, float, float, float]] = None  # (x0, y0, x1, y1)
    plan_crop_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Conversion en dictionnaire pour JSON"""
        return asdict(self)


@dataclass
class ReportMetadata:
    """Métadonnées du rapport analysé"""
    filename: str
    total_pages: int
    zones_detectees: int
    zones_avec_plans: int
    date_traitement: str


# ============================================================================
# ÉTAPE 1 : EXTRACTION TEXTUELLE STRUCTURÉE
# ============================================================================

class TextExtractor:
    """
    Responsable de l'extraction intelligente du texte depuis le PDF.
    Filtre les pages pertinentes et extrait les tableaux de repérage.
    """
    
    # Patterns de détection
    PATTERNS_IGNORE = [
        r"sommaire",
        r"table des matières",
        r"mentions légales",
        r"conditions générales",
        r"page de garde"
    ]
    
    PATTERNS_TABLEAU_REPERAGE = [
        # Formats standards
        r"tableau.*repérage",
        r"résultats.*analyses",
        r"zones.*échantillon",
        r"repérage.*amiante",
        
        # Format Institut Galilé
        r"prélèvement.*positif",
        r"prelevement.*positif",
        r"liste.*prélèvements",
        r"liste.*prelevements",
        r"résultats.*prélèvements",
        r"resultats.*prelevements",
    ]
    
    # Mots-clés indiquant la présence d'amiante
    KEYWORDS_POSITIF = [
        # Format Institut Galilé (PRIORITAIRE)
        "prélèvement positif",
        "prelevement positif",
        
        # Formats standards
        "présence",
        "présence d'amiante",
        "détecté",
        "positif",
        "amiante",
        "matériau amianté",
        "amianté",
        
        # Résultats de laboratoire
        "chrysotile",
        "amosite",
        "crocidolite",
        
        # Autres variantes
        "trace",
        "mca",  # Matériau Contenant de l'Amiante
    ]
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf = None
        
    def __enter__(self):
        self.pdf = pdfplumber.open(self.pdf_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pdf:
            self.pdf.close()
    
    def est_page_pertinente(self, page_num: int, text: str) -> bool:
        """
        Détermine si une page contient des informations pertinentes.
        
        Stratégie:
        - Ignorer les 3 premières pages (sommaire, garde, intro)
        - Ignorer si contient des patterns d'exclusion
        - Accepter si contient des patterns de tableau de repérage
        """
        if page_num < 3:  # Réduit de 5 à 3
            logger.debug(f"Page {page_num}: ignorée (page de garde)")
            return False
        
        text_lower = text.lower()
        
        # Vérifier les patterns à ignorer
        for pattern in self.PATTERNS_IGNORE:
            if re.search(pattern, text_lower):
                logger.debug(f"Page {page_num}: ignorée (pattern: {pattern})")
                return False
        
        # Vérifier les patterns pertinents
        for pattern in self.PATTERNS_TABLEAU_REPERAGE:
            if re.search(pattern, text_lower):
                logger.info(f"Page {page_num}: pertinente (pattern: {pattern})")
                return True
        
        return False
    
    def extraire_tableaux(self, page) -> List[List[List[str]]]:
        """
        Extrait tous les tableaux d'une page avec pdfplumber.
        Retourne une liste de tableaux (chaque tableau est une liste de lignes).
        """
        try:
            tables = page.extract_tables()
            return tables if tables else []
        except Exception as e:
            logger.warning(f"Erreur extraction tableau page {page.page_number}: {e}")
            return []
    
    def analyser_ligne_tableau(self, row: List[str], page_num: int) -> Optional[ZoneDangereuse]:
        """
        Analyse une ligne de tableau pour détecter une zone dangereuse.
        
        Heuristique de détection:
        - Chercher colonne contenant un ID (ex: P076, Z-12, LOCAL-04)
        - Chercher colonne contenant localisation
        - Chercher colonne contenant matériau
        - Vérifier présence de mots-clés positifs
        """
        if not row or len(row) < 3:
            return None
        
        # Convertir None en string vide
        row = [str(cell).strip() if cell else "" for cell in row]
        
        # Joindre toute la ligne pour recherche de mots-clés
        row_text = " ".join(row).lower()
        
        # Vérifier si c'est une détection positive
        est_positif = any(keyword in row_text for keyword in self.KEYWORDS_POSITIF)
        
        # NOUVEAU: Exclure explicitement les résultats négatifs
        est_negatif = any(keyword in row_text for keyword in [
            "négatif", "negatif", "prélèvement négatif", "prelevement negatif",
            "absence", "non détecté", "non detecte"
        ])
        
        if not est_positif or est_negatif:
            return None
        
        # Extraction de l'ID de zone
        # NOUVEAU: Support format Institut Galilé: "002EW675245 n°49 - 1 (P49)"
        id_zone = None
        
        # Priorité 1: Format (PXX) - Institut Galilé
        match = re.search(r'\(P(\d+)\)', row_text, re.IGNORECASE)
        if match:
            id_zone = f"P{match.group(1)}"
        
        # Priorité 2: Format n°XX
        if not id_zone:
            match = re.search(r'n[°º]\s*(\d+)', row_text, re.IGNORECASE)
            if match:
                id_zone = f"P{match.group(1)}"
        
        # Priorité 3: Formats standards (P076, Z-12, LOCAL-04, etc.)
        if not id_zone:
            for cell in row[:3]:
                match = re.search(r'\b([A-Z]+[\-_]?\d+|P\d+|Z\d+|LOCAL[\-_]\d+)\b', cell, re.IGNORECASE)
                if match:
                    id_zone = match.group(1).upper()
                    break
        
        if not id_zone:
            logger.debug(f"Ligne positive mais ID zone non trouvé: {row}")
            return None
        
        # Extraction de la localisation (chercher la cellule la plus longue)
        localisation = max(row, key=len) if row else "Non spécifiée"
        
        # Extraction du matériau (chercher mots-clés comme dalle, plafond, cloison)
        materiaux_communs = ["dalle", "plafond", "cloison", "tuyau", "isolation", "enduit", "colle"]
        materiau = "Non spécifié"
        for cell in row:
            if any(mat in cell.lower() for mat in materiaux_communs):
                materiau = cell
                break
        
        # Détermination de l'état (dégradé, bon état, etc.)
        etats_possibles = ["dégradé", "bon état", "moyen", "détérioré", "friable"]
        etat = "Non évalué"
        for cell in row:
            for etat_possible in etats_possibles:
                if etat_possible in cell.lower():
                    etat = etat_possible.title()
                    break
        
        zone = ZoneDangereuse(
            id_zone=id_zone,
            localisation_texte=localisation,
            materiau=materiau,
            etat=etat,
            page_source=page_num,
            risque_niveau="CRITIQUE" if "dégradé" in etat.lower() else "ÉLEVÉ"
        )
        
        logger.info(f"✓ Zone dangereuse détectée: {zone.id_zone} - {zone.localisation_texte}")
        return zone
    
    def extraire_zones_dangereuses(self) -> List[ZoneDangereuse]:
        """Extraction ultra-tolérante par scan de texte brut."""
        zones = []
        KEYWORDS_DANGER = ["amiante", "présence", "positif", "détecté", "amianté", "contient"]
        
        logger.info("Scan global du texte par page...")

        for page_num, page in enumerate(self.pdf.pages, start=1):
            # Extraction avec layout=True pour garder la structure visuelle
            text = page.extract_text(layout=True)
            if not text:
                continue

            lines = text.split('\n')
            for line in lines:
                line_lower = line.lower()
                
                # Regex pour trouver l'ID (ex: P076, Z-12)
                match_id = re.search(r'\b([A-Z]{1,2}[- _]?\d{1,4})\b', line)
                
                if match_id:
                    id_found = match_id.group(1)
                    
                    # Si ID + mot de danger sur la même ligne
                    if any(k in line_lower for k in KEYWORDS_DANGER):
                        zone = ZoneDangereuse(
                            id_zone=id_found,
                            localisation_texte=line.strip()[:120],
                            materiau="Identifié par scan texte",
                            etat="Voir rapport",
                            page_source=page_num,
                            risque_niveau="CRITIQUE" if "dégradé" in line_lower else "ÉLEVÉ"
                        )
                        zones.append(zone)
                        logger.info(f"✓ Zone identifiée : {id_found} à la page {page_num}")

        # Nettoyage des doublons
        unique_zones = {z.id_zone: z for z in zones}.values()
        return list(unique_zones)

# ============================================================================
# ÉTAPE 2 : IDENTIFICATION ET TRAITEMENT DES PLANS
# ============================================================================

class PlanDetector:
    """
    Responsable de l'identification des pages de plans et de la localisation
    des zones sur ces plans via recherche textuelle + coordonnées.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = None  # PyMuPDF document
        
    def __enter__(self):
        self.doc = fitz.open(self.pdf_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.doc:
            self.doc.close()
    
    def est_page_plan(self, page) -> bool:
        """
        Détecte si une page est un plan architectural.
        
        Heuristiques:
        - Orientation paysage (width > height)
        - Peu de texte (ratio texte/surface faible)
        - Présence d'images ou dessins vectoriels
        """
        rect = page.rect
        width = rect.width
        height = rect.height
        
        # Critère 1: Format paysage
        est_paysage = width > height
        
        # Critère 2: Faible densité de texte
        text = page.get_text()
        text_length = len(text.strip())
        surface = width * height
        densite_texte = text_length / surface if surface > 0 else 0
        
        est_faible_texte = densite_texte < 0.5  # Seuil empirique
        
        # Critère 3: Présence d'images
        images = page.get_images()
        a_des_images = len(images) > 0
        
        # Décision
        est_plan = (est_paysage and est_faible_texte) or a_des_images
        
        if est_plan:
            logger.info(f"Page {page.number + 1}: identifiée comme PLAN (paysage={est_paysage}, img={len(images)})")
        
        return est_plan
    
    def chercher_zone_sur_plan(self, page, zone_id: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Recherche l'ID d'une zone sur un plan et retourne ses coordonnées.
        
        Args:
            page: Page PyMuPDF
            zone_id: ID à rechercher (ex: "P076")
            
        Returns:
            Tuple (x0, y0, x1, y1) de la bounding box si trouvé, None sinon
        """
        # Recherche exacte
        text_instances = page.search_for(zone_id)
        
        if text_instances:
            # Prendre la première occurrence
            bbox = text_instances[0]
            logger.info(f"  ✓ '{zone_id}' trouvé sur page {page.number + 1} à {bbox}")
            return tuple(bbox)
        
        # Tentative avec variations (minuscules, avec tiret, etc.)
        variations = [
            zone_id.lower(),
            zone_id.replace("-", ""),
            zone_id.replace("_", ""),
            zone_id.replace(" ", "")
        ]
        
        for variant in variations:
            text_instances = page.search_for(variant)
            if text_instances:
                bbox = text_instances[0]
                logger.info(f"  ✓ '{zone_id}' (variante: {variant}) trouvé sur page {page.number + 1}")
                return tuple(bbox)
        
        return None
    
    def lier_zones_aux_plans(self, zones: List[ZoneDangereuse]) -> List[ZoneDangereuse]:
        """
        Pour chaque zone, cherche sa localisation sur les plans du document.
        
        Stratégie:
        1. Identifier toutes les pages de plans
        2. Pour chaque zone, scanner tous les plans
        3. Associer la zone au premier plan où l'ID est trouvé
        """
        logger.info("Démarrage liaison zones ↔ plans...")
        
        # Étape 1: Identifier les pages de plans
        pages_plans = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            if self.est_page_plan(page):
                pages_plans.append(page_num)
        
        logger.info(f"✓ {len(pages_plans)} pages de plans identifiées: {pages_plans}")
        
        # Étape 2: Pour chaque zone, chercher sur les plans
        zones_liees = 0
        for zone in zones:
            logger.info(f"Recherche de '{zone.id_zone}' sur les plans...")
            
            for page_num in pages_plans:
                page = self.doc[page_num]
                bbox = self.chercher_zone_sur_plan(page, zone.id_zone)
                
                if bbox:
                    zone.plan_page = page_num + 1  # Indexation humaine
                    zone.plan_bbox = bbox
                    zones_liees += 1
                    break  # Prendre le premier plan trouvé
            
            if not zone.plan_bbox:
                logger.warning(f"  ✗ '{zone.id_zone}' non trouvé sur les plans")
        
        logger.info(f"✓ Liaison terminée: {zones_liees}/{len(zones)} zones liées à un plan")
        return zones


# ============================================================================
# ÉTAPE 3 : GÉNÉRATION DES ASSETS VISUELS
# ============================================================================

class ImageCropper:
    """
    Responsable de la génération des crops de plans avec mise en évidence.
    """
    
    def __init__(self, pdf_path: str, output_dir: str = "/home/claude/crops"):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.doc = None
        
    def __enter__(self):
        self.doc = fitz.open(self.pdf_path)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.doc:
            self.doc.close()
    
    def generer_crop(self, zone: ZoneDangereuse, crop_size: int = 800, dpi: int = 200) -> Optional[str]:
        """
        Génère un crop du plan centré sur la zone détectée.
        
        Args:
            zone: Zone dangereuse avec coordonnées
            crop_size: Taille du crop en pixels
            dpi: Résolution de rendu
            
        Returns:
            Chemin du fichier image généré, ou None si échec
        """
        if not zone.plan_page or not zone.plan_bbox:
            logger.warning(f"Zone {zone.id_zone}: pas de plan associé")
            return None
        
        page_num = zone.plan_page - 1  # Indexation 0-based
        page = self.doc[page_num]
        
        # Coordonnées du texte trouvé
        x0, y0, x1, y1 = zone.plan_bbox
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        
        # Calculer la zone de crop (carré centré)
        # Note: Les coordonnées PDF sont en points (1/72 inch)
        # Conversion en pixels selon DPI
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        
        # Définir rectangle de crop (en coordonnées PDF)
        half_size = crop_size / 2 * (72 / dpi)  # Convertir pixels → points
        crop_rect = fitz.Rect(
            center_x - half_size,
            center_y - half_size,
            center_x + half_size,
            center_y + half_size
        )
        
        # S'assurer que le crop reste dans les limites de la page
        page_rect = page.rect
        crop_rect = crop_rect & page_rect  # Intersection
        
        # Render la zone
        pix = page.get_pixmap(matrix=mat, clip=crop_rect)
        
        # Convertir en PIL Image pour annotations
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Ajouter annotations (cadre rouge autour de la zone)
        draw = ImageDraw.Draw(img)
        
        # Calculer position du texte dans le crop
        # Transformation: coordonnées PDF → coordonnées crop image
        text_x0 = (x0 - crop_rect.x0) * (dpi / 72)
        text_y0 = (y0 - crop_rect.y0) * (dpi / 72)
        text_x1 = (x1 - crop_rect.x0) * (dpi / 72)
        text_y1 = (y1 - crop_rect.y0) * (dpi / 72)
        
        # Cadre rouge autour du texte (élargi)
        padding = 10
        draw.rectangle(
            [text_x0 - padding, text_y0 - padding, text_x1 + padding, text_y1 + padding],
            outline="red",
            width=5
        )
        
        # Ajouter un label
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        label = f"ZONE {zone.id_zone}"
        # Positionner le label au-dessus du cadre
        draw.text((text_x0, text_y0 - 30), label, fill="red", font=font)
        
        # Sauvegarder
        output_path = self.output_dir / f"crop_{zone.id_zone}.png"
        img.save(output_path, "PNG")
        logger.info(f"✓ Crop généré: {output_path}")
        
        zone.plan_crop_path = str(output_path)
        return str(output_path)
    
    def generer_tous_les_crops(self, zones: List[ZoneDangereuse]) -> int:
        """
        Génère les crops pour toutes les zones.
        
        Returns:
            Nombre de crops générés avec succès
        """
        logger.info("Démarrage génération des crops...")
        count = 0
        
        for zone in zones:
            if self.generer_crop(zone):
                count += 1
        
        logger.info(f"✓ {count}/{len(zones)} crops générés")
        return count


# ============================================================================
# ÉTAPE 4 : GÉNÉRATION DU RAPPORT PDF
# ============================================================================

class ReportGenerator:
    """
    Génère la fiche réflexe PDF de 2 pages maximum.
    """
    
    def __init__(self, output_path: str = "/home/claude/fiche_reflexe.pdf"):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self._configurer_styles()
        
    def _configurer_styles(self):
        """Configuration des styles personnalisés"""
        # Style pour titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#CC0000'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Style pour zone dangereuse
        self.styles.add(ParagraphStyle(
            name='DangerZone',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#CC0000'),
            spaceAfter=6
        ))
        
        # Style pour détails
        self.styles.add(ParagraphStyle(
            name='Details',
            parent=self.styles['Normal'],
            fontSize=9,
            leftIndent=10
        ))
    
    def creer_entete(self) -> List:
        """Crée l'en-tête du rapport"""
        story = []
        
        # Titre principal
        titre = Paragraph("⚠ FICHE RÉFLEXE - ZONES AMIANTE DÉTECTÉES ⚠", self.styles['CustomTitle'])
        story.append(titre)
        story.append(Spacer(1, 6*mm))
        
        # Avertissement
        warning = Paragraph(
            "<b>ATTENTION:</b> Ce document liste <u>uniquement</u> les zones à RISQUE ÉLEVÉ. "
            "Port des EPI obligatoire. Consulter le rapport complet avant intervention.",
            self.styles['Normal']
        )
        story.append(warning)
        story.append(Spacer(1, 8*mm))
        
        return story
    
    def creer_bloc_zone(self, zone: ZoneDangereuse) -> List:
        """
        Crée un bloc pour une zone dangereuse.
        Format: Texte à gauche, image du plan à droite.
        """
        story = []
        
        # Données textuelles
        zone_title = Paragraph(
            f"<b>ZONE {zone.id_zone}</b> - {zone.risque_niveau}",
            self.styles['DangerZone']
        )
        
        localisation = Paragraph(
            f"<b>Localisation:</b> {zone.localisation_texte}",
            self.styles['Details']
        )
        
        materiau = Paragraph(
            f"<b>Matériau:</b> {zone.materiau}",
            self.styles['Details']
        )
        
        etat = Paragraph(
            f"<b>État:</b> {zone.etat}",
            self.styles['Details']
        )
        
        # Colonne texte
        texte_data = [[zone_title], [localisation], [materiau], [etat]]
        
        if zone.plan_crop_path and Path(zone.plan_crop_path).exists():
            # Image disponible - Layout côte à côte
            img = RLImage(zone.plan_crop_path, width=60*mm, height=60*mm)
            
            # Table 2 colonnes: texte | image
            table_data = [
                [Table(texte_data, colWidths=[90*mm]), img]
            ]
            
            table = Table(table_data, colWidths=[90*mm, 70*mm])
            table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            story.append(table)
        else:
            # Pas d'image - Texte seul
            table = Table(texte_data, colWidths=[160*mm])
            story.append(table)
            
            # Message si plan non trouvé
            no_plan = Paragraph(
                "<i>Plan non localisé - Consulter rapport complet page " + 
                str(zone.page_source) + "</i>",
                self.styles['Details']
            )
            story.append(no_plan)
        
        story.append(Spacer(1, 6*mm))
        
        # Ligne de séparation
        story.append(Spacer(1, 2*mm))
        
        return story
    
    def generer(self, zones: List[ZoneDangereuse], metadata: ReportMetadata) -> str:
        """
        Génère le PDF de la fiche réflexe.
        
        Args:
            zones: Liste des zones dangereuses
            metadata: Métadonnées du rapport
            
        Returns:
            Chemin du fichier PDF généré
        """
        logger.info(f"Génération du rapport: {self.output_path}")
        
        # Configuration du document
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=15*mm
        )
        
        story = []
        
        # En-tête
        story.extend(self.creer_entete())
        
        # Ajouter chaque zone (maximum 2 pages)
        zones_affichees = zones[:6]  # Limiter à ~6 zones pour tenir sur 2 pages
        
        for zone in zones_affichees:
            story.extend(self.creer_bloc_zone(zone))
        
        # Si plus de zones que la capacité
        if len(zones) > 6:
            message = Paragraph(
                f"<b>NOTE:</b> {len(zones) - 6} zone(s) supplémentaire(s) non affichée(s). "
                f"Consulter le fichier JSON complet.",
                self.styles['Normal']
            )
            story.append(message)
        
        # Footer
        story.append(Spacer(1, 10*mm))
        footer = Paragraph(
            f"<i>Document généré automatiquement - Source: {metadata.filename} - "
            f"{metadata.zones_detectees} zones à risque identifiées</i>",
            self.styles['Normal']
        )
        story.append(footer)
        
        # Construction du PDF
        doc.build(story)
        logger.info(f"✓ Rapport PDF généré: {self.output_path}")
        
        return self.output_path


# ============================================================================
# ORCHESTRATEUR PRINCIPAL
# ============================================================================

class AsbestosReportAnalyzer:
    """
    Orchestrateur principal du pipeline d'analyse.
    """
    
    def __init__(self, pdf_path: str, output_dir: str = "/home/claude"):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Chemins de sortie
        self.json_output = self.output_dir / "zones_dangereuses.json"
        self.pdf_output = self.output_dir / "fiche_reflexe.pdf"
        self.crops_dir = self.output_dir / "crops"
        
    def analyser(self) -> Dict:
        """
        Pipeline complet d'analyse.
        
        Returns:
            Dictionnaire avec résultats et statistiques
        """
        from datetime import datetime
        
        logger.info("="*80)
        logger.info("DÉMARRAGE ANALYSE RAPPORT AMIANTE")
        logger.info("="*80)
        
        # Étape 1: Extraction textuelle
        logger.info("\n[ÉTAPE 1/4] Extraction textuelle structurée")
        logger.info("-" * 80)
        
        with TextExtractor(self.pdf_path) as extractor:
            zones = extractor.extraire_zones_dangereuses()
        
        if not zones:
            logger.error("❌ Aucune zone dangereuse détectée. Vérifier le format du PDF.")
            return {"error": "Aucune zone détectée"}
        
        # Étape 2: Liaison avec les plans
        logger.info("\n[ÉTAPE 2/4] Identification et liaison des plans")
        logger.info("-" * 80)
        
        with PlanDetector(self.pdf_path) as detector:
            zones = detector.lier_zones_aux_plans(zones)
        
        # Étape 3: Génération des crops
        logger.info("\n[ÉTAPE 3/4] Génération des assets visuels")
        logger.info("-" * 80)
        
        with ImageCropper(self.pdf_path, str(self.crops_dir)) as cropper:
            crops_count = cropper.generer_tous_les_crops(zones)
        
        # Étape 4: Génération du rapport PDF
        logger.info("\n[ÉTAPE 4/4] Génération de la fiche réflexe")
        logger.info("-" * 80)
        
        metadata = ReportMetadata(
            filename=Path(self.pdf_path).name,
            total_pages=0,  # À implémenter si nécessaire
            zones_detectees=len(zones),
            zones_avec_plans=crops_count,
            date_traitement=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        generator = ReportGenerator(str(self.pdf_output))
        pdf_path = generator.generer(zones, metadata)
        
        # Sauvegarde JSON
        zones_dict = [zone.to_dict() for zone in zones]
        with open(self.json_output, 'w', encoding='utf-8') as f:
            json.dump(zones_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ Données JSON sauvegardées: {self.json_output}")
        
        # Résumé
        logger.info("\n" + "="*80)
        logger.info("ANALYSE TERMINÉE")
        logger.info("="*80)
        logger.info(f"✓ Zones dangereuses détectées: {len(zones)}")
        logger.info(f"✓ Zones avec plan localisé: {crops_count}")
        logger.info(f"✓ Fiche réflexe PDF: {pdf_path}")
        logger.info(f"✓ Données JSON: {self.json_output}")
        
        return {
            "success": True,
            "zones_count": len(zones),
            "zones_with_plan": crops_count,
            "pdf_output": str(pdf_path),
            "json_output": str(self.json_output),
            "zones": zones_dict
        }


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

def main():
    """Point d'entrée du script"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python asbestos_report_analyzer.py <chemin_rapport.pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Erreur: Le fichier {pdf_path} n'existe pas")
        sys.exit(1)
    
    # Lancement de l'analyse
    analyzer = AsbestosReportAnalyzer(pdf_path)
    result = analyzer.analyser()
    
    if result.get("success"):
        print("\n✅ Analyse réussie!")
        print(f"📄 Fiche réflexe: {result['pdf_output']}")
        print(f"📊 Données JSON: {result['json_output']}")
    else:
        print("\n❌ Échec de l'analyse")
        sys.exit(1)


if __name__ == "__main__":
    main()
