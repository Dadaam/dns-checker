# DNS-Checker

Scanner DNS récursif et modulaire qui repose exclusivement sur des requêtes DNS. Il explore automatiquement l'infrastructure DNS d'un domaine cible et visualise les résultats sous forme de graphe dans le terminal.

---

## Table des matieres

1. [Presentation](#presentation)
2. [Fonctionnalites](#fonctionnalites)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Utilisation](#utilisation)
6. [Strategies de scan](#strategies-de-scan)
7. [Structure du projet](#structure-du-projet)
8. [Modele de donnees](#modele-de-donnees)
9. [Export et visualisation](#export-et-visualisation)
10. [Tests](#tests)
11. [Limitations connues](#limitations-connues)
12. [Contribuer](#contribuer)
13. [Licence](#licence)

---

## Presentation

DNS-Checker est un outil d'exploration DNS qui permet de cartographier l'infrastructure d'un domaine en effectuant uniquement des requetes DNS.  Contrairement aux outils de reconnaissance classiques, il n'utilise ni WHOIS, ni requetes HTTP, ni scraping web.

L'outil fonctionne de maniere recursive :  chaque nouvelle entite decouverte (domaine, adresse IP) devient une nouvelle cible a analyser, jusqu'a atteindre une profondeur maximale configurable.

### Cas d'usage

- Audit de securite : identifier les serveurs exposes, les configurations SPF/DMARC
- Cartographie d'infrastructure : visualiser les relations entre domaines et IPs
- Analyse forensique : tracer les dependances DNS d'un domaine
- Apprentissage :  comprendre le fonctionnement du systeme DNS

---

## Fonctionnalites

### Scan DNS pur

- Interrogation des enregistrements A, AAAA, MX, NS, CNAME, TXT, PTR
- Aucune dependance a des services externes (WHOIS, APIs tierces)
- Timeout configurable pour eviter les blocages

### Exploration recursive

- Decouverte automatique de nouveaux domaines et IPs
- Controle de la profondeur de recursion
- Detection des cycles pour eviter les boucles infinies

### Analyse intelligente

- Extraction des IPs et domaines caches dans les enregistrements SPF/DMARC
- Resolution DNS inverse (PTR) pour identifier les hostnames des IPs
- Deduction des domaines parents

### Interface terminal

- Affichage en temps reel avec arbre hierarchique colore
- Statistiques de scan (noeuds, aretes, duree)
- Export du graphe au format Graphviz (.dot)

---

## Architecture

Le projet suit une architecture modulaire basee sur le pattern Strategy : 

```
                    +------------------+
                    |     main.py      |
                    | (Point d'entree) |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |   RichDNSApp     |
                    |  (Interface TUI) |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |  ScannerEngine   |
                    |  (Moteur DFS)    |
                    +--------+---------+
                             |
          +------------------+------------------+
          |                  |                  |
          v                  v                  v
   +-------------+    +-------------+    +-------------+
   | BasicDNS    |    | TxtStrategy |    | PtrStrategy |
   | Strategy    |    |             |    |             |
   +-------------+    +-------------+    +-------------+
          |                  |                  |
          +------------------+------------------+
                             |
                             v
                    +------------------+
                    |    dnspython     |
                    | (Requetes DNS)   |
                    +------------------+
```

### Composants principaux

| Composant | Role |
|-----------|------|
| `main.py` | Point d'entree, parsing des arguments CLI |
| `ScannerEngine` | Moteur de scan avec algorithme DFS iteratif |
| `Strategy` | Interface abstraite pour les strategies de scan |
| `RichDNSApp` | Interface utilisateur terminal avec Rich |
| `Node` / `Edge` | Structures de donnees du graphe |

---

## Installation

### Prerequis

- Python 3.8 ou superieur
- pip (gestionnaire de paquets Python)

### Etapes

1. Cloner le depot : 
   ```bash
   git clone https://github.com/Dadaam/dns-checker.git
   cd dns-checker
   ```

2. Creer un environnement virtuel (recommande) :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # ou
   venv\Scripts\activate     # Windows
   ```

3. Installer les dependances :
   ```bash
   pip install -r requirements. txt
   ```

### Dependances

| Paquet | Version | Description |
|--------|---------|-------------|
| dnspython | >= 2.0 | Bibliotheque de requetes DNS |
| rich | >= 13.0 | Affichage terminal avance |
| tldextract | >= 3.0 | Extraction des composants de domaine |
| networkx | >= 3.0 | Manipulation de graphes |
| pytest | >= 7.0 | Framework de tests (developpement) |

---

## Utilisation

### Mode interactif

Lancer le scanner sans arguments pour entrer le domaine et la profondeur de maniere interactive :

```bash
python main.py
```

L'application demande alors : 
- Le domaine cible
- La profondeur de recursion (defaut : 3)

### Mode ligne de commande

Specifier directement le domaine et les options :

```bash
# Scan basique
python main.py example.com

# Scan avec profondeur personnalisee
python main.py example.com -d 5
python main.py example.com --depth 5
```

### Options disponibles

| Option | Format court | Description | Defaut |
|--------|--------------|-------------|--------|
| `domain` | - | Domaine cible a scanner | (interactif) |
| `--depth` | `-d` | Profondeur maximale de recursion | 3 |

### Exemple de sortie

```
Scan:  google.com (profondeur 3)
Scan termine en 2.34s
Nodes: 47 | Edges: 52

Carte des resultats:
google.com [DOMAIN]  ROOT
├── A  142.250.185.46 [IP_V4]
│   └── PTR  par21s17-in-f14.1e100.net [DOMAIN]
├── A  142.250.185.78 [IP_V4]
├── AAAA  2a00:1450:4007:80e::200e [IP_V6]
├── NS  ns1.google.com [DOMAIN]
│   └── A  216.239.32.10 [IP_V4]
├── NS  ns2.google.com [DOMAIN]
├── MX  smtp.google.com [DOMAIN]
└── TXT  _spf. google.com [DOMAIN]
    └── TXT  _netblocks.google.com [DOMAIN]

Generation du DOT... 
Saved ./scan. dot
```

---

## Strategies de scan

Le moteur de scan utilise un systeme de strategies modulaires.  Chaque strategie est responsable d'un type d'analyse specifique. 

### BasicDNSStrategy

Interroge les enregistrements DNS standards. 

| Type d'enregistrement | Description | Resultat |
|----------------------|-------------|----------|
| A | Adresse IPv4 | Noeud IP_V4 |
| AAAA | Adresse IPv6 | Noeud IP_V6 |
| MX | Serveur de messagerie | Noeud DOMAIN |
| NS | Serveur de noms | Noeud DOMAIN |
| CNAME | Alias canonique | Noeud DOMAIN |
| TXT | Enregistrement texte | Noeud TXT |

### TxtStrategy

Analyse le contenu des enregistrements TXT pour extraire des informations cachees. 

Patterns detectes :
- `ip4: X.X.X.X` : Adresses IPv4 dans les enregistrements SPF
- `ip6:XXXX:... ` : Adresses IPv6 dans les enregistrements SPF
- `include:domain. com` : Domaines inclus dans SPF
- `redirect=domain.com` : Redirections SPF

Exemple d'enregistrement SPF analyse :
```
v=spf1 ip4:192.168.1.1 include:_spf.google.com ~all
```
Resultat : decouverte de l'IP `192.168.1.1` et du domaine `_spf.google.com`

### PtrStrategy

Effectue des resolutions DNS inverses sur les adresses IP pour retrouver les hostnames associes.

Fonctionnement :
1. Recoit un noeud de type IP_V4 ou IP_V6
2. Convertit l'IP en format in-addr.arpa (ex: `8.8.8.8` devient `8.8.8.8.in-addr.arpa`)
3. Interroge l'enregistrement PTR
4. Retourne le hostname associe

### ParentStrategy

Deduit les domaines parents jusqu'au domaine enregistrable.

Exemple :
```
mail.subdomain.example.com
        |
        v (parent)
subdomain.example.com
        |
        v (parent)
example.com  <- domaine enregistrable, arret
```

La strategie utilise `tldextract` pour identifier correctement le suffixe public (TLD) et eviter de scanner les TLD eux-memes (. com, .fr, .co.uk, etc.).

### Ajouter une nouvelle strategie

Pour creer une nouvelle strategie de scan : 

1. Creer un fichier dans `src/strategies/`
2. Heriter de la classe `Strategy`
3. Implementer la methode `execute()`

```python
from src.strategies.base import Strategy
from src.models.graph import Node, Edge, NodeType, EdgeType

class MaStrategie(Strategy):
    def execute(self, node: Node):
        if node.type != NodeType.DOMAIN:
            return
        
        # Logique de scan
        nouveau_noeud = Node(value="resultat", type=NodeType. DOMAIN)
        arete = Edge(source=node, target=nouveau_noeud, type=EdgeType. A)
        yield nouveau_noeud, arete
```

4. Enregistrer la strategie dans `RichDNSApp. register_strategies()`

---

## Structure du projet

```
dns-checker/
├── main.py                     # Point d'entree CLI
├── requirements.txt            # Dependances Python
├── README.md                   # Documentation
├── scan.dot                    # Fichier de sortie Graphviz (genere)
│
├── src/                        # Code source principal
│   ├── __init__.py
│   │
│   ├── engine/                 # Moteur de scan
│   │   ├── __init__.py
│   │   └── core.py             # Classe ScannerEngine
│   │
│   ├── models/                 # Structures de donnees
│   │   ├── __init__.py
│   │   └── graph. py            # Node, Edge, NodeType, EdgeType
│   │
│   ├── strategies/             # Strategies de scan
│   │   ├── __init__. py
│   │   ├── base.py             # Classe abstraite Strategy
│   │   ├── dns. py              # BasicDNSStrategy
│   │   ├── txt.py              # TxtStrategy
│   │   ├── ptr.py              # PtrStrategy
│   │   └── parents.py          # ParentStrategy
│   │
│   └── tui/                    # Interfaces utilisateur
│       ├── __init__.py
│       ├── rich_app.py         # Application Rich (principale)
│       ├── textual_app.py      # Application Textual (alternative)
│       ├── ttk_app.py          # Application TermTk (alternative)
│       └── widgets/            # Composants graphiques
│           ├── graph. py
│           └── ttk_graph.py
│
├── tests/                      # Tests unitaires
│   ├── __init__.py
│   ├── test_engine.py
│   └── test_strategies.py
│
└── utils/                      # Utilitaires
    └── __init__.py
```

### Description des fichiers cles

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `src/engine/core.py` | ~70 | Moteur de scan DFS iteratif |
| `src/models/graph.py` | ~40 | Definitions des noeuds et aretes |
| `src/strategies/dns.py` | ~50 | Requetes DNS standards |
| `src/strategies/txt.py` | ~60 | Analyse des enregistrements TXT |
| `src/strategies/ptr.py` | ~30 | Resolution DNS inverse |
| `src/strategies/parents.py` | ~40 | Deduction des parents |
| `src/tui/rich_app.py` | ~210 | Interface utilisateur Rich |

---

## Modele de donnees

### Types de noeuds (NodeType)

| Type | Description | Exemple |
|------|-------------|---------|
| DOMAIN | Nom de domaine | google.com |
| IP_V4 | Adresse IPv4 | 142.250.185.46 |
| IP_V6 | Adresse IPv6 | 2a00:1450:4007:80e::200e |
| TLD | Top-Level Domain | com |
| SERVICE | Service SRV | _xmpp._tcp.example.com |
| TXT | Contenu TXT brut | v=spf1 ...  |

### Types d'aretes (EdgeType)

| Type | Description | Source -> Cible |
|------|-------------|-----------------|
| A | Enregistrement A | DOMAIN -> IP_V4 |
| AAAA | Enregistrement AAAA | DOMAIN -> IP_V6 |
| CNAME | Alias canonique | DOMAIN -> DOMAIN |
| NS | Serveur de noms | DOMAIN -> DOMAIN |
| MX | Serveur mail | DOMAIN -> DOMAIN |
| PTR | DNS inverse | IP -> DOMAIN |
| TXT | Extrait de TXT | DOMAIN -> IP/DOMAIN |
| PARENT | Domaine parent | DOMAIN -> DOMAIN |

### Structure des objets

```python
# Noeud (immuable)
@dataclass(frozen=True)
class Node:
    value: str       # ex: "google.com"
    type: NodeType   # ex:  NodeType.DOMAIN

# Arete (immuable)
@dataclass(frozen=True)
class Edge:
    source: Node     # Noeud source
    target: Node     # Noeud cible
    type: EdgeType   # Type de relation
```

L'attribut `frozen=True` rend les objets immuables, ce qui permet de les utiliser dans des ensembles (sets) et comme cles de dictionnaires.

---

## Export et visualisation

### Format Graphviz (. dot)

Apres chaque scan, un fichier `scan.dot` est genere. Ce fichier peut etre converti en image avec Graphviz. 

Installation de Graphviz :
```bash
# Ubuntu/Debian
sudo apt install graphviz

# macOS
brew install graphviz

# Windows
choco install graphviz
```

Conversion en image :
```bash
# PNG
dot -Tpng scan.dot -o scan.png

# SVG (vectoriel)
dot -Tsvg scan.dot -o scan. svg

# PDF
dot -Tpdf scan.dot -o scan.pdf
```

Visualisation interactive :
```bash
xdot scan.dot
```

### Structure du fichier .dot

```dot
digraph G {
  rankdir=LR;
  node [style=filled, fontname="Helvetica"];
  
  "123456789" [label="google.com", fillcolor="lightblue", shape=box];
  "987654321" [label="142.250.185.46", fillcolor="gold", shape=box];
  
  "123456789" -> "987654321" [label="A"];
}
```

### Code couleur des noeuds

| Type | Couleur |
|------|---------|
| DOMAIN | Bleu clair (lightblue) |
| IP_V4 | Jaune (gold) |
| IP_V6 | Orange |
| TLD | Gris clair |
| SERVICE | Rose (pink) |

---

## Tests

### Lancer les tests

```bash
# Tous les tests
pytest

# Avec couverture
pytest --cov=src

# Tests verbeux
pytest -v

# Un fichier specifique
pytest tests/test_strategies.py
```

### Structure des tests

- `test_engine.py` : Tests du moteur de scan
- `test_strategies.py` : Tests des strategies individuelles

Les tests utilisent des mocks pour simuler les reponses DNS sans effectuer de vraies requetes reseau.

### Exemple de test

```python
def test_txt_strategy():
    strategy = TxtStrategy()
    node = Node("example.com", NodeType.DOMAIN)
    
    with patch("dns. resolver. Resolver.resolve") as mock_resolve:
        mock_answer = MagicMock()
        mock_answer.__str__. return_value = '"v=spf1 include:_spf.google.com ~all"'
        mock_resolve.return_value = [mock_answer]
        
        results = list(strategy.execute(node))
        
        values = [n.value for n, e in results]
        assert "_spf.google.com" in values
```

---

## Limitations connues

### Techniques

- **Timeout DNS** : Certains serveurs DNS lents peuvent causer des delais.  Le timeout est fixe a 1-2 secondes par requete.
- **Rate limiting** : Des scans intensifs peuvent declencher des limites de taux sur certains serveurs DNS.
- **DNSSEC** : La validation DNSSEC n'est pas implementee. 

### Fonctionnelles

- **Pas de brute-force de sous-domaines** : La strategie existe dans le README original mais n'est pas implementee dans le code actuel.
- **Pas de scan SRV automatique** : Les enregistrements SRV ne sont pas scannes par defaut.
- **Pas de scan de voisins IP** : La fonctionnalite de scan des IPs adjacentes n'est pas implementee. 

### Performances

- Le scan est synchrone et mono-thread
- Les grands domaines avec beaucoup de sous-domaines peuvent prendre du temps
- La profondeur recommandee est 3-5 pour eviter une explosion combinatoire

---

## Contribuer

### Signaler un bug

Ouvrir une issue sur GitHub avec : 
- Description du probleme
- Etapes pour reproduire
- Sortie du terminal
- Version de Python et du systeme d'exploitation

### Proposer une amelioration

1. Forker le depot
2. Creer une branche (`git checkout -b feature/ma-fonctionnalite`)
3. Commiter les modifications (`git commit -am 'Ajout de ma fonctionnalite'`)
4. Pousser la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrir une Pull Request

### Convention de code

- Style PEP 8
- Docstrings pour les fonctions publiques
- Tests pour les nouvelles fonctionnalites

---

## Licence

Ce projet est distribue sous licence MIT. Voir le fichier `LICENSE` pour plus de details.

---

## Auteur

Projet developpe dans le cadre d'un projet academique.

---

## Remerciements

- [dnspython](https://www.dnspython.org/) - Bibliotheque DNS pour Python
- [Rich](https://rich.readthedocs.io/) - Bibliotheque d'affichage terminal
- [tldextract](https://github.com/john-googgev/tldextract) - Extraction des composants de domaine
- [NetworkX](https://networkx.org/) - Manipulation de graphes
- [Graphviz](https://graphviz.org/) - Visualisation de graphes