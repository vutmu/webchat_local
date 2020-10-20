from app.views import app
from app.dbrout import pgdb

if __name__ == '__main__':
    app.run(debug=True)