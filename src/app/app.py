#!/usr/bin/env python3

# import normaldb
from flask import Flask, render_template, request, url_for

# TODO: Create a frontend that allows users to interact with the
#       normaldb package.

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("./index.html")

@app.route("/normalize", methods=["POST"])
def normalize():
    # TODO: Integrate the app with the functionalities of normal-db
    try:
        data = request.get_json(silent=True)
        print(data)
        if data is None:
            return {"error": "No JSON body received."}, 400
        return {"received": data}
    except Exception as error:
        print("Normalization error:", error)
        return {"error": "Failed to parse request."}, 500

if __name__ == "__main__":
    app.run(debug=True)
