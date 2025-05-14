from arcsi import create_app

app = create_app("../config.py")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5666,
    )
