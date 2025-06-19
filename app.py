#!/usr/bin/env python3
"""
Simple application to fetch and display the current exchange rate of Nigerian Naira to US Dollar
"""
import requests
from datetime import datetime
from flask import Flask, render_template_string

app = Flask(__name__)

def get_exchange_rate():
    """Fetch the current NGN to USD exchange rate using a free API"""
    try:
        # Using ExchangeRate-API's free endpoint
        response = requests.get('https://open.er-api.com/v6/latest/USD')
        data = response.json()
        
        if response.status_code == 200 and data['result'] == 'success':
            # Get the NGN rate (USD to NGN)
            ngn_rate = data['rates'].get('NGN')
            
            if ngn_rate:
                # Calculate NGN to USD (inverse of USD to NGN)
                usd_rate = 1 / ngn_rate
                return {
                    'ngn_to_usd': usd_rate,
                    'usd_to_ngn': ngn_rate,
                    'last_updated': data['time_last_update_utc'],
                    'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                return {'error': 'NGN rate not found in the response'}
        else:
            return {'error': f"API Error: {data.get('error-type', 'Unknown error')}"}
    
    except requests.RequestException as e:
        return {'error': f"Request failed: {str(e)}"}
    except Exception as e:
        return {'error': f"An unexpected error occurred: {str(e)}"}

# HTML template for the web page
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>NGN to USD Exchange Rate</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
        .container { background-color: #f5f5f5; border-radius: 5px; padding: 20px; }
        .rate { font-size: 24px; font-weight: bold; color: #2c3e50; margin: 10px 0; }
        .info { color: #7f8c8d; font-size: 14px; }
        .error { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Current Exchange Rates</h1>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% else %}
            <p class="rate">1 NGN = {{ "%.6f"|format(ngn_to_usd) }} USD</p>
            <p class="rate">1 USD = {{ "%.2f"|format(usd_to_ngn) }} NGN</p>
            <p class="info">Last Updated: {{ last_updated }}</p>
            <p class="info">Current Time: {{ current_time }}</p>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Display exchange rate in web browser"""
    result = get_exchange_rate()
    
    if 'error' in result:
        return render_template_string(HTML_TEMPLATE, error=result['error'])
    else:
        return render_template_string(HTML_TEMPLATE, 
                                     ngn_to_usd=result['ngn_to_usd'],
                                     usd_to_ngn=result['usd_to_ngn'],
                                     last_updated=result['last_updated'],
                                     current_time=result['current_time'])

def main():
    """Command line display of exchange rate"""
    print("Fetching current NGN to USD exchange rate...\n")
    
    result = get_exchange_rate()
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Current Exchange Rates:")
        print(f"1 NGN = {result['ngn_to_usd']:.6f} USD")
        print(f"1 USD = {result['usd_to_ngn']:.2f} NGN")
        print(f"\nLast Updated: {result['last_updated']}")
        print(f"Current Time: {result['current_time']}")

if __name__ == "__main__":
    # Run the Flask web server when executed as a script
    print("Starting web server. Access the exchange rate at http://127.0.0.1:5000/")
    app.run(host='0.0.0.0', port=5000, debug=True)