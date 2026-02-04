#!/bin/bash

# ============================================================================
# Script de Génération de la Structure GitHub Complète
# Analyseur de Rapports Amiante - MVP
# ============================================================================

echo "=================================="
echo "🚀 Création de la structure GitHub"
echo "=================================="
echo ""

# Nom du projet
PROJECT_NAME="analyseur-amiante-mvp"

# Créer le dossier racine
echo "📁 Création du dossier racine: $PROJECT_NAME"
mkdir -p $PROJECT_NAME
cd $PROJECT_NAME

# ============================================================================
# STRUCTURE DES DOSSIERS
# ============================================================================

echo "📂 Création de la structure des dossiers..."

# Créer tous les dossiers
mkdir -p .github/workflows
mkdir -p docs/images
mkdir -p src
mkdir -p tests
mkdir -p examples
mkdir -p web
mkdir -p test_data
mkdir -p output

# Créer .gitkeep pour les dossiers vides
touch test_data/.gitkeep
touch output/.gitkeep

echo "✅ Structure des dossiers créée"
echo ""

# ============================================================================
# FICHIERS RACINE
# ============================================================================

echo "📝 Création des fichiers racine..."

# .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Jupyter Notebook
.ipynb_checkpoints

# Pytest
.pytest_cache/
.coverage
htmlcov/

# Fichiers de sortie (généré par l'application)
/output/
/crops/
zones_dangereuses.json
fiche_reflexe.pdf
demo_*.pdf
demo_*.json

