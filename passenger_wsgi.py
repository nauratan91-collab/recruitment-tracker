import sys
import os

# Set working directory to project root
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

try:
    os.chdir(app_dir)
except Exception:
    pass

# Load environment variables from .env file
env_path = os.path.join(app_dir, '.env')
if os.path.exists(env_path):
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip("'").strip('"')
                    if key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass

# Import Flask app as 'application' (Passenger / WSGI standard)
try:
    from app import app as application
except Exception as e:
    import traceback
    error_msg = traceback.format_exc()
    try:
        with open(os.path.join(app_dir, 'passenger_error.log'), 'a', encoding='utf-8') as ef:
            ef.write(f"\n--- Startup Error: {e} ---\n{error_msg}\n")
    except Exception:
        pass

    def application(environ, start_response):
        status = '500 Internal Server Error'
        output = (
            f"<html><head><title>Startup Error - Key Dynamics</title></head><body>"
            f"<h2 style='color:#c00;'>GoDaddy Python Startup Error</h2>"
            f"<p>An error occurred while loading the application. Check <code>passenger_error.log</code> or verify dependencies in cPanel.</p>"
            f"<pre style='background:#f4f4f4;padding:15px;border:1px solid #ddd;border-radius:6px;overflow-x:auto;'>{error_msg}</pre>"
            f"</body></html>"
        ).encode('utf-8')
        response_headers = [
            ('Content-type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(output)))
        ]
        start_response(status, response_headers)
        return [output]
