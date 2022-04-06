from arcsi import create_app

app = create_app("../config_ci.py")


if __name__ == "__main__":
    app.run(host="localhost", port=5000,)
