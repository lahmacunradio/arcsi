from arcsi import create_app
import os

app = create_app("../" + os.getenv("CONFIG_PATH"))


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5666,
    )
