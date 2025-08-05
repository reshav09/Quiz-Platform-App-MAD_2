import os
import jwt
from functools import wraps
from flask import request, jsonify, current_app, g
from datetime import datetime, timedelta, timezone
from models.database import User, Admin

def decode_token(token):
    return jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])

def create_access_token(user_id, is_admin=False, expires_delta=None):
    """
    Create a JWT access token for authentication.
    
    Args:
        user_id: The user ID to encode in the token
        is_admin: Whether this token is for an admin user
        expires_delta: Optional expiration time override
        
    Returns:
        str: JWT access token
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=24)  # Default 24 hour expiration
        
    payload = {
        'sub': user_id,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + expires_delta
    }
    
    if is_admin:
        payload['admin'] = True
        
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token

def get_jwt_identity():
    """
    Get the user ID from the JWT token in the current request.
    
    Returns:
        int: The user ID from the token
    """
    token = get_token_from_request()
    if not token:
        return None
        
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload.get('sub')
    except jwt.PyJWTError:
        return None

def is_admin_token():
    """
    Check if the current token belongs to an admin user.
    
    Returns:
        bool: True if the token is for an admin, False otherwise
    """
    token = get_token_from_request()
    if not token:
        return False
        
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload.get('admin', False)
    except jwt.PyJWTError:
        return False

def get_token_from_request():
    """
    Extract the JWT token from the current request.
    
    Returns:
        str or None: The JWT token if present, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
        
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
        
    return parts[1]

def jwt_required(f):
    """
    Decorator to require a valid JWT token for a route.
    
    If no valid token is present, returns a 401 Unauthorized response.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({'status': 'error', 'message': 'Missing authorization token'}), 401
            
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Store user ID in g for access in the view function
            g.user_id = payload.get('sub')
            g.is_admin = payload.get('admin', False)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """
    Decorator to require an admin JWT token for a route.
    
    If no valid admin token is present, returns a 403 Forbidden response.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({'status': 'error', 'message': 'Missing authorization token'}), 401
            
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Check if token has admin flag
            if not payload.get('admin', False):
                return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
                
            # Store user ID in g for access in the view function
            g.user_id = payload.get('sub')
            g.is_admin = True
            
        except jwt.ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'status': 'error', 'message': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated