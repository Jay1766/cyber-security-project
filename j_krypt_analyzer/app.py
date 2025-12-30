from flask import Flask, render_template, request, jsonify, send_file
from scanner.core import perform_scan
from scanner.report_manager import save_report, save_html_report, get_report_path, list_reports
import time
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Renders the V12 Portal (Main Menu)."""
    return render_template('portal.html')

@app.route('/scanner')
def scanner_view():
    """Renders the Dedicated Scanner Module."""
    return render_template('scanner.html')

@app.route('/reports')
def reports_view():
    """Renders the Dedicated Reports Module."""
    reports = list_reports()
    return render_template('reports.html', reports=reports)

@app.route('/scan', methods=['POST'])
def scan():
    """Handles the scan request and returns results."""
    target = request.form.get('target')
    if not target:
         return render_template('scanner.html', error="Please enter a URL or IP Address.")
    
    # Simulate a small delay for the animation effect if scan is too fast
    start_time = time.time()
    results = perform_scan(target)
    elapsed = time.time() - start_time
    if elapsed < 2:
        time.sleep(2 - elapsed)
        
    if "error" in results:
        return render_template('scanner.html', error=results['error'])
    
    # Auto-Save JSON Report
    json_file = save_report(results)
    
    # Generate and Save Professional HTML Report
    html_content = render_template('report_template.html', results=results)
    report_file = save_html_report(html_content, target)
        
    return render_template('result.html', results=results, report_file=report_file)

@app.route('/view/<filename>')
def view_report(filename):
    """View a saved report in the browser."""
    try:
        path = get_report_path(filename)
        if os.path.exists(path):
            return send_file(path, as_attachment=False)
        else:
            return "File not found", 404
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
