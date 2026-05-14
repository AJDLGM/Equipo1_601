from server.app import app, create_directories, create_tables

create_directories()
create_tables()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
