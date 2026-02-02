from flask import Flask, render_template_string, jsonify, request
import os
import asyncio
from deriv_api import DerivAPI  # NEW: real Deriv library
import threading  # To run async in Flask

app = Flask(__name__)

# Global vars (simple for MVP – later use session or redis)
api = None
authorized = False
app_id = 120541  # ← REPLACE with your real app_id (e.g. 1089 or whatever)
api_token = None  # Set on connect

# Run async functions in sync Flask
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@app.route("/healthz")
def health():
    return "ok", 200

# Your HTML stays the SAME – no change needed there

# ... (paste your full HTML string here, unchanged)

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/connect', methods=['POST'])
def connect():
    global api, authorized, api_token
    data = request.json
    token = data.get('token', '')

    if not token:
        return jsonify({'success': False, 'error': 'No token provided'})

    api_token = token

    try:
        # Initialize and authorize
        api = DerivAPI(endpoint=f'wss://ws.derivws.com/websockets/v3?app_id={app_id}')
        auth_response = run_async(api.authorize({'authorize': api_token}))
        if 'error' in auth_response:
            return jsonify({'success': False, 'error': auth_response['error']['message']})

        authorized = True
        # Optional: fetch balance once
        balance_resp = run_async(api.balance({'balance': 1, 'subscribe': 1}))
        balance = balance_resp.get('balance', {}).get('balance', 'N/A')

        return jsonify({'success': True, 'message': 'Connected & Authorized', 'balance': balance})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analyze')
def analyze():
    if not authorized or api is None:
        return jsonify({'signal': 'WAIT', 'confidence': 0, 'reason': 'Not connected to Deriv'})

    # TODO Phase 2: real tick analysis (we'll add later)
    # For now keep simple random as placeholder, but log it's fake
    even_percent = random.randint(40, 60)
    if even_percent > 55:
        signal = 'EVEN'
        confidence = min(85, even_percent - 40)
        reason = f'Even bias detected ({even_percent}%) - SIMULATED for now'
    elif even_percent < 45:
        signal = 'ODD'
        confidence = min(85, 55 - even_percent)
        reason = f'Odd bias detected ({100-even_percent}%) - SIMULATED'
    else:
        signal = 'WAIT'
        confidence = 0
        reason = 'Market balanced - SIMULATED'

    return jsonify({
        'signal': signal,
        'confidence': confidence,
        'reason': reason,
        'even_percent': even_percent
    })

@app.route('/api/trade', methods=['POST'])
def trade():
    if not authorized or api is None:
        return jsonify({'success': False, 'error': 'Not connected'})

    data = request.json
    signal = data.get('signal')
    amount = data.get('amount', 10)

    if signal not in ['EVEN', 'ODD']:
        return jsonify({'success': False, 'error': 'Invalid signal'})

    try:
        contract_type = 'DIGITEVEN' if signal == 'EVEN' else 'DIGITODD'
        symbol = 'R_100'  # Volatility 100 Index – good for digits (change if needed)

        # Proposal first
        proposal_req = {
            'proposal': 1,
            'amount': amount,
            'basis': 'stake',
            'contract_type': contract_type,
            'currency': 'USD',
            'duration': 5,          # 5 ticks
            'duration_unit': 't',   # ticks
            'symbol': symbol
        }
        proposal_resp = run_async(api.proposal(proposal_req))

        if 'error' in proposal_resp:
            return jsonify({'success': False, 'error': proposal_resp['error']['message']})

        proposal_id = proposal_resp['proposal']['id']

        # Buy
        buy_resp = run_async(api.buy({'buy': proposal_id, 'price': proposal_resp['proposal']['ask_price']}))

        if 'error' in buy_resp:
            return jsonify({'success': False, 'error': buy_resp['error']['message']})

        # For MVP: assume instant result or log contract_id
        # Real: you'd subscribe to proposal_open_contract to see win/loss later
        return jsonify({
            'success': True,
            'result': f'Bought {signal} contract - ID: {buy_resp["buy"]["contract_id"]}',
            'balance': 'Check Deriv app for update'  # TODO: fetch real balance
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
