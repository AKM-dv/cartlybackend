import mysql.connector
from flask import current_app, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

db = SQLAlchemy()

class DatabaseManager:
    """Manages multi-tenant database connections."""
    
    def __init__(self):
        self.engines = {}
        self.sessions = {}
    
    def get_admin_connection(self):
        """Get connection to main admin database."""
        config = {
            'host': current_app.config['MYSQL_HOST'],
            'port': current_app.config['MYSQL_PORT'],
            'user': current_app.config['MYSQL_USER'],
            'password': current_app.config['MYSQL_PASSWORD'],
            'database': current_app.config['MYSQL_DATABASE'],
            'autocommit': True
        }
        
        try:
            connection = mysql.connector.connect(**config)
            return connection
        except mysql.connector.Error as err:
            logging.error(f"Admin database connection error: {err}")
            raise
    
    def get_store_database_uri(self, store_id):
        """Generate database URI for specific store."""
        db_name = f"{current_app.config['TENANT_DATABASE_PREFIX']}{store_id}"
        
        return (f"mysql+pymysql://{current_app.config['MYSQL_USER']}:"
                f"{current_app.config['MYSQL_PASSWORD']}@"
                f"{current_app.config['MYSQL_HOST']}:"
                f"{current_app.config['MYSQL_PORT']}/{db_name}")
    
    def create_store_database(self, store_id):
        """Create database for new store."""
        db_name = f"{current_app.config['TENANT_DATABASE_PREFIX']}{store_id}"
        
        try:
            connection = self.get_admin_connection()
            cursor = connection.cursor()
            
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            cursor.close()
            connection.close()
            
            logging.info(f"Database created for store: {store_id}")
            return True
            
        except mysql.connector.Error as err:
            logging.error(f"Error creating store database: {err}")
            return False
    
    def get_store_engine(self, store_id):
        """Get SQLAlchemy engine for specific store."""
        if store_id not in self.engines:
            uri = self.get_store_database_uri(store_id)
            self.engines[store_id] = create_engine(
                uri,
                pool_size=5,
                pool_recycle=3600,
                pool_pre_ping=True
            )
        
        return self.engines[store_id]
    
    def get_store_session(self, store_id):
        """Get database session for specific store."""
        if store_id not in self.sessions:
            engine = self.get_store_engine(store_id)
            Session = sessionmaker(bind=engine)
            self.sessions[store_id] = Session()
        
        return self.sessions[store_id]
    
    def close_store_session(self, store_id):
        """Close database session for specific store."""
        if store_id in self.sessions:
            self.sessions[store_id].close()
            del self.sessions[store_id]
    
    def delete_store_database(self, store_id):
        """Delete database for store (use with caution)."""
        db_name = f"{current_app.config['TENANT_DATABASE_PREFIX']}{store_id}"
        
        try:
            connection = self.get_admin_connection()
            cursor = connection.cursor()
            
            cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
            
            cursor.close()
            connection.close()
            
            # Clean up cached connections
            if store_id in self.engines:
                del self.engines[store_id]
            if store_id in self.sessions:
                del self.sessions[store_id]
            
            logging.info(f"Database deleted for store: {store_id}")
            return True
            
        except mysql.connector.Error as err:
            logging.error(f"Error deleting store database: {err}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    
    with app.app_context():
        # Create admin database tables
        db.create_all()

def get_db():
    """Get current database session."""
    return db.session

def get_store_db(store_id):
    """Get database session for specific store."""
    return db_manager.get_store_session(store_id)