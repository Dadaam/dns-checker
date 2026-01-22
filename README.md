# DNS-Checker

Scanner DNS récursif qui cartographie l'infrastructure d'un domaine via requêtes DNS uniquement. Visualisation en graphe dans le terminal.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python main.py <domaine> [-d profondeur]
```

**Exemples :**
```bash
python main.py example.com          # Scan avec profondeur par défaut (3)
python main.py example.com -d 5     # Scan avec profondeur 5
```

## Fonctionnalités

- **Scan DNS pur** : A, AAAA, MX, NS, CNAME, TXT, PTR, SRV
- **Exploration récursive** : découverte automatique de nouveaux domaines/IPs
- **Visualisation** : graphe interactif dans le terminal (Rich TUI)
- **Export** : format DOT (Graphviz)

## Structure

```
src/
├── engine/      # Moteur de scan
├── models/      # Modèle de graphe
├── strategies/  # Stratégies DNS (A, MX, NS, TXT, PTR, SRV...)
└── tui/         # Interface terminal Rich
```

## Tests

```bash
pytest
```

## Dépendances

- `dnspython` - Requêtes DNS
- `networkx` - Graphe
- `rich` - Interface terminal

## Licence

MIT
