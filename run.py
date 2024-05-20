from src.server import app
from src.db import ensure_initialization
if __name__ == '__main__':
    ensure_initialization()
    app.run(debug=True)
