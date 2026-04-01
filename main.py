from db.database import create_tables
from ui.login_window import start_app

if __name__ == "__main__":
    create_tables()
    start_app()
    