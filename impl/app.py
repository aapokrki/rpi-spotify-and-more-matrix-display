from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)
_selected_mode = "clock"

@app.route('/')
def index():
    return render_template("index.html", current_mode=_selected_mode)

@app.route('/set/<mode>', methods=['POST'])
def set_mode(mode):
    global _selected_mode
    if mode in ["spotify", "clock"]:
        _selected_mode = mode
    return redirect(url_for("index"))

def run_flask():
    app.run(host="0.0.0.0", port=5000)

def get_selected_mode():
    return _selected_mode
