"""
web_app.py
~~~~~~~~~~
Main entrypoint for Capybala's developer web dashboard.
Delegates to the modular web.app package.
Run with: python web_app.py
"""

import uvicorn
from web.app import app

if __name__ == "__main__":
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=False)
