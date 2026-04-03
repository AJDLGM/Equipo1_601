from db.database import create_tables
from ui.login_window import start_app
from config.paths import create_directories

if __name__ == "__main__":

    create_directories()
    create_tables()

    start_app()