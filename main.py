from flask import Flask
import requests


app = Flask(__name__)

@app.route('/')
def main():
    pass


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')