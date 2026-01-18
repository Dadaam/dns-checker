import argparse
from src.tui.rich_app import RichDNSApp

def main():
    parser = argparse.ArgumentParser(description="DNS Scanner")
    parser.add_argument("domain", nargs="?", help="Choisit la cible du domaine à scanner")
    parser.add_argument("-d", "--depth", type=int, default=3, help="Profondeur de la récursion (par défaut : 3)")
    
    args = parser.parse_args()
    
    app = RichDNSApp()
    app.run(domain=args.domain, depth=args.depth)

if __name__ == "__main__":
    main()
