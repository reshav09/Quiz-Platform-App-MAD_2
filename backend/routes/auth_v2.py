from flask import Blueprint, request, jsonify, current_app
from backend.models.database import db, User
from backend.auth.jwt_utils import create_access_token, jwt_required, get_jwt_identity
import hashlib
from datetime import datetime
import re

auth_v2_bp = Blueprint('auth_v2', __name__, url_prefix='/api/v2/auth')

# Validation regex patterns
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{4,20}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
PASSWORD_PATTERN = re.compile(r'^.{8,}$')  # At least 8 chars

@auth_v2_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with validation"""
    try:
        data = request.get_json()
        
        # Check for required fields
        required_fields = ['username', 'password', 'full_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
        
        # Validate username
        if not USERNAME_PATTERN.match(data['username']):
            return jsonify({
                'status': 'error', 
                'message': 'Username must be 4-20 characters and contain only letters, numbers, and underscores'
            }), 400
            
        # Validate password
        if not PASSWORD_PATTERN.match(data['password']):
            return jsonify({
                'status': 'error', 
                'message': 'Password must be at least 8 characters'
            }), 400
            
        # Check if username already exists
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'status': 'error', 'message': 'Username already exists'}), 409
            
        # Hash password for security
        hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()
        
        # Create new user
        new_user = User(
            username=data['username'],
            password=hashed_password,
            full_name=data['full_name'],
            qualification=data.get('qualification'),
            dob=datetime.strptime(data['dob'], '%Y-%m-%d') if 'dob' in data and data['dob'] else None,
            report_format=data.get('report_format', 'html')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Generate access token for the new user
        access_token = create_access_token(new_user.id, is_admin=False)
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'user': new_user.to_dict(exclude=['password']),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@auth_v2_bp.route('/login', methods=['POST'])
def login():
    """Login a user and return JWT token"""
    try:
        data = request.get_json()
        
        # Check for required fields
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'status': 'error', 'message': 'Username and password are required'}), 400
            
        # Authenticate user
        user = User.authenticate(data['username'], data['password'])
        
        if not user:
            return jsonify({'status': 'error', 'message': 'Invalid username or password'}), 401
            
        # Generate access token
        access_token = create_access_token(user.id, is_admin=False)
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'user': user.to_dict(exclude=['password']),
            'access_token': access_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@auth_v2_bp.route('/profile', methods=['GET'])
@jwt_required
def get_profile():
    """Get user profile information"""
    try:
        user_id = get_jwt_identity()
        
        # Get user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        return jsonify({
            'status': 'success',
            'user': user.to_dict(exclude=['password'])
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@auth_v2_bp.route('/profile', methods=['PUT'])
@jwt_required
def update_profile():
    """Update user profile information"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name']
            
        if 'qualification' in data:
            user.qualification = data['qualification']
            
        if 'dob' in data and data['dob']:
            try:
                user.dob = datetime.strptime(data['dob'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Invalid date format for DOB. Use YYYY-MM-DD'}), 400
                
        if 'report_format' in data:
            if data['report_format'] not in ['html', 'json', 'csv']:
                return jsonify({'status': 'error', 'message': 'Invalid report format. Use html, json, or csv'}), 400
            user.report_format = data['report_format']
            
        # Handle password change if provided
        if 'current_password' in data and 'new_password' in data:
            # Verify current password
            if not user.verify_password(data['current_password']):
                return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 401
                
            # Validate new password
            if not PASSWORD_PATTERN.match(data['new_password']):
                return jsonify({
                    'status': 'error', 
                    'message': 'Password must be at least 8 characters'
                }), 400
                
            # Update password
            user.password = hashlib.sha256(data['new_password'].encode()).hexdigest()
            
        # Update timestamp and commit changes
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Profile updated successfully',
            'user': user.to_dict(exclude=['password'])
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating user profile: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@auth_v2_bp.route('/verify-token', methods=['GET'])
@jwt_required
def verify_token():
    """Verify if the token is valid"""
    try:
        user_id = get_jwt_identity()
        
        # Get user from database to ensure they still exist
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        return jsonify({
            'status': 'success',
            'message': 'Token is valid',
            'user_id': user_id
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token verification error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@auth_v2_bp.route('/change-password', methods=['POST'])
@jwt_required
def change_password():
    """Change user password"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Check for required fields
        if not data or 'current_password' not in data or 'new_password' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Current password and new password are required'
            }), 400
            
        # Get user from database
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
            
        # Verify current password
        if not user.verify_password(data['current_password']):
            return jsonify({'status': 'error', 'message': 'Current password is incorrect'}), 401
            
        # Validate new password
        if not PASSWORD_PATTERN.match(data['new_password']):
            return jsonify({
                'status': 'error', 
                'message': 'Password must be at least 8 characters'
            }), 400
            
        # Update password
        user.password = hashlib.sha256(data['new_password'].encode()).hexdigest()
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Password change error: {e}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500