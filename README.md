# Scanner DNS

Un scanner DNS récursif et modulaire qui repose **exclusivement** sur des requêtes DNS. Visualise les résultats dans une interface terminal (TUI) hiérarchique, en utilisant rich.tree

## Fonctionnalités

- **DNS Pur** : Utilise uniquement des requêtes DNS standard (A, AAAA, MX, NS, PTR, SRV, TXT).
- **Scan Récursif** : Trouve un nouveau domaine/IP -> Le scanne immédiatement.
- **Stratégies** :
  - **Basique** : Enregistrements standard.
  - **Analyse TXT** : Extrait les IP/Domaines des champs SPF/DMARC.
  - **Brute-force SRV** : Trouve des services comme `_xmpp`, `_sip`.
  - **DNS Inverse** : Recherches PTR pour les IP.
  - **Déduction Parent** : Remonte jusqu'au domaine enregistré.
  - **Voisins** : Scanne les IP adjacentes (+1/-1).
  - **Sous-domaines** : Brute-force les préfixes courants.
- **TUI** : Tableau de bord en temps réel dans le terminal avec vue arborescente et statistiques.
- **Export Graphviz** : Exporte le graphe de découverte au format `.dot`.

## Installation

1. Cloner le dépôt.
2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

Lancer le scanner :
```bash
python main.py
```

- Entrez un **Domaine**.
- Définissez la **Profondeur** (limite de récursion).
- Cliquez sur **START SCAN** (ou Entrée si lancé en CLI).
- Utilisez **Export .dot** pour sauvegarder le graphe.

Ou via la ligne de commande directement :
```bash
python main.py --domain example.com --depth 3
```


