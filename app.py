from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_babel import Babel, _
import json, os, re, datetime
import spacy

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "supersecret")
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
babel = Babel(app)
LANGUAGES = ['en', 'es', 'fr']
nlp = spacy.load("en_core_web_sm")

@babel.localeselector
def get_locale():
    return request.args.get('lang') or 'en'

def require_tier(min_tier):
    def decorator(f):
        def wrapped(*args, **kwargs):
            if session.get("tier", 0) < min_tier:
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

@app.route("/")
@require_tier(1)
def dashboard():
    return render_template("dashboard.html")

@app.route("/submit", methods=["POST"])
@require_tier(1)
def submit():
    text = request.form.get("text", "")
    doc = nlp(text)
    entities = [{"text": e.text, "label": e.label_} for e in doc.ents]
    pii = re.findall(r"[\w\.-]+@[\w\.-]+", text)
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "text": text,
        "ner": entities,
        "pii": pii,
        "user": session.get("user")
    }
    with open("logs/sessions.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
    return render_template("dashboard.html", result=entry)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form['username'], request.form['password']
        users = json.load(open("users.json"))
        if u in users and users[u]['password'] == p:
            session["user"] = u
            session["tier"] = users[u]['tier']
            return redirect("/")
    return render_template("login.html")

@app.route("/graph")
@require_tier(1)
def graph():
    return render_template("graph.html")

@app.route("/graph.json")
@require_tier(1)
def graph_data():
    nodes, edges = {}, []
    with open("logs/sessions.jsonl") as f:
        for line in f:
            entry = json.loads(line)
            t = entry["timestamp"]
            if t not in nodes:
                nodes[t] = {"id": t, "label": t, "group": "time"}
            for ent in entry["ner"]:
                key = ent["text"]
                if key not in nodes:
                    nodes[key] = {"id": key, "label": key, "group": ent["label"]}
                edges.append({"from": t, "to": key})
    return jsonify({"nodes": list(nodes.values()), "edges": edges})

@app.route("/admin")
@require_tier(2)
def admin():
    users = json.load(open("users.json"))
    logs = open("logs/sessions.jsonl").readlines()[-20:]
    logs = [json.loads(l) for l in logs]
    return render_template("admin.html", users=users, logs=logs)

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)