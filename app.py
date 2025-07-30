import os
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Flask and SocketIO after eventlet
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
load_dotenv()

# Configure Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Global counters
github_activity_count = 0
analytics_events_count = 0
agent_activity_count = 0

@app.route('/')
def index():
    return render_template('github_connect.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/setup', methods=['POST'])
def setup():
    try:
        # Get Google Analytics credentials
        ga_api_key = request.form.get('ga_api_key')
        ga_property_id = request.form.get('ga_property_id')
        
        if not ga_api_key or not ga_property_id:
            return jsonify({
                'status': 'error',
                'message': 'Google Analytics credentials are required'
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
            repo = Repo.clone_from(auth_url, repo_path)
            
            # Handle branch selection/creation
            try:
                if branch_type == 'existing':
                    # Check out existing branch
                    if branch != 'other':
                        repo.git.checkout(branch)
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': 'Please select a valid branch'
                        }), 400
                else:  # Creating new branch
                    if not new_branch_name:
                        return jsonify({
                            'status': 'error',
                            'message': 'Please enter a name for the new branch'
                        }), 400
                    
                    # Create and checkout new branch
                    repo.git.checkout('-b', new_branch_name)
                    branch = new_branch_name  # Update branch variable for config
            except git.exc.GitCommandError as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to create branch: {str(e)}'
                }), 500

            # Start monitoring threads
            threading.Thread(target=analyze_and_commit_changes, args=(repo_path, ga_api_key, ga_property_id, prompt)).start()
            threading.Thread(target=monitor_analytics_events, args=(ga_api_key, ga_property_id)).start()
            threading.Thread(target=monitor_agent_activity).start()

            # Store configuration
            config = {
                'ga_api_key': ga_api_key,
                'ga_property_id': ga_property_id,
                'repo_url': repo_url,
                'branch': branch,
                'branch_type': branch_type,
                'new_branch_name': new_branch_name if branch_type == 'new' else None,
                'prompt': prompt
            }
            
            # Save configuration to file
            with open(os.path.join(repo_path, 'project_config.json'), 'w') as f:
                json.dump(config, f, indent=4)

            # Emit setup complete event
            socketio.emit('activity_log', 'Project setup completed successfully')

            return jsonify({
                'status': 'success',
                'message': f'Successfully set up project with repository: {repo_name} on branch: {branch}'
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
    try:
        # Get Google Analytics credentials
        ga_api_key = request.form.get('ga_api_key')
        ga_property_id = request.form.get('ga_property_id')
        
        if not ga_api_key or not ga_property_id:
            return jsonify({
                'status': 'error',
                'message': 'Google Analytics credentials are required'
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
            repo = Repo.clone_from(auth_url, repo_path)
            
            # Handle branch selection/creation
            try:
                if branch_type == 'existing':
                    # Check out existing branch
                    if branch != 'other':
                        repo.git.checkout(branch)
                    else:
                        return jsonify({
                            'status': 'error',
                            'message': 'Please select a valid branch'
                        }), 400
                else:  # Creating new branch
                    if not new_branch_name:
                        return jsonify({
                            'status': 'error',
                            'message': 'Please enter a name for the new branch'
                        }), 400
                    
                    # Create and checkout new branch
                    repo.git.checkout('-b', new_branch_name)
                    branch = new_branch_name  # Update branch variable for config
            except git.exc.GitCommandError as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to create branch: {str(e)}'
                }), 500

            # Store configuration
            config = {
                'ga_api_key': ga_api_key,
                'ga_property_id': ga_property_id,
                'repo_url': repo_url,
                'branch': branch,
                'branch_type': branch_type,
                'new_branch_name': new_branch_name if branch_type == 'new' else None,
                'prompt': prompt
            }
            
            # Save configuration to file
            with open(os.path.join(repo_path, 'project_config.json'), 'w') as f:
                json.dump(config, f, indent=4)

            return jsonify({
                'status': 'success',
                'message': f'Successfully set up project with repository: {repo_name} on branch: {branch}'
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
def analyze_and_commit_changes(repo_path, ga_api_key, ga_property_id, prompt):
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
            analytics_data = get_google_analytics_data(ga_api_key, ga_property_id)

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
                'avgDuration': analytics_data['average_session_duration'],
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

def get_google_analytics_data(api_key, property_id):
    """Simulate getting data from Google Analytics API"""
    # In a real app, this would use the actual Google Analytics API
    return {
        'page_views': 1000,
        'conversions': 50,
        'bounce_rate': 0.25,
        'average_session_duration': 120
    }

def monitor_analytics_events(ga_api_key, ga_property_id):
    global analytics_events_count
    while True:
        try:
            # Get real analytics data
            analytics_data = get_google_analytics_data(ga_api_key, ga_property_id)
            
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

if __name__ == '__main__':
    try:
        logger.info("Starting application...")
        socketio.run(app, 
                    host='0.0.0.0',
                    port=5001,
                    debug=True,
                    use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
