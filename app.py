from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os
from dotenv import load_dotenv
import git
from git import Repo
import shutil
import json
import eventlet
import threading
import time
from datetime import datetime

eventlet.monkey_patch()

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
            threading.Thread(target=monitor_github_activity, args=(repo_path,)).start()
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
def monitor_github_activity(repo_path):
    global github_activity_count
    while True:
        try:
            # Get git log
            repo = Repo(repo_path)
            commits = list(repo.iter_commits('HEAD', max_count=10))
            
            # Update activity count
            github_activity_count = len(commits)
            socketio.emit('github_activity', {'count': github_activity_count})
            
            # Emit activity log
            if commits:
                last_commit = commits[0]
                socketio.emit('activity_log', f'New commit detected: {last_commit.message.strip()}')
                
        except Exception as e:
            socketio.emit('activity_log', f'GitHub monitoring error: {str(e)}')
        
        time.sleep(30)  # Check every 30 seconds

def monitor_analytics_events(ga_api_key, ga_property_id):
    global analytics_events_count
    while True:
        try:
            # Simulate analytics events (in a real app, you'd connect to GA API here)
            analytics_events_count += 1
            socketio.emit('analytics_event', {
                'count': analytics_events_count,
                'eventType': 'Page View'
            })
            
            # Emit activity log
            socketio.emit('activity_log', 'Analytics event processed')
            
        except Exception as e:
            socketio.emit('activity_log', f'Analytics monitoring error: {str(e)}')
        
        time.sleep(10)  # Check every 10 seconds

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
    socketio.run(app, debug=True, port=5001)
