import json
import os
import time

REPORT_DIR = os.path.join(os.getcwd(), "reports")

def ensure_report_dir():
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)

def save_report(data):
    """Saves the scan data to a JSON file and returns the filename."""
    ensure_report_dir()
    
    # Create valid filename
    target_clean = data.get("target", "scan").replace("http://", "").replace("https://", "").replace("/", "_").replace(":", "_")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"scan_{target_clean}_{timestamp}.json"
    filepath = os.path.join(REPORT_DIR, filename)
    
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        return filename
    except Exception as e:
        print(f"Error saving report: {e}")
        return None

def save_html_report(html_content, target):
    """Saves rendered HTML to a file."""
    ensure_report_dir()
    
    target_clean = target.replace("http://", "").replace("https://", "").replace("/", "_").replace(":", "_")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"report_{target_clean}_{timestamp}.html"
    filepath = os.path.join(REPORT_DIR, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return filename
    except Exception as e:
        print(f"Error saving HTML report: {e}")
        return None

def get_report_path(filename):
    """Returns absolute path to a report file."""
    # Security check to prevent directory traversal
    filename = os.path.basename(filename)
    return os.path.join(REPORT_DIR, filename)

def list_reports():
    """Returns a list of saved report dictionaries (filename, date, target)."""
    ensure_report_dir()
    reports = []
    try:
        # Get HTML report files
        files = [f for f in os.listdir(REPORT_DIR) if f.endswith('.html')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(REPORT_DIR, x)), reverse=True)
        
        for f in files:
            # Parse filename format: report_TARGET_TIMESTAMP.html
            parts = f.replace("report_", "").replace(".html", "").split("_")
            target_display = parts[0] if len(parts) > 0 else "Unknown"
            
            reports.append({
                "filename": f,
                "target": target_display,
                "timestamp": time.ctime(os.path.getmtime(os.path.join(REPORT_DIR, f)))
            })
    except Exception as e:
        print(f"Error listing reports: {e}")
    return reports
