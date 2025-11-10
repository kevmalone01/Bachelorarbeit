from flask_sqlalchemy import SQLAlchemy

# Create the db instance
db = SQLAlchemy()

def init_db():
    """Initialize the database by creating all tables."""
    db.create_all()
    
def reset_db():
    """Reset the database by dropping and recreating all tables."""
    db.drop_all()
    db.create_all() 