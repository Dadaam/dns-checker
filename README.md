# DNS Checker

A terminal-based DNS scanner and information retrieval tool built with Python and pyTermTk.

## Features

- **DNS Records**: Retrieve A, AAAA, MX, NS, TXT, SOA, CNAME records.
- **WHOIS Lookup**: Fetch domain registration details.
- **TUI**: User-friendly Terminal User Interface.
- **Modular Architecture**: Clean and extensible code structure.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd dns-checker
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```bash
python main.py
```

## Testing

Run the tests using pytest:
```bash
pytest
```
