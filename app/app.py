from flask import Flask, jsonify, render_template_string, request
import random
import os
from datetime import datetime
import time

app = Flask(__name__)

request_count = 0
failure_count = 0
healing_history = []
healed_successfully = 0
current_failure = None  # Track if we're currently in a failure state
last_failure_time = None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Pipeline Monitor - Healing Visualization</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f0f0f0;
        }
        .container {
            max-width: 1000px;
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
        .alert-warning {
            background: #fff3cd;
            border-left: 3px solid #ffc107;
            color: #856404;
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
        
        .healing-section {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 3px;
        }
        .healing-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }
        .retry-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 15px 0;
            gap: 10px;
        }
        .retry-step {
            flex: 1;
            text-align: center;
            padding: 10px;
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 3px;
            position: relative;
        }
        .retry-step.active {
            background: #007bff;
            color: white;
            border-color: #007bff;
        }
        .retry-step.completed {
            background: #28a745;
            color: white;
            border-color: #28a745;
        }
        .retry-step.failed {
            background: #dc3545;
            color: white;
            border-color: #dc3545;
        }
        .retry-number {
            font-size: 18px;
            font-weight: bold;
        }
        .retry-label {
            font-size: 10px;
            margin-top: 5px;
        }
        .arrow {
            font-size: 20px;
            color: #666;
        }
        
        .timeline {
            margin: 20px 0;
            max-height: 300px;
            overflow-y: auto;
        }
        .timeline-item {
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-left: 3px solid #007bff;
            font-size: 12px;
        }
        .timeline-time {
            color: #666;
            font-size: 10px;
        }
        .timeline-message {
            margin-top: 3px;
        }
        .healing-badge {
            background: #28a745;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            margin-left: 10px;
        }
        
        .progress-container {
            margin: 15px 0;
        }
        .progress-bar {
            height: 20px;
            background: #e9ecef;
            border-radius: 3px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: #28a745;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 11px;
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
            margin-bottom: 10px;
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
        .button-green {
            background: #28a745;
        }
        .button-green:hover {
            background: #218838;
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
        .retry-info {
            background: #e7f3ff;
            padding: 10px;
            margin: 10px 0;
            border-radius: 3px;
            font-size: 13px;
        }
        .note {
            background: #fff3cd;
            padding: 8px;
            margin: 10px 0;
            border-radius: 3px;
            font-size: 12px;
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Pipeline Monitor</h1>
        <div class="subtitle">CI/CD with healing visualization</div>
        
        <div class="note">
            <strong>Note:</strong> Healing happens automatically when failure occurs. Refresh the page to see healing progress.
        </div>
        
        <div class="alert alert-{{ 'danger' if is_failure and not healing_active else 'warning' if healing_active else 'success' }}">
            <strong>
                {% if healing_active %}
                    Healing in progress...
                {% elif is_failure %}
                    Failure detected
                {% else %}
                    System operational
                {% endif %}
            </strong><br>
            {{ message }}
        </div>
        
        {% if healing_active or healing_completed %}
        <div class="healing-section">
            <div class="healing-title">
                Healing Process 
                <span class="healing-badge">Auto-retry active</span>
            </div>
            
            <div class="retry-container">
                <div class="retry-step {% if retry_count >= 1 %}completed{% elif healing_active and retry_attempt == 1 %}active{% endif %}">
                    <div class="retry-number">1</div>
                    <div class="retry-label">Attempt 1</div>
                </div>
                <div class="arrow">→</div>
                <div class="retry-step {% if retry_count >= 2 %}completed{% elif healing_active and retry_attempt == 2 %}active{% endif %}">
                    <div class="retry-number">2</div>
                    <div class="retry-label">Attempt 2</div>
                </div>
                <div class="arrow">→</div>
                <div class="retry-step {% if retry_count >= 3 %}completed{% elif healing_active and retry_attempt == 3 %}active{% endif %}">
                    <div class="retry-number">3</div>
                    <div class="retry-label">Attempt 3</div>
                </div>
            </div>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ healing_progress }}%;">
                        {{ healing_progress }}%
                    </div>
                </div>
            </div>
            
            <div class="retry-info">
                <strong>Status:</strong> {{ retry_status }}<br>
                <strong>Action:</strong> {{ current_action }}<br>
                <strong>Time:</strong> {{ retry_timestamp }}
            </div>
        </div>
        {% endif %}
        
        {% if healing_history %}
        <div class="healing-section">
            <div class="healing-title">Recent Healing Events</div>
            <div class="timeline">
                {% for event in healing_history %}
                <div class="timeline-item">
                    <div class="timeline-time">{{ event.time }}</div>
                    <div class="timeline-message">
                        <strong>{{ event.type }}:</strong> {{ event.message }}
                        {% if event.retry_count %}
                            (Attempt {{ event.retry_count }}/3)
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{{ total_requests }}</div>
                <div class="stat-label">Total checks</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ failures }}</div>
                <div class="stat-label">Failures</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ healed_count }}</div>
                <div class="stat-label">Healed</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ success_rate }}%</div>
                <div class="stat-label">Success rate</div>
            </div>
        </div>
        
        <div style="margin: 20px 0;">
            <button onclick="location.reload()">Refresh Status</button>
            <button class="button-red" onclick="forceFailure()">Trigger New Failure</button>
            <button onclick="checkHealth()">Health Check</button>
            <button class="button-green" onclick="clearHistory()">Clear History</button>
        </div>
        
        <div class="footer">
            <div>Healing rate: {{ healing_rate }}% of failures recovered</div>
            <div class="small-text">Last update: {{ timestamp }}</div>
        </div>
    </div>
    
    <script>
        function forceFailure() {
            if(confirm('Trigger a new failure? This will start the healing process.')) {
                fetch('/fail')
                    .then(function(response) { return response.json(); })
                    .then(function(data) { 
                        alert(data.message); 
                        location.reload();
                    });
            }
        }
        
        function checkHealth() {
            fetch('/health')
                .then(function(response) { return response.json(); })
                .then(function(data) { 
                    alert('Status: ' + data.status + '\\nFailures: ' + data.failures + '\\nHealed: ' + data.healed_count); 
                });
        }
        
        function clearHistory() {
            if(confirm('Clear healing history?')) {
                fetch('/clear_history')
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        alert('History cleared');
                        location.reload();
                    });
            }
        }
    </script>
