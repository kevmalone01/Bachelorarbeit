# Logging in the application

In the application, a logging system is implemented to track the operation of all components and diagnose problems.

## Logging Levels

The system uses standard Python logging levels:

- **DEBUG**: Detailed information for debugging problems.
- **INFO**: Confirmation that everything is working as expected.
- **WARNING**: Indication of something unexpected or a potential problem in the future.
- **ERROR**: Due to a more serious problem, the function cannot complete its task.
- **CRITICAL**: A serious error indicating that the program cannot continue.

## Logging Storage

Logs are stored in the `logs` directory in the root of the project. The system creates several log files:

- **app.log**: The main log file with rotation by size (10MB).
- **app.daily.log**: Daily logs with rotation at midnight.
- **error.log**: A separate file for logging errors (level ERROR and above).

## Log Format

By default, the text log format is used:

```
[TIMESTAMP] LEVEL in MODULE (FILENAME:LINE): MESSAGE
```

JSON format is also supported for more convenient analysis of logs with tools:

```json
{
  "timestamp": "2023-01-01T12:00:00.000000",
  "level": "INFO",
  "module": "document_service",
  "function": "save_document",
  "line": 42,
  "message": "Document saved successfully"
}
```

## Logging HTTP requests

The system automatically logs the following information about HTTP requests:

- Method and request path
- Request headers
- Execution time of the request
- Response status

## Logging Configuration

Logging settings are defined in the `app.config.logging_config` module and applied when starting the application in `main.py`.

## Example of using logging in code

```python
import logging

# Getting the logger
logger = logging.getLogger(__name__)

def some_function():
    logger.debug("Detailed information")
    logger.info("The function started execution")
    
    try:
        # Code of the function
        result = do_something()
        logger.info("The function was executed successfully")
        return result
    except Exception as e:
        logger.error("Error in the function: %s", str(e), exc_info=True)
        raise
```

## Monitoring logs

To view logs in real time, you can use the command:

```bash
tail -f logs/app.log
```

To search for errors:

```bash
grep ERROR logs/app.log
```

## Logging level configuration

The logging level is configured depending on the application mode:
- In the debug mode (`debug=True`): DEBUG
- In the production mode: INFO 