import os
# This must be set before any other imports
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

import sys
import time
import json
import shutil
import threading
import logging
from datetime import datetime
from dotenv import load_dotenv
import git
from git import Repo
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Flask and SocketIO after eventlet
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
load_dotenv()

# Configure session
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-please-change')

# Configure Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Import GA OAuth after app is created
from ga_oauth import authorize, oauth2callback, get_analytics_data

# Global counters
github_activity_count = 0
analytics_events_count = 0
agent_activity_count = 0

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'credentials' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    # If user is already authenticated, redirect to dashboard
    if 'credentials' in session:
        return redirect(url_for('analytics_dashboard'))
    return render_template('ga_connect.html')

@app.route('/authorize')
def authorize_google():
    return authorize()

@app.route('/oauth2callback')
def oauth_callback():
    return oauth2callback()

@app.route('/analytics')
@login_required
def analytics_dashboard():
    # Get property ID from session or request args
    property_id = session.get('ga_property_id') or request.args.get('property_id')
    if not property_id:
        return redirect(url_for('index'))
    
    # Store property ID in session
    session['ga_property_id'] = property_id
    
    # Get analytics data
    analytics_data = get_analytics_data(property_id)
    
    if not analytics_data:
        return render_template('error.html', 
                            title='Analytics Error',
                            message='Could not fetch analytics data. Please try again.')
    
    return render_template('dashboard.html', 
                         analytics_data=analytics_data,
                         property_id=property_id)

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    return redirect(url_for('index'))

@app.route('/setup', methods=['POST'])
def setup():
    try:
        # Get Google Analytics credentials
        ga_property_id = request.form.get('ga_property_id')
        
        if not ga_property_id:
            return jsonify({
                'status': 'error',
                'message': 'Google Analytics Property ID is required'
            }), 400

        # Get GitHub repository information
        repo_url = request.form.get('repo_url')
        token = request.form.get('token')
        branch_type = request.form.get('branch_type')
        branch = request.form.get('branch')
        new_branch_name = request.form.get('new_branch_name')
        prompt = request.form.get('prompt')
        
        if not repo_url or not token:
            return jsonify({
                'status': 'error',
                'message': 'GitHub repository URL and token are required'
            }), 400

        # Validate repository URL format
        if not repo_url.startswith('https://github.com/'):
            return jsonify({
                'status': 'error',
                'message': 'Please provide a valid GitHub repository URL'
            }), 400

        # Replace username with token in URL
        url_parts = repo_url.split('/')
        url_parts[2] = f'{token}@github.com'
        auth_url = '/'.join(url_parts)

        # Create a directory for the repository
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = os.path.join('repos', repo_name)
        
        try:
            # Clone the repository
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            repo_path = os.path.join('repos', repo_name)
            
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
            
            Repo.clone_from(auth_url, repo_path)
            logging.info(f'Successfully cloned repository: {repo_url}')
        except Exception as e:
            logging.error(f'Error cloning repository: {str(e)}')
            return jsonify({'error': f'Failed to clone repository: {str(e)}'}), 500

        # Start analysis and monitoring in background threads
        if repo_path:
            threading.Thread(target=analyze_and_commit_changes, args=(repo_path, ga_property_id, prompt)).start()
            threading.Thread(target=monitor_analytics_events, args=(ga_property_id,)).start()

        return jsonify({
            'status': 'success',
            'message': 'Analysis started',
            'repo_path': repo_path,
            'ga_property_id': ga_property_id,
            'prompt': prompt
        })
    except Exception as e:
        logging.error(f'Error in setup: {str(e)}')
        return jsonify({'error': str(e)}), 500