</body>
</html>
'''

def start_healing_process():
    """Start a new healing process"""
    global healing_history, healed_successfully, current_failure, last_failure_time
    
    healing_data = {
        'in_progress': True,
        'retry_attempt': 1,
        'retry_count': 0,
        'start_time': datetime.now(),
        'status': 'Healing started',
        'completed': False
    }
    
    # Simulate retry attempts with delays
    for attempt in range(1, 4):
        healing_data['retry_attempt'] = attempt
        healing_data['status'] = f'Retry attempt {attempt}/3'
        
        healing_history.insert(0, {
            'time': datetime.now().strftime("%H:%M:%S"),
            'type': 'RETRY',
            'message': f'Attempt {attempt} to recover',
            'retry_count': attempt
        })
        
        # Simulate delay (just for demo purposes)
        # In real app, this would be actual retry logic
        
        # 80% chance of success on retry, last attempt always succeeds
        if attempt == 3 or random.random() < 0.8:
            healing_data['status'] = f'Successfully healed on attempt {attempt}'
            healing_data['retry_count'] = attempt
            healing_data['in_progress'] = False
            healing_data['completed'] = True
            healed_successfully += 1
            
            healing_history.insert(0, {
                'time': datetime.now().strftime("%H:%M:%S"),
                'type': 'HEALED',
                'message': f'System recovered after {attempt} retries',
                'retry_count': attempt
            })
            break
        else:
            healing_history.insert(0, {
                'time': datetime.now().strftime("%H:%M:%S"),
                'type': 'RETRY_FAILED',
                'message': f'Attempt {attempt} failed, retrying...',
                'retry_count': attempt
            })
    
    # Keep only last 10 events
    healing_history = healing_history[:10]
    
    # Mark that we have a failure that's being processed
    current_failure = healing_data
    last_failure_time = datetime.now()
    
    return healing_data

@app.route('/')
def hello():
    global request_count, failure_count, current_failure, last_failure_time
    
    request_count += 1
    
    healing_active = False
    healing_completed = False
    healing_progress = 0
    retry_attempt = 0
    retry_count = 0
    retry_status = ''
    current_action = ''
    retry_timestamp = ''
    is_failure = False
    message = "Pipeline running normally"
    status_code = 200
    
    # Check if we have an active healing process
    if current_failure:
        healing_data = current_failure
        
        if healing_data.get('in_progress', False):
            # Healing is still in progress
            healing_active = True
            is_failure = True
            healing_progress = (healing_data.get('retry_attempt', 0) / 3) * 100
            retry_attempt = healing_data.get('retry_attempt', 0)
            retry_count = healing_data.get('retry_count', 0)
            retry_status = healing_data.get('status', 'Healing in progress')
            current_action = f'Retry {retry_attempt}/3'
            retry_timestamp = healing_data.get('start_time', datetime.now()).strftime("%H:%M:%S")
            message = f"Failure detected - healing in progress (attempt {retry_attempt}/3)"
            status_code = 500
        elif healing_data.get('completed', False):
            # Healing completed successfully
            healing_completed = True
            healing_progress = 100
            retry_count = healing_data.get('retry_count', 0)
            retry_status = healing_data.get('status', 'Healing complete')
            current_action = 'System recovered'
            retry_timestamp = healing_data.get('start_time', datetime.now()).strftime("%H:%M:%S")
            message = f"System healed after {retry_count} retries"
            status_code = 200
            
            # Clear the current failure after showing completion once
            # We'll keep it for this request to display, but mark to clear
            if 'displayed' not in healing_data:
                healing_data['displayed'] = True
            else:
                current_failure = None
    else:
        # No active healing, normal operation with random failure chance
        # Only trigger new failure if no healing is in progress
        if random.random() < 0.2:  # 20% chance of failure
            current_failure = start_healing_process()
            healing_active = True
            is_failure = True
            failure_count += 1
            
            healing_data = current_failure
            healing_progress = (healing_data.get('retry_attempt', 0) / 3) * 100
            retry_attempt = healing_data.get('retry_attempt', 0)
            retry_count = healing_data.get('retry_count', 0)
            retry_status = healing_data.get('status', 'Healing in progress')
            current_action = f'Retry {retry_attempt}/3'
            retry_timestamp = healing_data.get('start_time', datetime.now()).strftime("%H:%M:%S")
            message = f"Failure detected - starting healing (attempt {retry_attempt}/3)"
            status_code = 500
        else:
            message = "Pipeline running normally"
            status_code = 200
    
    # Calculate statistics
    if request_count > 0:
        success_rate = round(((request_count - failure_count) / request_count) * 100, 1)
    else:
        success_rate = 100
    
    if failure_count > 0:
        healing_rate = round((healed_successfully / failure_count) * 100, 1)
    else:
        healing_rate = 100
    
    return render_template_string(
        HTML_TEMPLATE,
        message=message,
        is_failure=is_failure,
        healing_active=healing_active,
        healing_completed=healing_completed,
        healing_progress=healing_progress,
        retry_attempt=retry_attempt,
        retry_count=retry_count,
        retry_status=retry_status,
        current_action=current_action,
        retry_timestamp=retry_timestamp,
        healing_history=healing_history[:5],
        total_requests=request_count,
        failures=failure_count,
        healed_count=healed_successfully,
        success_rate=success_rate,
        healing_rate=healing_rate,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ), status_code

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "requests": request_count,
        "failures": failure_count,
        "healed_count": healed_successfully,
        "healing_active": current_failure is not None
    }), 200

@app.route('/fail')
def force_fail():
    global failure_count, current_failure
    failure_count += 1
    current_failure = start_healing_process()
    return jsonify({
        "status": "failure",
        "message": "Manual failure triggered - healing started",
        "healing_started": True
    }), 200

@app.route('/stats')
def stats():
    if request_count > 0:
        success_rate = round(((request_count - failure_count) / request_count) * 100, 2)
    else:
        success_rate = 100
    
    return jsonify({
        "total_requests": request_count,
        "failures": failure_count,
        "healed_count": healed_successfully,
        "success_rate": success_rate,
        "healing_events": len(healing_history)
    }), 200

@app.route('/clear_history')
def clear_history():
    global healing_history
    healing_history = []
    return jsonify({"message": "Healing history cleared"}), 200

@app.route('/reset')
def reset():
    global request_count, failure_count, healing_history, healed_successfully, current_failure
    request_count = 0
    failure_count = 0
    healing_history = []
    healed_successfully = 0
    current_failure = None
    return jsonify({"message": "All stats reset"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*50)
    print("Pipeline Monitor with Healing Visualization")
    print("="*50)
    print(f"Running on: http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Statistics: http://localhost:{port}/stats")
    print("\nHow it works:")
    print("- 20% random chance of failure on each page load")
    print("- When failure occurs, healing process starts automatically")
    print("- System attempts up to 3 retries")
    print("- Refresh page to see healing progress")
    print("- Click 'Trigger New Failure' to manually start healing")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)