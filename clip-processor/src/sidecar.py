"""Entry point HTTP do clip-processor, sem scheduler de pipeline."""

from src.internal_api import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8090, use_reloader=False, debug=False)
