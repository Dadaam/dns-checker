# Pure DNS Scanner

A recursive, modular DNS scanner that relies **exclusively** on DNS queries (no WHOIS, no HTTP scraping). Visualizes results in a hierarchical TUI.

## Features

- **Pure DNS**: Uses only standard DNS queries (A, AAAA, MX, NS, PTR, SRV, TXT).
- **Recursive Scanning**: Finds a new domain/IP -> Scans it immediately.
- **Strategies**:
  - **Basic**: Standard records.
  - **TXT Parsing**: Extracts IPs/Domains from SPF/DMARC.
  - **SRV Brute-force**: Finds services like `_xmpp`, `_sip`.
  - **Reverse DNS**: PTR lookups for IPs.
  - **Parent Deduction**: Crawls up to the registered domain.
  - **Neighbors**: Scans adjacent IPs (+1/-1).
  - **Subdomains**: Brute-forces common prefixes.
- **TUI**: Real-time terminal dashboard with Tree View and Stats.
- **Graphviz Export**: Exports the discovery graph to `.dot` format.

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the scanner:
```bash
python main.py
```

- Enter a **Domain**.
- Set **Depth** (recursion limit).
- Click **START SCAN**.
- Use **Export .dot** to save the graph.
