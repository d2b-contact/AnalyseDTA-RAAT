# 🚀 Guide de Démarrage Rapide

Ce guide vous permet de démarrer avec l'analyseur en **moins de 5 minutes**.

---

## ⚡ Installation Express

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-username/analyseur-amiante-mvp.git
cd analyseur-amiante-mvp
```

### 2. Installer les dépendances

**Option A - Avec pip :**
```bash
pip install -r requirements.txt
```

**Option B - Avec environnement virtuel (recommandé) :**
```bash
# Créer l'environnement
python -m venv venv

# Activer l'environnement
# Sur Windows:
venv\Scripts\activate
# Sur Mac/Linux:
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

---

## 🎯 Premier Test

### Option 1 : Démo automatique (sans PDF)

```bash
python demo_interactive.py
```

**Ce que fait la démo :**
- ✅ Crée un rapport amiante synthétique de 4 pages
- ✅ L'analyse automatiquement
- ✅ Génère la fiche réflexe PDF
- ✅ Exporte les données JSON

**Résultats dans :** `demo_*.pdf` et `demo_*.json`

---

### Option 2 : Analyser votre propre rapport

```bash
python asbestos_report_analyzer.py /chemin/vers/votre_rapport.pdf
```

**Résultats dans :** `./fiche_reflexe.pdf` et `./zones_dangereuses.json`

---

## 📊 Exemple de Sortie

### Fiche Réflexe PDF (2 pages)

```
┌─────────────────────────────────────────┐
│   ⚠ FICHE RÉFLEXE - ZONES AMIANTE ⚠   │
├─────────────────────────────────────────┤
│                                         │
│  🔴 ZONE P076 - CRITIQUE                │
│  ├─ Localisation: RDC Aile Nord        │
│  ├─ Matériau: Dalle de sol             │
│  └─ État: Dégradé                       │
│     [Image du plan avec zone encadrée]  │
│                                         │
│  🟠 ZONE Z-12 - ÉLEVÉ                   │
│  ├─ Localisation: 1er Étage            │
│  ├─ Matériau: Isolation tuyauterie     │
│  └─ État: Bon état                      │
│     [Image du plan avec zone encadrée]  │
│                                         │
└─────────────────────────────────────────┘
```

### Données JSON

```json
{
  "metadata": {
    "zones_detectees": 2,
    "zones_critiques": 1
  },
  "zones": [
    {
      "id_zone": "P076",
      "localisation_texte": "RDC Aile Nord - Local TGBT",
      "materiau": "Dalle de sol vinyle-amiante",
      "etat": "Dégradé",
      "risque_niveau": "CRITIQUE"
    }
  ]
}
```

---

## 🔧 Configuration Avancée

### Personnaliser le répertoire de sortie

```bash
python asbestos_report_analyzer.py rapport.pdf --output ./resultats_chantier_A/
```

### Utilisation en Python

```python
from asbestos_report_analyzer import AsbestosReportAnalyzer

analyzer = AsbestosReportAnalyzer(
    pdf_path="rapport.pdf",
    output_dir="./output"
)

result = analyzer.analyser()

# Accéder aux résultats
print(f"Zones détectées: {result['zones_count']}")
print(f"PDF généré: {result['pdf_output']}")
```

---

## 🧪 Tests

### Tester avec vos propres données

1. Placez votre rapport PDF dans `test_data/`
2. Lancez :
   ```bash
   python test_analyzer.py
   ```

### Tests unitaires complets

```bash
python test_analyzer.py
```

---

## 📁 Structure des Fichiers de Sortie

```
output/
├── fiche_reflexe.pdf          # Fiche réflexe 2 pages
├── zones_dangereuses.json     # Données structurées
└── crops/                     # Images des plans annotées
    ├── crop_P076.png
    ├── crop_Z-12.png
    └── crop_LOCAL-04.png
```

---

## 🎨 Interface Web (Optionnel)

Pour une interface graphique avec drag & drop :

```bash
# Ouvrir dans votre navigateur
open interface_analyseur.html
```

**Fonctionnalités :**
- Upload par drag & drop
- Visualisation temps réel des résultats
- Téléchargement JSON/PDF

---

## ❓ Résolution de Problèmes

### Erreur : "No module named 'fitz'"

```bash
pip install PyMuPDF
```

### Erreur : "PDF file is encrypted"

Votre PDF est protégé. Déverrouillez-le avec :
```bash
qpdf --decrypt --password=MOTDEPASSE input.pdf output.pdf
```

### Aucune zone détectée

**Causes possibles :**
1. Le format du tableau n'est pas reconnu
2. Les mots-clés de détection ne correspondent pas
3. Le PDF est scanné sans OCR

**Solutions :**
- Vérifier les patterns dans `TextExtractor.KEYWORDS_POSITIF`
- Activer l'OCR (voir documentation avancée)

### Performance lente (> 2 min pour 500 pages)

**Optimisations :**
1. Vérifier que le PDF n'est pas en haute résolution inutile
2. Activer le mode "fast" (à venir en v2.0)
3. Utiliser un SSD plutôt qu'un HDD

---

## 🆘 Besoin d'Aide ?

- 📖 **Documentation complète** : [README.md](README.md)
- 🏗️ **Architecture technique** : [ARCHITECTURE_TECHNIQUE.md](ARCHITECTURE_TECHNIQUE.md)
- 🐛 **Signaler un bug** : [GitHub Issues](https://github.com/votre-username/analyseur-amiante-mvp/issues)

---

## ✅ Checklist de Démarrage

- [ ] Cloner le dépôt
- [ ] Installer les dépendances
- [ ] Lancer la démo automatique
- [ ] Tester avec un rapport réel
- [ ] Consulter la documentation complète

---

**Temps estimé pour tout ce guide : 5 minutes** ⏱️

Vous êtes prêt ! 🎉
