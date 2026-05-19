from flask import Flask, jsonify, render_template_string, request
import random
import os
from datetime import datetime

app = Flask(__name__)

request_count = 0
failure_count = 0

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Pipeline Monitor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f0f0f0;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 24px;
            margin-bottom: 5px;
            color: #333;
        }
        .subtitle {
            color: #666;
            font-size: 14px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ddd;
        }
        .alert {
            padding: 15px;
            margin: 20px 0;
            border-radius: 3px;
            font-size: 14px;
        }
        .alert-success {
            background: #d4edda;
            border-left: 3px solid #28a745;
            color: #155724;
        }
        .alert-danger {
            background: #f8d7da;
            border-left: 3px solid #dc3545;
            color: #721c24;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .stat-box {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 15px;
            flex: 1;
            text-align: center;
            border-radius: 3px;
        }
        .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #333;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 10px;
        }
        button:hover {
            background: #0056b3;
        }
        .button-red {
            background: #dc3545;
        }
        .button-red:hover {
            background: #c82333;
        }
        .footer {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
        }
        .feature-list {
            margin: 20px 0;
            padding: 0;
            list-style: none;
        }
        .feature-list li {
            display: inline-block;
            background: #e9ecef;
            padding: 4px 10px;
            border-radius: 3px;
            font-size: 12px;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        .small-text {
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Pipeline Monitor</h1>
        <div class="subtitle">CI/CD with automatic recovery</div>
        
        <div class="alert alert-{{ 'danger' if is_failure else 'success' }}">
            <strong>{{ 'Failure detected' if is_failure else 'System operational' }}</strong><br>
            {{ message }}
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{{ total_requests }}</div>
                <div class="stat-label">Total checks</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ failures }}</div>
                <div class="stat-label">Recovered failures</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ success_rate }}%</div>
                <div class="stat-label">Success rate</div>
            </div>
        </div>
        
        <div>
            <h3 style="font-size: 16px; margin: 15px 0 10px 0;">Features</h3>
            <ul class="feature-list">
                <li>Auto retry (3 attempts)</li>
                <li>Health checks</li>
                <li>Docker support</li>
                <li>Jenkins pipeline</li>
            </ul>
        </div>
        
        <div style="margin: 20px 0;">
            <button onclick="location.reload()">Refresh</button>
            <button class="button-red" onclick="forceFailure()">Trigger failure</button>
            <button onclick="checkHealth()">Health check</button>
        </div>
        
        <div class="footer">
            <div>Random failure rate: 20%</div>
            <div class="small-text">Last update: {{ timestamp }}</div>
        </div>
    </div>
    
    <script>
        function forceFailure() {
            fetch('/fail')
                .then(function(response) { 
                    alert('Failure triggered'); 
                    location.reload();
                })
                .catch(function() {
                    alert('Failure triggered');
                    location.reload();
                });
        }
        
        function checkHealth() {
            fetch('/health')
                .then(function(response) { return response.json(); })
                .then(function(data) { 
                    alert('Status: ' + data.status); 
                })
                .catch(function() {
                    alert('Health check endpoint responding');
                });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def hello():
    global request_count, failure_count
    request_count += 1
    
    is_failure = random.random() < 0.2
    
    if is_failure:
        failure_count += 1
        message = "Random failure occurred. Jenkins will retry the deployment."
        status_code = 500
    else:
        message = "Pipeline running normally. All checks passed."
        status_code = 200
    
    if request_count > 0:
        success_rate = round(((request_count - failure_count) / request_count) * 100, 1)
    else:
        success_rate = 100
    
    return render_template_string(
        HTML_TEMPLATE,
        message=message,
        is_failure=is_failure,
        total_requests=request_count,
        failures=failure_count,
        success_rate=success_rate,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ), status_code

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "requests": request_count,
        "failures": failure_count
    }), 200
    
    
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("GitHub Webhook Received:")
    print(data)

    return jsonify({
        "status": "success",
        "message": "Webhook received"
    }), 200

@app.route('/fail')
def force_fail():
    global failure_count
    failure_count += 1
    return jsonify({
        "status": "failure",
        "message": "Manual failure triggered"
    }), 500

@app.route('/stats')
def stats():
    if request_count > 0:
        success_rate = round(((request_count - failure_count) / request_count) * 100, 2)
    else:
        success_rate = 100
    
    return jsonify({
        "total_requests": request_count,
        "failures": failure_count,
        "success_rate": success_rate
    }), 200

@app.route('/reset')
def reset():
    global request_count, failure_count
    request_count = 0
    failure_count = 0
    return jsonify({"message": "Stats reset"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("Starting pipeline monitor on http://localhost:" + str(port))
    print("Health check: http://localhost:" + str(port) + "/health")
    print("Stats: http://localhost:" + str(port) + "/stats")
    app.run(host='0.0.0.0', port=port, debug=False)