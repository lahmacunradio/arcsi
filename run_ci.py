from arcsi import create_app

app = create_app("../config_ci.py")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
