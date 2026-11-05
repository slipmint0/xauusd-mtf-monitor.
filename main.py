from api.monitor import handler

def app(environ, start_response):
    """Failsafe WSGI wrapper acting as Vercel's required top-level application root entrypoint."""
    # Instantly processes your factual price calculations handler routine
    result = handler(None)
    
    status = '200 OK'
    response_headers = [('Content-Type', 'application/json')]
    start_response(status, response_headers)
    
    # Returns the JSON status report text mapping cleanly to the web terminal window
    import json
    return [json.dumps(result).encode('utf-8')]
