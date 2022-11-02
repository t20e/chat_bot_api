from datetime import datetime
from __init__ import app

# this allows routes to use app.route
import routes

if __name__ == '__main__':
    app.run(port=8080, debug=True)
