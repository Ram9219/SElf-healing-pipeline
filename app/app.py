from flask import Flask, jsonify, render_template_string, request
import random
import os
from datetime import datetime
import time
import threading

app = Flask(__name__)

request_count = 0
failure_count = 0
healing_history = []
healed_successfully = 0
current_healing = None
healing_lock = threading.Lock()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Self-Healing Pipeline - Live Demo</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1e1e2e;
            color: #eee;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: #2d2d3d;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        h1 {
            font-size: 28px;
            margin-bottom: 5px;
            color: #fff;
        }
        .subtitle {
            color: #aaa;
            font-size: 14px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #444;
        }
        .status-card {
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            text-align: center;
        }
        .status-healthy {
            background: #1a472a;
            border: 1px solid #2ecc71;
            color: #2ecc71;
        }
        .status-failure {
            background: #4a1a1a;
            border: 1px solid #e74c3c;
            color: #e74c3c;
        }
        .status-healing {
            background: #4a3a1a;
            border: 1px solid #f39c12;
            color: #f39c12;
        }
        .status-recovered {
            background: #1a472a;
            border: 1px solid #2ecc71;
            color: #2ecc71;
        }
        .status-message {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .status-detail {
            font-size: 14px;
            color: #ccc;
        }
        
        .healing-visualization {
            background: #252535;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        .healing-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #f39c12;
        }
        
        .retry-steps {
            display: flex;
            justify-content: space-between;
            margin: 30px 0;
            position: relative;
        }
        .retry-step {
            flex: 1;
            text-align: center;
            position: relative;
            z-index: 2;
        }
        .step-circle {
            width: 50px;
            height: 50px;
            background: #3d3d4d;
            border-radius: 50%;
            margin: 0 auto 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 20px;
            transition: all 0.3s ease;
        }
        .step-circle.active {
            background: #f39c12;
            color: #1e1e2e;
            box-shadow: 0 0 20px #f39c12;
            animation: pulse 1s infinite;
        }
        .step-circle.completed {
            background: #2ecc71;
            color: #1e1e2e;
        }
        .step-circle.failed {
            background: #e74c3c;
            color: #1e1e2e;
        }
        .step-label {
            font-size: 12px;
            color: #aaa;
        }
        .step-time {
            font-size: 10px;
            color: #888;
            margin-top: 5px;
        }
        
        .connector {
            position: absolute;
            top: 25px;
            left: 0;
            right: 0;
            height: 2px;
            background: #3d3d4d;
            z-index: 1;
        }
        .connector-progress {
            position: absolute;
            top: 0;
            left: 0;
            height: 2px;
            background: #2ecc71;
            transition: width 0.5s ease;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .progress-bar-container {
            margin: 20px 0;
            background: #3d3d4d;
            border-radius: 10px;
            overflow: hidden;
        }
        .progress-bar {
            height: 30px;
            background: linear-gradient(90deg, #f39c12, #2ecc71);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }
        
        .timeline {
            margin: 20px 0;
            max-height: 400px;
            overflow-y: auto;
            background: #1e1e2e;
            border-radius: 8px;
            padding: 10px;
        }
        .timeline-item {
            padding: 10px;
            margin: 5px 0;
            background: #2d2d3d;
            border-left: 3px solid;
            border-radius: 5px;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        .timeline-time {
            font-size: 11px;
            color: #888;
            font-family: monospace;
        }
        .timeline-message {
            margin-top: 5px;
            font-size: 13px;
        }
        .timeline-type-RETRY { border-left-color: #f39c12; }
        .timeline-type-HEALED { border-left-color: #2ecc71; }
        .timeline-type-FAILURE { border-left-color: #e74c3c; }
        .timeline-type-RETRY_FAILED { border-left-color: #e74c3c; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #252535;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-number {
            font-size: 32px;
            font-weight: bold;
            color: #f39c12;
        }
        .stat-label {
            font-size: 12px;
            color: #aaa;
            margin-top: 5px;
        }
        
        button {
            background: #f39c12;
            color: #1e1e2e;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            margin: 5px;
            transition: all 0.2s;
        }
        button:hover {
            background: #e67e22;
            transform: translateY(-2px);
        }
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
        .btn-success {
            background: #2ecc71;
            color: white;
        }
        .btn-success:hover {
            background: #27ae60;
        }
        
        .workflow-steps {
            background: #1e1e2e;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 12px;
        }
        .workflow-step {
            padding: 8px;
            margin: 5px 0;
            font-family: monospace;
            border-left: 2px solid #f39c12;
        }
        
        .footer {
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #444;
            font-size: 12px;
            color: #888;
            text-align: center;
        }
        
        .auto-refresh-toggle {
            background: #3d3d4d;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            text-align: center;
        }
        
        .healing-stats {
            display: flex;
            justify-content: space-between;
            margin: 15px 0;
            padding: 10px;
            background: #1e1e2e;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 Self-Healing Pipeline</h1>
        <div class="subtitle">Real-time healing visualization | Auto-retry with 3 attempts</div>
        
        <div class="status-card status-{{ status_type }}">
            <div class="status-message">{{ status_message }}</div>
            <div class="status-detail">{{ status_detail }}</div>
        </div>
        
        {% if healing_active or show_healing %}
        <div class="healing-visualization">
            <div class="healing-title">
                🔧 Healing Process in Action
                <span class="healing-badge" style="background: #f39c12; padding: 2px 8px; border-radius: 3px; font-size: 10px; margin-left: 10px;">
                    ⚡ Active
                </span>
            </div>
            
            <!-- Retry Visualization -->
            <div class="retry-steps">
                <div class="connector"></div>
                <div class="connector-progress" style="width: {{ connector_progress }}%;"></div>
                
                <div class="retry-step">
                    <div class="step-circle {% if retry_attempt >= 1 %}completed{% elif healing_active and current_retry == 1 %}active{% endif %}">
                        {% if retry_attempt >= 1 %}✓{% else %}1{% endif %}
                    </div>
                    <div class="step-label">Attempt 1</div>
                    <div class="step-time">{{ attempt1_time }}</div>
                </div>
                <div class="retry-step">
                    <div class="step-circle {% if retry_attempt >= 2 %}completed{% elif healing_active and current_retry == 2 %}active{% endif %}">
                        {% if retry_attempt >= 2 %}✓{% else %}2{% endif %}
                    </div>
                    <div class="step-label">Attempt 2</div>
                    <div class="step-time">{{ attempt2_time }}</div>
                </div>
                <div class="retry-step">
                    <div class="step-circle {% if retry_attempt >= 3 %}completed{% elif healing_active and current_retry == 3 %}active{% endif %}">
                        {% if retry_attempt >= 3 %}✓{% else %}3{% endif %}
                    </div>
                    <div class="step-label">Attempt 3</div>
                    <div class="step-time">{{ attempt3_time }}</div>
                </div>
            </div>
            
            <!-- Progress Bar -->
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {{ healing_progress }}%;">
                    {{ healing_progress }}% Complete
                </div>
            </div>
            
            <!-- Current Action -->
            <div class="healing-stats">
                <div>📍 Current Action: <strong>{{ current_action }}</strong></div>
                <div>⏱️ Time Elapsed: <strong>{{ elapsed_time }}</strong></div>
                <div>🔄 Retry: <strong>{{ current_retry }}/3</strong></div>
            </div>
        </div>
        {% endif %}
        
        <!-- Healing Timeline -->
        <div class="healing-visualization" style="margin-top: 20px;">
            <div class="healing-title">📋 Healing Timeline</div>
            <div class="timeline" id="timeline">
                {% for event in healing_history %}
                <div class="timeline-item timeline-type-{{ event.type }}">
                    <div class="timeline-time">{{ event.time }}</div>
                    <div class="timeline-message">
                        <strong>{{ event.type }}:</strong> {{ event.message }}
                        {% if event.retry_count %} (Attempt {{ event.retry_count }}/3){% endif %}
                        {% if event.duration %} - Duration: {{ event.duration }}{% endif %}
                    </div>
                </div>
                {% endfor %}
                {% if not healing_history %}
                <div style="text-align: center; color: #888; padding: 20px;">
                    No healing events yet. Trigger a failure to see healing in action!
                </div>
                {% endif %}
            </div>
        </div>
        
        <!-- Statistics -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{{ total_requests }}</div>
                <div class="stat-label">Total Requests</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ failures }}</div>
                <div class="stat-label">Failures Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ healed_count }}</div>
                <div class="stat-label">Successfully Healed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ success_rate }}%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ healing_rate }}%</div>
                <div class="stat-label">Healing Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ avg_healing_time }}s</div>
                <div class="stat-label">Avg Healing Time</div>
            </div>
        </div>
        
        <!-- Workflow Explanation -->
        <div class="workflow-steps">
            <div style="font-weight: bold; margin-bottom: 10px;">⚙️ Healing Workflow (Real-time)</div>
            <div class="workflow-step">1️⃣ Failure Detection → System status changes to "FAILURE"</div>
            <div class="workflow-step">2️⃣ Healing Triggered → Auto-retry sequence starts (3 attempts)</div>
            <div class="workflow-step">3️⃣ Retry Attempt 1 → Waits 2 seconds, checks if recovered</div>
            <div class="workflow-step">4️⃣ Retry Attempt 2 → If failed, waits 2 more seconds, retries</div>
            <div class="workflow-step">5️⃣ Retry Attempt 3 → Final attempt, guaranteed recovery</div>
            <div class="workflow-step">6️⃣ System Healed → Status changes to "RECOVERED", logs success</div>
            <div class="workflow-step">💡 Total healing time: 4-8 seconds depending on retry attempts</div>
        </div>
        
        <!-- Controls -->
        <div style="margin: 20px 0; text-align: center;">
            <button onclick="location.reload()">🔄 Refresh Status</button>
            <button class="btn-danger" onclick="triggerFailure()">💥 Trigger Failure</button>
            <button class="btn-success" onclick="checkHealth()">✅ Health Check</button>
            <button onclick="clearHistory()">🗑️ Clear History</button>
        </div>
        
        <div class="auto-refresh-toggle">
            <label>
                <input type="checkbox" id="autoRefresh" onchange="toggleAutoRefresh()"> 
                Auto-refresh (updates every 2 seconds to show healing progress)
            </label>
        </div>
        
        <div class="footer">
            <div>⚡ Self-Healing Demo | 20% Random Failure Rate | Real-time Healing Visualization</div>
            <div>🕐 Last update: {{ timestamp }}</div>
        </div>
    </div>
    
    <script>
        let autoRefreshInterval = null;
        
        function toggleAutoRefresh() {
            const checkbox = document.getElementById('autoRefresh');
            if (checkbox.checked) {
                autoRefreshInterval = setInterval(function() {
                    location.reload();
                }, 2000);
            } else {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
            }
        }
        
        function triggerFailure() {
            if (confirm('Trigger a new failure? Healing will start automatically.')) {
                fetch('/fail')
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        location.reload();
                    });
            }
        }
        
        function checkHealth() {
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    alert('System Status: ' + data.status + 
                          '\\nFailures: ' + data.failures + 
                          '\\nHealed: ' + data.healed_count +
                          '\\nHealing Active: ' + (data.healing_active ? 'Yes' : 'No'));
                });
        }
        
        function clearHistory() {
            if (confirm('Clear healing history?')) {
                fetch('/clear_history')
                    .then(response => response.json())
                    .then(data => {
                        alert('History cleared');
                        location.reload();
                    });
            }
        }
        
        // Auto-scroll timeline to bottom
        const timeline = document.getElementById('timeline');
        if (timeline) {
            timeline.scrollTop = timeline.scrollHeight;
        }
    </script>
