from sqlalchemy.orm import class_mapper
from datetime import datetime
import json

class SerializerMixin:
    """
    Mixin class to add serialization capabilities to SQLAlchemy models.
    
    This mixin provides methods to convert a model instance to dictionary and JSON formats,
    with support for customizing the output by excluding specific fields or including 
    related objects.
    
    Usage:
        class User(db.Model, SerializerMixin):
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True, nullable=False)
            email = db.Column(db.String(120), unique=True, nullable=False)
            password = db.Column(db.String(120), nullable=False)
            
            # Then you can use:
            user = User.query.get(1)
            user_dict = user.to_dict()  # Converts to dictionary
            user_json = user.to_json()  # Converts to JSON string
            
            # Exclude sensitive fields:
            safe_user = user.to_dict(exclude=['password'])
            
            # Include related objects (if defined as relationships):
            user_with_posts = user.to_dict(include=['posts'])
    """
    
    def to_dict(self, exclude=None, include=None):
        """
        Convert model instance to dictionary.
        
        Args:
            exclude (list): List of field names to exclude from output
            include (list): List of relationship names to include in output
            
        Returns:
            dict: Dictionary representation of the model
        """
        if exclude is None:
            exclude = []
            
        if include is None:
            include = []
            
        result = {}
        
        # Add all columns
        for column in class_mapper(self.__class__).columns:
            if column.key not in exclude:
                value = getattr(self, column.key)
                
                # Handle datetime objects
                if isinstance(value, datetime):
                    value = value.isoformat()
                    
                result[column.key] = value
                
        # Add requested relationships
        for relationship in include:
            if hasattr(self, relationship) and relationship not in exclude:
                related_obj = getattr(self, relationship)
                
                # Handle collections (one-to-many, many-to-many)
                if hasattr(related_obj, '__iter__') and not isinstance(related_obj, str):
                    result[relationship] = [obj.to_dict(exclude=exclude) for obj in related_obj]
                # Handle single objects (many-to-one, one-to-one)
                elif related_obj is not None:
                    result[relationship] = related_obj.to_dict(exclude=exclude)
                else:
                    result[relationship] = None
                    
        return result
        
    def to_json(self, exclude=None, include=None):
        """
        Convert model instance to JSON string.
        
        Args:
            exclude (list): List of field names to exclude from output
            include (list): List of relationship names to include in output
            
        Returns:
            str: JSON string representation of the model
        """
        return json.dumps(self.to_dict(exclude=exclude, include=include))
        
    @classmethod
    def from_dict(cls, data):
        """
        Create a new instance from a dictionary.
        
        Args:
            data (dict): Dictionary with model data
            
        Returns:
            object: New instance of the model
        """
        return cls(**{k: v for k, v in data.items() if k in cls.__table__.columns.keys()})