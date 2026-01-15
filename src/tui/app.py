import TermTk as ttk
from src.scanner.manager import ScannerManager
import threading

class DNSCheckerApp:
    def __init__(self):
        self.root = ttk.TTk()
        self.layout = ttk.TTkVBoxLayout()
        self.root.setLayout(self.layout)
        
        # Main Window configuration
        # We use a TTkWindow to hold our application content
        self.window = ttk.TTkWindow(parent=self.root, pos=(1,1), size=(100, 30), title="DNS Checker", border=True)
        self.window.setLayout(ttk.TTkVBoxLayout())
        
        # Input Area: Layout for domain input and scan button
        input_container = ttk.TTkContainer(layout=ttk.TTkHBoxLayout(), maxHeight=3)
        self.window.layout().addWidget(input_container)
        
        input_label = ttk.TTkLabel(text="Domain:", maxWidth=10)
        input_container.layout().addWidget(input_label)
        
        self.domain_input = ttk.TTkLineEdit()
        input_container.layout().addWidget(self.domain_input)
        
        self.scan_btn = ttk.TTkButton(text="Scan", maxWidth=10, border=True)
        input_container.layout().addWidget(self.scan_btn)
        self.scan_btn.clicked.connect(self.start_scan)
        
        # Results Area (Tabs)
        self.tab_widget = ttk.TTkTabWidget()
        self.window.layout().addWidget(self.tab_widget)
        
        self.dns_text = ttk.TTkTextEdit(readOnly=True)
        self.tab_widget.addTab(self.dns_text, "DNS Records")
        
        self.whois_text = ttk.TTkTextEdit(readOnly=True)
        self.tab_widget.addTab(self.whois_text, "WHOIS")
        
        self.log_text = ttk.TTkTextEdit(readOnly=True)
        self.tab_widget.addTab(self.log_text, "Logs")

    def log(self, message):
        self.log_text.append(message)

    def start_scan(self):
        """
        Initiates the scanning process.
        Validates input and starts a background thread to prevent UI freezing.
        """
        domain = self.domain_input.text()
        if not domain:
            self.log("Error: Please enter a domain.")
            return
            
        self.log(f"Starting scan for {domain}...")
        self.scan_btn.setEnabled(False) # Disable button to prevent double-click
        self.clear_results()
        
        # Run scan in a separate thread to prevent freezing TUI
        threading.Thread(target=self.perform_scan, args=(domain,)).start()

    def clear_results(self):
        self.dns_text.setText("")
        self.whois_text.setText("")

    def perform_scan(self, domain):
        try:
            manager = ScannerManager(domain)
            results = manager.scan_all()
            
            # Update UI (pyTermTk is not strictly thread-safe in all aspects, but simple text updates usually work. 
            # ideally, use signals/slots if available or a queue. For now, direct update.)
            # Formatting DNS results
            dns_output = ""
            if "dns" in results:
                for record_type, records in results["dns"].items():
                    dns_output += f"--- {record_type} ---\n"
                    if records:
                        for r in records:
                            dns_output += f"{r}\n"
                    else:
                        dns_output += "No records found.\n"
                    dns_output += "\n"
            self.dns_text.setText(dns_output)
            
            # Formatting WHOIS results
            whois_output = str(results.get("whois", "No WHOIS data"))
            self.whois_text.setText(whois_output)
            
            self.log("Scan completed successfully.")
            
        except Exception as e:
            self.log(f"Error during scan: {str(e)}")
        finally:
            self.scan_btn.setEnabled(True)

def run():
    app = DNSCheckerApp()
    app.root.mainloop()