</body>
</html>
'''

def perform_healing():
    """Perform actual healing with real time delays"""
    global current_healing, healed_successfully, healing_history, failure_count
    
    with healing_lock:
        if current_healing is None:
            return
        
        start_time = time.time()
        healing_data = current_healing
        
        for attempt in range(1, 4):
            healing_data['current_retry'] = attempt
            healing_data['healing_progress'] = (attempt / 3) * 100
            healing_data['connector_progress'] = ((attempt - 1) / 2) * 100 if attempt <= 2 else 100
            
            # Update timeline
            healing_history.insert(0, {
                'time': datetime.now().strftime("%H:%M:%S"),
                'type': 'RETRY',
                'message': f'Retry attempt {attempt}/3 started',
                'retry_count': attempt,
                'duration': None
            })
            
            # Simulate actual work with real delay
            time.sleep(2)  # 2 second delay for each retry
            
            # Check if this attempt succeeds (80% chance, last attempt always succeeds)
            if attempt == 3 or random.random() < 0.8:
                # Healing successful
                healing_data['status'] = 'recovered'
                healing_data['healing_active'] = False
                healing_data['show_healing'] = True
                healing_data['retry_attempt'] = attempt
                healing_data['current_action'] = f'System healed on attempt {attempt}'
                healing_data['healing_progress'] = 100
                healing_data['connector_progress'] = 100
                
                total_time = round(time.time() - start_time, 1)
                healed_successfully += 1
                
                healing_history.insert(0, {
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'type': 'HEALED',
                    'message': f'System successfully healed after {attempt} retries',
                    'retry_count': attempt,
                    'duration': f'{total_time}s'
                })
                
                # Keep only last 15 events
                healing_history[:] = healing_history[:15]
                break
            else:
                # Retry failed, continue to next attempt
                healing_history.insert(0, {
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'type': 'RETRY_FAILED',
                    'message': f'Attempt {attempt} failed, retrying...',
                    'retry_count': attempt,
                    'duration': None
                })
                
                healing_data['current_action'] = f'Attempt {attempt} failed, retrying in 2 seconds...'
        
        # Mark healing as completed
        healing_data['healing_active'] = False
        healing_data['show_healing'] = True
        
        # Clear healing after 5 seconds of showing completion
        def clear_healing():
            time.sleep(5)
            with healing_lock:
                global current_healing
                if current_healing and not current_healing.get('healing_active', False):
                    current_healing = None
        
        threading.Thread(target=clear_healing, daemon=True).start()

@app.route('/')
def hello():
    global request_count, failure_count, current_healing, healed_successfully
    
    request_count += 1
    
    # Initialize default values
    status_type = 'healthy'
    status_message = '✅ System Operational'
    status_detail = 'All systems running normally'
    healing_active = False
    show_healing = False
    healing_progress = 0
    connector_progress = 0
    current_retry = 0
    retry_attempt = 0
    current_action = 'Idle'
    elapsed_time = '0s'
    attempt1_time = ''
    attempt2_time = ''
    attempt3_time = ''
    
    # Check if healing is in progress
    with healing_lock:
        if current_healing and current_healing.get('healing_active', False):
            healing_active = True
            show_healing = True
            status_type = 'healing'
            status_message = '🔧 Healing in Progress'
            status_detail = f'Attempt {current_healing.get("current_retry", 1)}/3 - System is recovering automatically'
            
            healing_progress = current_healing.get('healing_progress', 0)
            connector_progress = current_healing.get('connector_progress', 0)
            current_retry = current_healing.get('current_retry', 1)
            retry_attempt = current_healing.get('retry_attempt', 0)
            current_action = current_healing.get('current_action', 'Healing in progress')
            
            elapsed = time.time() - current_healing.get('start_time', time.time())
            elapsed_time = f'{round(elapsed, 1)}s'
            
            # Set attempt times
            if current_retry >= 1:
                attempt1_time = '✓ Completed'
            else:
                attempt1_time = 'Pending'
            
            if current_retry >= 2:
                attempt2_time = '✓ Completed'
            elif current_retry == 2:
                attempt2_time = 'In progress...'
            else:
                attempt2_time = 'Pending'
            
            if current_retry >= 3:
                attempt3_time = '✓ Completed'
            elif current_retry == 3:
                attempt3_time = 'In progress...'
            else:
                attempt3_time = 'Pending'
                
        elif current_healing and current_healing.get('show_healing', False) and not current_healing.get('healing_active', False):
            # Show completed healing
            show_healing = True
            status_type = 'recovered'
            status_message = '✅ System Recovered'
            status_detail = f'Successfully healed after {current_healing.get("retry_attempt", 0)} retries'
            healing_progress = 100
            connector_progress = 100
            current_retry = current_healing.get('retry_attempt', 3)
            retry_attempt = current_healing.get('retry_attempt', 3)
            current_action = 'Healing complete'
            attempt1_time = '✓ Completed'
            attempt2_time = '✓ Completed' if current_retry >= 2 else '-'
            attempt3_time = '✓ Completed' if current_retry >= 3 else '-'
        else:
            # Random failure chance (20%)
            if random.random() < 0.2:
                failure_count += 1
                status_type = 'failure'
                status_message = '❌ Failure Detected'
                status_detail = 'Initiating self-healing sequence...'
                
                # Start healing in background thread
                healing_data = {
                    'healing_active': True,
                    'show_healing': True,
                    'current_retry': 1,
                    'retry_attempt': 0,
                    'healing_progress': 0,
                    'connector_progress': 0,
                    'current_action': 'Starting healing process...',
                    'start_time': time.time()
                }
                current_healing = healing_data
                healing_active = True
                show_healing = True
                
                # Start healing process
                threading.Thread(target=perform_healing, daemon=True).start()
                
                # Add failure event to timeline
                healing_history.insert(0, {
                    'time': datetime.now().strftime("%H:%M:%S"),
                    'type': 'FAILURE',
                    'message': 'System failure detected, starting healing',
                    'retry_count': None,
                    'duration': None
                })
                healing_history[:] = healing_history[:15]
    
    # Calculate statistics
    if request_count > 0:
        success_rate = round(((request_count - failure_count) / request_count) * 100, 1)
    else:
        success_rate = 100
    
    if failure_count > 0:
        healing_rate = round((healed_successfully / failure_count) * 100, 1)
    else:
        healing_rate = 100
    
    # Calculate average healing time from history
    healing_times = []
    for event in healing_history:
        if event.get('type') == 'HEALED' and event.get('duration'):
            try:
                healing_times.append(float(event['duration'].replace('s', '')))
            except:
                pass
    
    avg_healing_time = round(sum(healing_times) / len(healing_times), 1) if healing_times else 0
    
    return render_template_string(
        HTML_TEMPLATE,
        status_type=status_type,
        status_message=status_message,
        status_detail=status_detail,
        healing_active=healing_active,
        show_healing=show_healing,
        healing_progress=healing_progress,
        connector_progress=connector_progress,
        current_retry=current_retry,
        retry_attempt=retry_attempt,
        current_action=current_action,
        elapsed_time=elapsed_time,
        attempt1_time=attempt1_time,
        attempt2_time=attempt2_time,
        attempt3_time=attempt3_time,
        healing_history=healing_history,
        total_requests=request_count,
        failures=failure_count,
        healed_count=healed_successfully,
        success_rate=success_rate,
        healing_rate=healing_rate,
        avg_healing_time=avg_healing_time,
        timestamp=datetime.now().strftime("%H:%M:%S")
    ), 200

@app.route('/health')
def health():
    with healing_lock:
        healing_active = current_healing is not None and current_healing.get('healing_active', False)
    
    return jsonify({
        "status": "healthy" if not healing_active else "healing",
        "timestamp": datetime.now().isoformat(),
        "requests": request_count,
        "failures": failure_count,
        "healed_count": healed_successfully,
        "healing_active": healing_active
    }), 200

@app.route('/fail')
def force_fail():
    global failure_count, current_healing, healing_history
    
    with healing_lock:
        failure_count += 1
        
        # Create new healing process
        healing_data = {
            'healing_active': True,
            'show_healing': True,
            'current_retry': 1,
            'retry_attempt': 0,
            'healing_progress': 0,
            'connector_progress': 0,
            'current_action': 'Starting healing process...',
            'start_time': time.time()
        }
        current_healing = healing_data
        
        # Add failure event
        healing_history.insert(0, {
            'time': datetime.now().strftime("%H:%M:%S"),
            'type': 'FAILURE',
            'message': 'Manual failure triggered, starting healing',
            'retry_count': None,
            'duration': None
        })
        healing_history[:] = healing_history[:15]
        
        # Start healing thread
        threading.Thread(target=perform_healing, daemon=True).start()
    
    return jsonify({
        "status": "failure",
        "message": "Manual failure triggered - healing process started",
        "healing_started": True
    }), 200

@app.route('/stats')
def stats():
    if request_count > 0:
        success_rate = round(((request_count - failure_count) / request_count) * 100, 2)
    else:
        success_rate = 100
    
    if failure_count > 0:
        healing_rate = round((healed_successfully / failure_count) * 100, 2)
    else:
        healing_rate = 100
    
    return jsonify({
        "total_requests": request_count,
        "failures": failure_count,
        "healed_count": healed_successfully,
        "success_rate": success_rate,
        "healing_rate": healing_rate,
        "healing_events": len(healing_history)
    }), 200

@app.route('/clear_history')
def clear_history():
    global healing_history
    healing_history = []
    return jsonify({"message": "Healing history cleared"}), 200

@app.route('/reset')
def reset():
    global request_count, failure_count, healing_history, healed_successfully, current_healing
    request_count = 0
    failure_count = 0
    healing_history = []
    healed_successfully = 0
    current_healing = None
    return jsonify({"message": "All stats reset"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("🔄 SELF-HEALING PIPELINE - FULLY FUNCTIONAL DEMO")
    print("="*60)
    print(f"📍 Application URL: http://localhost:{port}")
    print(f"✅ Health Check: http://localhost:{port}/health")
    print(f"📊 Statistics: http://localhost:{port}/stats")
    print("\n⚙️ HOW IT WORKS:")
    print("   • 20% random failure chance on each request")
    print("   • When failure occurs, healing starts automatically")
    print("   • System attempts 3 retries with 2-second delays")
    print("   • Each retry has 80% success chance (3rd always succeeds)")
    print("   • Total healing time: 4-8 seconds")
    print("   • Enable 'Auto-refresh' to watch healing in real-time")
    print("\n🎮 TEST IT:")
    print("   • Click 'Trigger Failure' to manually start healing")
    print("   • Enable auto-refresh to see progress update automatically")
    print("   • Watch the retry circles animate in real-time")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)