from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Welkom!</h1>
    <p>Mijn website werkt!</p>
    <p>Dit is mijn Python Flask website.</p>
    """

if __name__ == "__main__":
    app.run()
