import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from flask import session, redirect, url_for, request
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth 2.0 configuration
CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
REDIRECT_URI = 'http://localhost:5001/oauth2callback'

def get_ga_service():
    """Get an authorized Google Analytics Data API service client."""
    if 'credentials' not in session:
        return None
    
    credentials = Credentials(
        **session['credentials']
    )
    
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            return None
    
    # Save the credentials back to the session
    session['credentials'] = credentials_to_dict(credentials)
    
    # Build the service
    service = build('analyticsdata', 'v1beta', credentials=credentials)
    return service

def credentials_to_dict(credentials):
    """Convert credentials object to a dictionary."""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def get_flow():
    """Create a flow instance to manage the OAuth 2.0 Authorization Grant Flow."""
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow

def authorize():
    """Start the OAuth flow to authorize the application."""
    flow = get_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    session['state'] = state
    return redirect(authorization_url)

def oauth2callback():
    """Handle the OAuth 2.0 server response."""
    state = session.get('state')
    
    flow = get_flow()
    flow.fetch_token(authorization_response=request.url)
    
    # Store the credentials in the session
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    
    # Redirect to the analytics page
    return redirect(url_for('analytics_dashboard'))

def get_analytics_data(property_id, date_range='7daysAgo'):
    """Fetch analytics data for the given property."""
    service = get_ga_service()
    if not service:
        return None
    
    try:
        request_body = {
            'dateRanges': [{'startDate': date_range, 'endDate': 'today'}],
            'metrics': [
                {'name': 'activeUsers'},
                {'name': 'sessions'},
                {'name': 'bounceRate'},
                {'name': 'averageSessionDuration'}
            ],
            'dimensions': [{'name': 'date'}]  # Add date dimension for time series data
        }
        
        response = service.properties().runReport(
            property=f'properties/{property_id}',
            body=request_body
        ).execute()
        
        return response
    except Exception as e:
        logger.error(f"Error fetching analytics data: {str(e)}")
        return None
