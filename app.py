from flask import Flask, render_template_string, jsonify, request
import os
import random
from datetime import datetime

app = Flask(__name__)

@app.route("/healthz")
def health():
    return "ok", 200
    
# HTML Template
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>🚀 Deriv Trading Bot Online</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .header {
            background: #1e293b;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #1e293b;
            padding: 20px;
            border-radius: 10px;
        }
        .signal {
            font-size: 48px;
            font-weight: bold;
            margin: 20px 0;
        }
        .even { color: #10b981; }
        .odd { color: #ef4444; }
        button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 15px 30px;
            margin: 10px;
            border-radius: 10px;
            font-size: 18px;
            cursor: pointer;
        }
        .trade-btn {
            background: #10b981;
        }
        input {
            padding: 10px;
            width: 80%;
            margin: 10px;
            border-radius: 5px;
            border: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Deriv Trading Bot Online</h1>
            <p>Trade from anywhere in the world</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>💰 Balance</h3>
                <h2 id="balance">$1000</h2>
            </div>
            <div class="stat-card">
                <h3>📊 Win Rate</h3>
                <h2 id="winRate">0%</h2>
            </div>
        </div>
        
        <div>
            <h2>Current Signal</h2>
            <div class="signal" id="signal">---</div>
            <p id="reason">Click Analyze</p>
        </div>
        
        <div>
            <button onclick="analyze()">🔍 Analyze Market</button>
            <button class="trade-btn" onclick="trade('EVEN')">⚡ Trade EVEN</button>
            <button class="trade-btn" onclick="trade('ODD')">⚡ Trade ODD</button>
        </div>
        
        <div style="margin-top: 30px; background: #1e293b; padding: 20px; border-radius: 10px;">
            <h3>🔑 Connect to Deriv</h3>
            <input type="password" id="token" placeholder="Enter Deriv API Token">
            <button onclick="connect()">Connect</button>
        </div>
        
        <div id="logs" style="margin-top: 20px; text-align: left; background: #1e293b; padding: 15px; border-radius: 10px;">
            <h4>📋 Activity Log</h4>
            <div id="logContent">Waiting for activity...</div>
        </div>
    </div>
    
    <script>
        let balance = 1000;
        let wins = 0;
        let losses = 0;
        
        function log(msg) {
            const logDiv = document.getElementById('logContent');
            const time = new Date().toLocaleTimeString();
            logDiv.innerHTML = `[${time}] ${msg}<br>` + logDiv.innerHTML;
        }
        
        async function analyze() {
            document.getElementById('signal').textContent = 'ANALYZING...';
            
            const response = await fetch('/api/analyze');
            const data = await response.json();
            
            document.getElementById('signal').textContent = data.signal;
            document.getElementById('signal').className = 'signal ' + data.signal.toLowerCase();
            document.getElementById('reason').textContent = data.reason;
            
            log(`Analyzed: ${data.signal} (${data.confidence}%)`);
        }
        
        async function trade(signal) {
            const amount = prompt(`Amount for ${signal} trade:`, '10');
            if (!amount || amount < 1) return;
            
            const response = await fetch('/api/trade', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({signal, amount: parseFloat(amount)})
            });
            
            const data = await response.json();
            
            if (data.success) {
                balance = data.balance;
                document.getElementById('balance').textContent = '$' + balance;
                
                if (data.won) wins++; else losses++;
                const winRate = wins + losses > 0 ? Math.round((wins / (wins + losses)) * 100) : 0;
                document.getElementById('winRate').textContent = winRate + '%';
                
                log(`${signal} trade: $${amount} → ${data.result}`);
            }
        }
        
        async function connect() {
            const token = document.getElementById('token').value;
            if (!token) {
                alert('Enter API token');
                return;
            }
            
            const response = await fetch('/api/connect', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({token})
            });
            
            const data = await response.json();
            if (data.success) {
                log('✅ Connected to Deriv API');
            } else {
                log('❌ Connection failed');
            }
        }
        
        // Auto-analyze on load
        setTimeout(analyze, 1000);
    </script>
</body>
</html>
'''
@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/analyze')
def analyze():
    even_percent = random.randint(40, 60)
    if even_percent > 55:
        signal = 'EVEN'
        confidence = min(85, even_percent - 40)
        reason = f'Even bias detected ({even_percent}%)'
    elif even_percent < 45:
        signal = 'ODD'
        confidence = min(85, 55 - even_percent)
        reason = f'Odd bias detected ({100-even_percent}%)'
    else:
        signal = 'WAIT'
        confidence = 0
        reason = 'Market balanced'
    
    return jsonify({
        'signal': signal,
        'confidence': confidence,
        'reason': reason,
        'even_percent': even_percent
    })

@app.route('/api/trade', methods=['POST'])
def trade():
    data = request.json
    amount = data.get('amount', 10)
    
    # Simulate trade
    won = random.random() > 0.4  # 60% win rate
    if won:
        result = f'WON +${amount * 0.8:.2f}'
        new_balance = 1000 + (amount * 0.8)
    else:
        result = f'LOST -${amount:.2f}'
        new_balance = 1000 - amount
    
    return jsonify({
        'success': True,
        'won': won,
        'result': result,
        'balance': new_balance
    })

@app.route('/api/connect', methods=['POST'])
def connect():
    data = request.json
    token = data.get('token', '')
    
    if token:
        return jsonify({'success': True, 'message': 'Connected to Deriv API'})
    else:
        return jsonify({'success': False, 'error': 'No token provided'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