# Données sensibles (rapports amiante)
/data/rapports/*.pdf
/test_data/*.pdf
!test_data/exemple_rapport.pdf

# Logs
*.log
logs/

# Environnement
.env
.env.local

# Documentation générée
docs/_build/

# Fichiers temporaires
tmp/
temp/
*.tmp
EOF

# LICENSE
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Analyseur Amiante MVP

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

DISCLAIMER: This software is an aid tool for decision-making. It does NOT 
replace professional expertise from certified asbestos specialists. Always 
consult complete reports and qualified professionals before any intervention 
in areas containing asbestos materials.
EOF

# requirements.txt
cat > requirements.txt << 'EOF'
# MVP Document Intelligence - Rapports Amiante
# Dépendances Python pour l'analyse automatisée

# === Traitement PDF ===
pdfplumber>=0.10.0          # Extraction texte et tableaux avec précision de layout
PyMuPDF>=1.23.0             # (fitz) Manipulation avancée, coordonnées, rendering haute-res
pypdf>=3.17.0               # Opérations basiques PDF (fallback)

# === Traitement d'Images ===
Pillow>=10.1.0              # Manipulation images, annotations, crops
pdf2image>=1.16.3           # Conversion PDF → images (si OCR nécessaire)

# === OCR (Optionnel - pour PDFs scannés) ===
# Décommenter si traitement de PDFs scannés requis
# pytesseract>=0.3.10       # Interface Python pour Tesseract OCR
# Nécessite: sudo apt-get install tesseract-ocr tesseract-ocr-fra

# === Génération de Documents ===
reportlab>=4.0.7            # Création PDF professionnels (layout, tableaux, images)

# === Manipulation de Données ===
pandas>=2.1.0               # Traitement données tabulaires (optionnel mais recommandé)

# === Intégration LLM (Phase 2 - Optionnel) ===
# Décommenter pour nettoyage de données avec IA
# anthropic>=0.18.0         # API Claude pour structuration données ambiguës
# openai>=1.10.0            # Alternative: API OpenAI

# === Utilities ===
python-dateutil>=2.8.2      # Gestion dates pour métadonnées
EOF

# README.md (version courte avec lien vers fichiers détachés)
cat > README.md << 'EOF'
# 🏗️ Analyseur de Rapports Amiante - MVP

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-MVP-orange.svg)

**Application d'intelligence documentaire pour extraire automatiquement les zones dangereuses depuis des rapports amiante (DTA/RAAT) et générer des fiches réflexes pour la sécurité BTP.**

---

## 🚀 Installation Rapide

```bash
# Cloner le dépôt
git clone https://github.com/votre-username/analyseur-amiante-mvp.git
cd analyseur-amiante-mvp

# Installer les dépendances
pip install -r requirements.txt

# Analyser un rapport
python src/asbestos_report_analyzer.py /path/to/rapport.pdf
```

## ✨ Fonctionnalités

- 📊 **Extraction automatique** des zones avec amiante détecté
- 🗺️ **Localisation sur plans** avec coordonnées précises
- ✂️ **Génération de crops** annotés des zones dangereuses
- 📑 **Fiche réflexe PDF** de 2 pages maximum
- 💾 **Export JSON** structuré

## 📚 Documentation

- **[Guide de démarrage](QUICKSTART.md)** - Commencez en 5 minutes
- **[Architecture technique](docs/ARCHITECTURE_TECHNIQUE.md)** - Documentation approfondie
- **[Stratégie algorithmique](docs/STRATEGIE_LIAISON_TEXTE_PLAN.md)** - Comment ça marche

## 🎬 Démo

```bash
# Lancer la démo interactive
python examples/demo_interactive.py
```

## 📊 Résultats

```
output/
├── fiche_reflexe.pdf          # Fiche réflexe 2 pages
├── zones_dangereuses.json     # Données structurées
└── crops/                     # Images des plans
    ├── crop_P076.png
    └── ...
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📝 Licence

MIT License - Voir [LICENSE](LICENSE)

## ⚠️ Disclaimer

Cet outil est une aide à la décision. Il ne remplace pas l'expertise d'un professionnel certifié en amiante.

---

Made with ❤️ for BTP safety
EOF

echo "✅ Fichiers racine créés"
echo ""

# ============================================================================
# FICHIER CI/CD
# ============================================================================

echo "⚙️ Création de la configuration CI/CD..."

cat > .github/workflows/ci.yml << 'EOF'
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y poppler-utils
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python tests/test_analyzer.py

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install linting tools
      run: |
        pip install flake8 black
    
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
EOF

echo "✅ CI/CD configuré"
echo ""

# ============================================================================
# README pour test_data
# ============================================================================

cat > test_data/README.md << 'EOF'
# Test Data

Ce dossier contient les fichiers PDF de test.

## Usage

Placez vos rapports amiante de test ici :

```
test_data/
├── exemple_rapport.pdf        # Rapport de test
├── rapport_chantier_A.pdf     # Autre test
└── ...
```

⚠️ **IMPORTANT:** Ne commitez JAMAIS de vrais rapports amiante (données confidentielles)

Le `.gitignore` est configuré pour ignorer tous les PDFs sauf `exemple_rapport.pdf`.
EOF

# ============================================================================
# CONTRIBUTING.md
# ============================================================================

cat > CONTRIBUTING.md << 'EOF'
# Guide de Contribution

Merci de contribuer à l'Analyseur de Rapports Amiante !

## Comment contribuer

1. **Fork** le projet
2. Créez une **branche** : `git checkout -b feature/MaFeature`
3. **Committez** : `git commit -m 'Ajout de MaFeature'`
4. **Push** : `git push origin feature/MaFeature`
5. Ouvrez une **Pull Request**

## Standards de code

- Respecter PEP 8
- Ajouter des docstrings pour toutes les fonctions
- Inclure des tests pour les nouvelles fonctionnalités
- Mettre à jour la documentation

## Tests

```bash
python tests/test_analyzer.py
```

## Questions ?

Ouvrez une [issue](https://github.com/votre-username/analyseur-amiante-mvp/issues)
EOF

echo "✅ Fichiers de documentation créés"
echo ""

# ============================================================================
# AFFICHAGE FINAL
# ============================================================================

echo ""
echo "=================================="
echo "✅ Structure GitHub créée avec succès !"
echo "=================================="
echo ""
echo "📂 Structure créée :"
echo ""
tree -L 2 -a
echo ""
echo "📋 Prochaines étapes :"
echo ""
echo "1. Copiez vos fichiers Python dans les dossiers appropriés :"
echo "   - asbestos_report_analyzer.py → src/"
echo "   - test_analyzer.py → tests/"
echo "   - exemples_utilisation.py → examples/"
echo "   - demo_interactive.py → examples/"
echo "   - interface_analyseur.html → web/"
echo ""
echo "2. Copiez la documentation :"
echo "   - ARCHITECTURE_TECHNIQUE.md → docs/"
echo "   - STRATEGIE_LIAISON_TEXTE_PLAN.md → docs/"
echo "   - QUICKSTART.md → ./"
echo ""
echo "3. Initialisez Git :"
echo "   cd $PROJECT_NAME"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit - MVP v1.0'"
echo ""
echo "4. Publiez sur GitHub :"
echo "   git remote add origin https://github.com/votre-username/$PROJECT_NAME.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "=================================="
