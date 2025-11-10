"""
Module for application  
Provides unified logging settings for all parts of the application
"""

import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """
    Formatter that formats log entries in JSON format.
    Useful for analyzing logs using log analysis tools.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Adding exception information if it exists
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_logger(app=None, log_dir=None, log_level=logging.INFO, enable_json=False):
    """
    Setup logging for the application
    
    Args:
        app: Flask application instance (optional)
        log_dir: Directory for storing log files
        log_level: Logging level
        enable_json: Use JSON formatting for logs
        
    Returns:
        Configured logger instance
    """
    if log_dir is None:
        # If directory is not specified, use logs directory in the root project
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
    
    # Create directory for logs if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger first
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Create logger
    logger = logging.getLogger('app')
    logger.setLevel(log_level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers = []
    
    # Setup formatting
    if enable_json:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s (%(filename)s:%(lineno)d): %(message)s'
        )
    
    # File handler with size rotation
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # File handler with time rotation (daily)
    daily_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'app.daily.log'),
        when='midnight',
        interval=1,
        backupCount=30  # Keep logs for 30 days
    )
    daily_handler.setFormatter(formatter)
    daily_handler.setLevel(log_level)
    
    # Error handler
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10485760,
        backupCount=10
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(daily_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    # Add handlers to root logger as well
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # If Flask application instance is provided, configure its logger
    if app:
        app.logger.handlers = []
        for handler in logger.handlers:
            app.logger.addHandler(handler)
        app.logger.setLevel(log_level)
        
        # Log application start
        app.logger.info('Flask application logging setup completed')
    
    # Configure loggers for important modules
    module_loggers = [
        logging.getLogger('app.services'),
        logging.getLogger('app.routes'),
        logging.getLogger('app.models'),
        logging.getLogger('app.db')
    ]
    
    for module_logger in module_loggers:
        module_logger.setLevel(log_level)
        # Set propagate to True to pass messages to the root logger
        module_logger.propagate = True
    
    # Log a message to verify logging is working
    logger.info('Logging setup completed')
    
    return logger

def log_request_info(app):
    """
    Adds middleware for logging request information
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request():
        from flask import request, g
        import time
        g.start_time = time.time()
        app.logger.debug(f"Received request: {request.method} {request.path}")
        
    @app.after_request
    def after_request(response):
        from flask import request, g
        import time
        
        # Calculate request processing time
        if hasattr(g, 'start_time'):
            elapsed_time = time.time() - g.start_time
            app.logger.debug(f"Request {request.method} {request.path} processed in {elapsed_time:.4f} seconds")
            app.logger.debug(f"Response status code: {response.status_code}")
        
        return response 