# Removed old GitHub connect route as we now have a unified setup route
def github_connect():
    try:
        repo_url = request.form.get('repo_url')
        token = request.form.get('token')
        
        if not repo_url or not token:
            return jsonify({
                'status': 'error',
                'message': 'Both repository URL and token are required'
            }), 400

        # Validate repository URL format
        if not repo_url.startswith('https://github.com/'):
            return jsonify({
                'status': 'error',
                'message': 'Please provide a valid GitHub repository URL'
            }), 400

        # Replace username with token in URL
        url_parts = repo_url.split('/')
        url_parts[2] = f'{token}@github.com'
        auth_url = '/'.join(url_parts)

        # Create a directory for the repository
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = os.path.join('repos', repo_name)
        
        try:
            # Clone the repository
            Repo.clone_from(auth_url, repo_path)
            return jsonify({
                'status': 'success',
                'message': f'Successfully connected to repository: {repo_name}'
            })
        except git.exc.GitError as e:
            return jsonify({
                'status': 'error',
                'message': f'Failed to clone repository: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/connect', methods=['POST'])
def connect():
    try:
        api_key = request.form.get('api_key')
        property_id = request.form.get('property_id')
        
        if not api_key or not property_id:
            return jsonify({
                'status': 'error',
                'message': 'Both API key and Property ID are required'
            }), 400
        
        # Here you would typically validate the API key and property ID
        # For now, we'll just store them in environment variables
        os.environ['GA_API_KEY'] = api_key
        os.environ['GA_PROPERTY_ID'] = property_id
        
        return jsonify({
            'status': 'success',
            'message': 'Successfully connected to Google Analytics'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Monitoring functions
def analyze_and_commit_changes(repo_path, ga_property_id, prompt):
    """Analyze Google Analytics data and make code changes based on the prompt"""
    global github_activity_count
    while True:
        try:
            # Load project configuration
            config_path = os.path.join(repo_path, 'project_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Simulate Google Analytics API connection
            # In a real app, this would use the actual Google Analytics API
            analytics_data = get_google_analytics_data(ga_property_id)

            # Analyze data and generate strategy
            strategy = analyze_data_and_generate_strategy(
                analytics_data,
                config['prompt']
            )

            # Emit analytics update
            socketio.emit('analytics_event', {
                'pageViews': analytics_data['page_views'],
                'conversions': analytics_data['conversions'],
                'bounceRate': analytics_data['bounce_rate'],
                'avgDuration': analytics_data['avg_session_duration'],
                'goal': config['prompt'],
                'strategy': strategy
            })

            # Generate code changes based on strategy
            changes = generate_code_changes(
                analytics_data,
                strategy,
                config['prompt']
            )

            # Load project configuration
            config_path = os.path.join(repo_path, 'project_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Analyze data and generate code changes based on prompt
            changes = analyze_data_and_generate_code(
                analytics_data,
                config['prompt']
            )

            if changes:
                # Apply changes to the codebase
                apply_code_changes(repo_path, changes)

                # Commit changes
                repo = Repo(repo_path)
                repo.git.add('.')
                commit_message = f"AI-assisted update: {config['prompt']}"
                repo.git.commit('-m', commit_message)

                # Update activity count
                github_activity_count = len(list(repo.iter_commits('HEAD', max_count=10)))
                socketio.emit('github_activity', {
                    'count': github_activity_count,
                    'commit_message': commit_message
                })

                # Emit activity log
                socketio.emit('activity_log', f'AI made changes: {commit_message}')

        except Exception as e:
            socketio.emit('activity_log', f'Error in analysis and commit: {str(e)}')
        
        time.sleep(300)  # Analyze and commit every 5 minutes

def analyze_data_and_generate_strategy(analytics_data, prompt):
    """Generate a detailed strategy based on analytics data and user prompt"""
    # This is where you would integrate with your AI model
    # For now, we'll simulate a strategy based on common patterns
    strategy = ""
    
    if 'optimize performance' in prompt.lower():
        strategy = """Optimizing performance:
        1. Reducing image sizes
        2. Implementing lazy loading
        3. Minifying CSS and JS files"""
            
    if 'increase conversions' in prompt.lower():
        strategy = """Improving conversions:
        1. Adding clearer CTAs
        2. Optimizing checkout flow
        3. Adding trust signals"""
            
    if 'reduce bounce rate' in prompt.lower():
        strategy = """Reducing bounce rate:
        1. Improving page load times
        2. Adding better navigation
        3. Enhancing mobile experience"""
            
    return strategy

def generate_code_changes(analytics_data, strategy, prompt):
    """Generate specific code changes based on strategy and analytics data"""
    changes = []
    
    # Parse strategy into specific actions
    actions = strategy.split('\n')
    for action in actions:
        if 'Optimizing performance' in action:
            changes.append({
                'file': 'index.html',
                'changes': 'Optimized HTML structure and added lazy loading'
            })
            changes.append({
                'file': 'styles.css',
                'changes': 'Added CSS optimizations'
            })
        elif 'Improving conversions' in action:
            changes.append({
                'file': 'main.js',
                'changes': 'Added conversion optimization features'
            })
        elif 'Reducing bounce rate' in action:
            changes.append({
                'file': 'index.html',
                'changes': 'Improved mobile responsiveness'
            })
    
    return changes

def apply_code_changes(repo_path, changes):
    """Apply code changes to the repository with detailed logging"""
    for change in changes:
        file_path = os.path.join(repo_path, change['file'])
        if os.path.exists(file_path):
            try:
                # For demo purposes, we'll just append a comment
                with open(file_path, 'a') as f:
                    f.write(f'\n\n/* AI Update: {change["changes"]} */\n')
                
                # Emit detailed activity log
                socketio.emit('agent_activity', {
                    'file': change['file'],
                    'changes': change['changes'],
                    'status': 'success'
                })
                
            except Exception as e:
                socketio.emit('agent_activity', {
                    'file': change['file'],
                    'changes': change['changes'],
                    'status': 'error',
                    'error': str(e)
                })
                continue

    # Emit overall success message
    socketio.emit('activity_log', 'Code changes applied successfully', 'success')

def get_google_analytics_data(property_id):
    """
    Get Google Analytics data using OAuth 2.0
    """
    try:
        if 'credentials' not in session:
            return {'error': 'User not authenticated'}

        # Get the stored credentials
        credentials = google.oauth2.credentials.Credentials(
            **session['credentials']
        )

        # Build the analytics data client
        analytics = build('analyticsdata', 'v1beta', credentials=credentials)

        # Define the request
        request = {
            'dateRanges': [
                {
                    'startDate': '30daysAgo',
                    'endDate': 'today'
                }
            ],
            'metrics': [
                {'name': 'activeUsers'},
                {'name': 'sessions'},
                {'name': 'bounceRate'},
                {'name': 'averageSessionDuration'},
                {'name': 'screenPageViews'},
                {'name': 'screenPageViewsPerSession'},
                {'name': 'newUsers'},
                {'name': 'conversions'}
            ],
            'dimensions': [{'name': 'pageTitle'}],
            'limit': 1000
        }

        # Make the request
        response = analytics.properties().runReport(
            property=f'properties/{property_id}',
            body=request
        ).execute()

        # Process the response
        if not response.get('rows'):
            return {'error': 'No data found'}

        # Extract metrics
        metrics = {}
        for row in response['rows']:
            for i, header in enumerate(response['metricHeaders']):
                metric_name = header['name'].replace(' ', '_').lower()
                metrics[metric_name] = row['metricValues'][i]['value']

        # Get top pages
        top_pages = []
        for row in response['rows'][:5]:  # Get top 5 pages
            page = row['dimensionValues'][0]['value']
            views = int(row['metricValues'][5]['value'])  # screenPageViews
            top_pages.append({'page': page, 'views': views})

        return {
            'users': int(metrics.get('active_users', 0)),
            'sessions': int(metrics.get('sessions', 0)),
            'bounce_rate': float(metrics.get('bounce_rate', 0)),
            'avg_session_duration': float(metrics.get('average_session_duration', 0)),
            'page_views': int(metrics.get('screen_page_views', 0)),
            'pages_per_session': float(metrics.get('screen_page_views_per_session', 0)),
            'new_users': int(metrics.get('new_users', 0)),
            'top_pages': top_pages
        }

    except Exception as e:
        logging.error(f'Error getting Google Analytics data: {str(e)}')
        return None

def monitor_analytics_events(ga_property_id):
    global analytics_events_count
    while True:
        try:
            # Get real analytics data
            analytics_data = get_google_analytics_data(ga_property_id)
            
            # Update analytics count
            analytics_events_count += 1
            
            # Emit analytics update
            socketio.emit('analytics_event', {
                'count': analytics_events_count,
                'data': analytics_data,
                'eventType': 'Metrics Update'
            })
            
            # Emit activity log
            socketio.emit('activity_log', {
                'message': 'Analytics metrics updated',
                'type': 'info'
            })
            
        except Exception as e:
            socketio.emit('activity_log', {
                'message': f'Analytics monitoring error: {str(e)}',
                'type': 'error'
            })
        
        time.sleep(30)  # Update every 30 seconds

def monitor_agent_activity():
    global agent_activity_count
    while True:
        try:
            # Simulate agent activity (in a real app, you'd track AI agent tasks here)
            agent_activity_count += 1
            socketio.emit('agent_activity', {'count': agent_activity_count})
            
            # Emit activity log
            socketio.emit('activity_log', 'Agent task completed')
            
        except Exception as e:
            socketio.emit('activity_log', f'Agent monitoring error: {str(e)}')
        
        time.sleep(5)  # Check every 5 seconds

def generate_self_signed_cert():
    """Generate a self-signed certificate for local development"""
    from OpenSSL import crypto
    from pathlib import Path
    import os
    
    cert_dir = os.path.join(os.path.dirname(__file__), 'certs')
    os.makedirs(cert_dir, exist_ok=True)
    
    key_path = os.path.join(cert_dir, 'key.pem')
    cert_path = os.path.join(cert_dir, 'cert.pem')
    
    if not os.path.exists(key_path) or not os.path.exists(cert_path):
        # Generate key
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)
        
        # Generate certificate
        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "State"
        cert.get_subject().L = "City"
        cert.get_subject().O = "Organization"
        cert.get_subject().OU = "Organizational Unit"
        cert.get_subject().CN = "localhost"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # Valid for 1 year
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')
        
        # Save certificate
        with open(cert_path, 'wb+') as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        with open(key_path, 'wb+') as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    
    return cert_path, key_path

if __name__ == '__main__':
    try:
        logger.info("Starting application...")
        
        # For development with self-signed certificate
        import os
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
        # Start the Flask development server with SSL
        # Note: This is for development only
        context = ('ssl/cert.pem', 'ssl/key.pem')
        
        # Start the Flask development server directly
        # This will use Werkzeug's development server with SSL
        app.run(
            host='0.0.0.0',
            port=5002,  # Changed from 5001 to 5002 to avoid conflicts
            debug=True,
            ssl_context=context
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
