from src.app import app
from src.ir_service.file_crawler import (
    load_virtual_file_system,
    update_virtual_file_system,
    save_virtual_file_system,
)

if __name__ == "__main__":
    load_virtual_file_system()
    update_virtual_file_system()
    save_virtual_file_system()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=True
    )
