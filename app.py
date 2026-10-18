import os, sqlite3, secrets, re
from datetime import datetime
from urllib.parse import urlencode
from flask import Flask, request, redirect, url_for, render_template_string, session, flash, abort

APP_TITLE = "Gopesh & Prachi | Wedding RSVP"
DB_PATH = os.environ.get("RSVP_DB_PATH", "wedding_rsvp.db")
ADMIN_PASSWORD = os.environ.get("RSVP_ADMIN_PASSWORD", "change-this-before-launch")
SECRET_KEY = os.environ.get("RSVP_SECRET_KEY", "change-this-secret-before-launch")
PUBLIC_BASE_URL = os.environ.get("RSVP_PUBLIC_BASE_URL", "http://127.0.0.1:5000")

app = Flask(__name__)
app.secret_key = SECRET_KEY

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            side TEXT NOT NULL DEFAULT 'Not specified',
            invited_by TEXT NOT NULL DEFAULT 'General link',
            dec4 INTEGER NOT NULL DEFAULT 0,
            dec5 INTEGER NOT NULL DEFAULT 0,
            plus_ones INTEGER NOT NULL DEFAULT 0,
            party_vibe TEXT NOT NULL DEFAULT 'solo',
            companions TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS companion_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id INTEGER NOT NULL,
            companion_guest_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'suggested',
            UNIQUE(guest_id, companion_guest_id),
            FOREIGN KEY(guest_id) REFERENCES guests(id) ON DELETE CASCADE,
            FOREIGN KEY(companion_guest_id) REFERENCES guests(id) ON DELETE CASCADE
        );
        """)
init_db()
# Lightweight migration for databases created by an earlier prototype version.
with db() as _c:
    _cols = [r["name"] for r in _c.execute("PRAGMA table_info(guests)").fetchall()]
    if "party_vibe" not in _cols:
        _c.execute("ALTER TABLE guests ADD COLUMN party_vibe TEXT NOT NULL DEFAULT 'solo'")

def normal_phone(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 10:
        digits = "91" + digits
    return digits

def safe_int(value, default=0, low=0, high=5):
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default

def invite_context():
    sender = (request.args.get("from") or "General link").strip()[:80]
    max_people = safe_int(request.args.get("max", 7), 7, 1, 7)
    side = (request.args.get("side") or "Not specified").strip()[:40]
    return sender, max_people, side

PAGE = """
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title><style>
:root{--ink:#302820;--gold:#9a7744;--paper:#fbf8f1;--line:#e5dccd;--muted:#756b60}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
.wrap{max-width:760px;margin:auto;padding:24px 16px 48px}.hero{text-align:center;padding:30px 12px 24px;border-bottom:1px solid var(--line);position:relative;overflow:hidden;background:radial-gradient(ellipse at top, #f3e6cf 0%, #fbf8f1 68%);border-radius:0 0 22px 22px}
.hero:before{content:'✦  ❀  ✦';display:block;color:var(--gold);letter-spacing:.45em;font-size:18px;margin-bottom:8px}
.hero:after{content:'❧';display:block;color:var(--gold);font-size:26px;line-height:1;margin-top:12px}
.eyebrow{letter-spacing:.18em;text-transform:uppercase;font-size:11px;color:var(--gold);font-weight:700}
h1{font-family:Georgia,serif;font-weight:500;font-size:clamp(32px,7vw,52px);line-height:1.08;margin:12px 0}
h2{font-family:Georgia,serif;font-weight:500;margin:0 0 12px;font-size:24px}
.sub{color:var(--muted)}.card{background:#fffdf9;border:1px solid var(--line);border-radius:18px;padding:20px;margin:16px 0;box-shadow:0 5px 20px #49391a08}
.card .card{border-left:3px solid var(--gold);background:linear-gradient(135deg,#fffdf9,#fbf4e8)}
.party-option{transition:background .15s ease,border-color .15s ease}
.party-option:has(input:checked){box-shadow:0 0 0 2px #9a77441a}

label{display:block;font-size:14px;font-weight:650;margin:12px 0 6px}[hidden]{display:none!important}input,select,textarea{width:100%;padding:12px;border:1px solid #d9cfbf;border-radius:10px;background:white;font:inherit;color:var(--ink)}
input[type=checkbox]{width:auto;accent-color:var(--gold);transform:scale(1.15);margin-right:8px}.check{display:flex;align-items:flex-start;gap:4px;font-weight:500;margin:10px 0}.check label{margin:0;font-weight:500}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.party-options{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.party-option{display:flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:12px;padding:13px;background:#fffdf9;cursor:pointer;font-weight:500!important;margin:0!important}
.party-option input{width:auto;accent-color:var(--gold);margin:0;flex-shrink:0}
.party-option:has(input:checked){border-color:var(--gold);background:#f7f0e5}
.btn{display:inline-block;background:var(--ink);color:white;text-decoration:none;border:0;border-radius:999px;padding:13px 22px;font:inherit;font-weight:700;cursor:pointer}.btn.secondary{background:white;color:var(--ink);border:1px solid var(--line)}
.full{width:100%}.small{font-size:13px;color:var(--muted)}.flash{padding:12px;border-radius:10px;background:#f6ead7;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:9px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted)}
.pill{display:inline-block;background:#f0e7d8;padding:3px 8px;border-radius:999px;font-size:12px;margin:2px}
@media(max-width:560px){.grid,.party-options{grid-template-columns:1fr}.card{padding:16px}table{font-size:12px}}
</style></head><body><main class="wrap">
<header class="hero"><div class="eyebrow">With love, we invite you</div><h1>Gopesh &amp; Prachi</h1><p class="sub">Two days of celebration · 4–5 December 2026</p></header>
{% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}<div class="flash">{{m}}</div>{% endfor %}{% endif %}{% endwith %}
{{ body|safe }}
</main></body></html>
"""

@app.route("/", methods=["GET", "POST"])
def rsvp():
    sender, max_people, side = invite_context()
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()[:100]
        raw_phone = re.sub(r"\D", "", request.form.get("phone") or "")
        if not raw_phone:
            flash("Please enter your mobile number using digits only.")
            return redirect(url_for("rsvp", **{"from": sender, "max": max_people, "side": side}))
        phone = normal_phone(raw_phone)
        if not name:
            flash("Please enter your name.")
            return redirect(url_for("rsvp", **{"from": sender, "max": max_people, "side": side}))
        dec4 = int(request.form.get("dec4") == "yes")
        dec5 = int(request.form.get("dec5") == "yes")
        party_vibe = (request.form.get("party_vibe") or "solo").strip()
        if party_vibe not in {"family", "better_half", "potential", "solo"}:
            party_vibe = "solo"
        plus_ones = safe_int(request.form.get("plus_ones"), 0, 0, max(0, max_people-1))
        if party_vibe == "better_half":
            plus_ones = min(1, max(0, max_people-1))
        elif party_vibe in {"solo", "potential"}:
            plus_ones = 0
        companions = (request.form.get("companions") or "").strip()[:400]
        notes = (request.form.get("notes") or "").strip()[:500]
        now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        with db() as c:
            existing = c.execute("SELECT id FROM guests WHERE phone=?", (phone,)).fetchone()
            if existing:
                guest_id = existing["id"]
                c.execute("""UPDATE guests SET name=?,side=?,invited_by=?,dec4=?,dec5=?,plus_ones=?,party_vibe=?,companions=?,notes=?,updated_at=? WHERE id=?""",
                          (name, side, sender, dec4, dec5, plus_ones, party_vibe, companions, notes, now, guest_id))
                flash("Your RSVP has been updated. We matched your mobile number to your existing record.")
            else:
                cur = c.execute("""INSERT INTO guests(name,phone,side,invited_by,dec4,dec5,plus_ones,party_vibe,companions,notes,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (name, phone, side, sender, dec4, dec5, plus_ones, party_vibe, companions, notes, now, now))
                guest_id = cur.lastrowid
                flash("Thank you! Your RSVP has been saved.")
            # Create suggested links to possible matching guests, but never merge automatically.
            tokens = [x.strip() for x in re.split(r"[,;\n]+", companions) if len(x.strip()) >= 3]
            c.execute("DELETE FROM companion_links WHERE guest_id=? OR companion_guest_id=?", (guest_id, guest_id))
            for token in tokens:
                matches = c.execute("""SELECT id FROM guests WHERE id<>? AND lower(name)=lower(?) LIMIT 5""", (guest_id, token)).fetchall()
                for match in matches:
                    try:
                        c.execute("INSERT OR IGNORE INTO companion_links(guest_id,companion_guest_id,status) VALUES(?,?,'suggested')", (guest_id, match["id"]))
                    except sqlite3.IntegrityError:
                        pass
        return redirect(url_for("thanks"))
    body = f"""
    <section class="card"><h2>You're invited</h2><p class="sub">Please let us know which celebrations you can join.</p>
    <form method="post">
    <label for="name">Your full name *</label><input id="name" name="name" required autocomplete="name" placeholder="Enter your name">
    <label for="phone">Mobile number *</label><input id="phone" name="phone" type="tel" inputmode="numeric" pattern="[0-9]+" autocomplete="tel" required oninput="this.value=this.value.replace(/[^0-9]/g,'')" placeholder="Digits only (include country code if needed)">
    <p class="small">Used only to identify your RSVP and prevent duplicate entries. The website cannot read your WhatsApp number automatically.</p>
    <div class="card"><h2>4 December · Shagun, Engagement &amp; Sangeet</h2><div class="check"><label><input type="checkbox" name="dec4" value="yes"> I/we will attend</label></div></div>
    <div class="card"><h2>5 December · Wedding</h2><div class="check"><label><input type="checkbox" name="dec5" value="yes"> I/we will attend</label></div></div>
    <label>What's your wedding squad situation? 😄</label>
    <div class="party-options">
      <label class="party-option"><input type="radio" name="party_vibe" value="family" onchange="partyChanged()" required> 👨‍👩‍👧‍👦 Rolling in with family</label>
      <label class="party-option"><input type="radio" name="party_vibe" value="better_half" onchange="partyChanged()"> 💑 Bringing my better half</label>
      <label class="party-option"><input type="radio" name="party_vibe" value="potential" onchange="partyChanged()"> 😉 Coming solo… open to a plot twist</label>
      <label class="party-option"><input type="radio" name="party_vibe" value="solo" onchange="partyChanged()"> 🕺 Flying solo, just here to celebrate</label>
    </div>
    <div id="guest-count-wrap" hidden>
      <label for="plus_ones" id="guest-count-label">How many family members are joining you?</label>
      <select id="plus_ones" name="plus_ones">{''.join(f'<option value="{i}">{i}</option>' for i in range(max(0, max_people-1)+1))}</select>
      <div id="companions-wrap"><label for="companions" id="companions-label">Names (optional)</label><input id="companions" name="companions" placeholder="e.g. family members"></div>
    </div>
    <script>
    function partyChanged() {{
      const selected = document.querySelector('input[name="party_vibe"]:checked');
      const wrap = document.getElementById('guest-count-wrap');
      const count = document.getElementById('plus_ones');
      const label = document.getElementById('guest-count-label');
      const companionsWrap = document.getElementById('companions-wrap');
      const companionsLabel = document.getElementById('companions-label');
      const companions = document.getElementById('companions');
      if (!selected) return;
      const v = selected.value;
      if (v === 'family') {{
        wrap.hidden = false;
        label.textContent = 'How many family members are joining you?';
        label.hidden = false;
        count.hidden = false;
        count.required = true;
        count.value = '0';
        companionsWrap.hidden = false;
        companionsLabel.textContent = 'Names (optional)';
        companions.placeholder = 'e.g. family members';
      }} else if (v === 'better_half') {{
        wrap.hidden = false;
        label.hidden = true;
        count.hidden = true;
        count.required = false;
        count.value = '1';
        companionsWrap.hidden = false;
        companionsLabel.textContent = 'Their name (optional)';
        companions.placeholder = 'Your better half’s name';
      }} else {{
        wrap.hidden = true;
        label.hidden = false;
        count.hidden = false;
        count.required = false;
        count.value = '0';
        companions.value = '';
      }}
    }}
    </script>
    <label for="notes">Anything we should know? (optional)</label><textarea id="notes" name="notes" rows="2" placeholder="Dietary or other notes"></textarea>
    <button class="btn full" type="submit">Confirm my RSVP</button></form></section>
    <p class="small">Invitation shared by: {sender.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')} · For any changes, submit again using the same mobile number.</p>
    """
    return render_template_string(PAGE, title=APP_TITLE, body=body)

@app.route("/thanks")
def thanks():
    body = """<section class="card" style="text-align:center;padding:36px 20px"><div class="eyebrow">RSVP received</div><h1 style="font-size:38px">Thank you!</h1><p class="sub">Your response has been saved. We look forward to celebrating together.</p><p>4–5 December 2026</p></section>"""
    return render_template_string(PAGE, title="Thank you | Wedding RSVP", body=body)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST" and request.form.get("action") == "login":
        if secrets.compare_digest(request.form.get("password",""), ADMIN_PASSWORD):
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Incorrect password.")
    if not session.get("admin"):
        body = """<section class="card"><h2>Private admin dashboard</h2><form method="post"><input type="hidden" name="action" value="login"><label>Admin password</label><input type="password" name="password" required><button class="btn full" style="margin-top:14px">Sign in</button></form><p class="small">Set RSVP_ADMIN_PASSWORD before deployment.</p></section>"""
        return render_template_string(PAGE, title="Admin login", body=body)
    with db() as c:
        guests = c.execute("SELECT * FROM guests ORDER BY updated_at DESC").fetchall()
        totals = c.execute("""SELECT COUNT(*) guests, SUM(dec4) d4, SUM(dec5) d5,
          SUM(CASE WHEN dec4=1 THEN 1+plus_ones ELSE 0 END) d4_people,
          SUM(CASE WHEN dec5=1 THEN 1+plus_ones ELSE 0 END) d5_people FROM guests""").fetchone()
        suggestions = c.execute("""SELECT g.name a, h.name b, l.status FROM companion_links l
          JOIN guests g ON g.id=l.guest_id JOIN guests h ON h.id=l.companion_guest_id
          ORDER BY g.name""").fetchall()
    rows = ""
    for g in guests:
        rows += "<tr><td>"+str(g["name"]).replace("<","&lt;")+"</td><td>"+str(g["phone"])+"</td><td>"+str(g["side"])+"</td><td>"+str(g["invited_by"]).replace("<","&lt;")+"</td><td>"+("Yes" if g["dec4"] else "No")+"</td><td>"+("Yes" if g["dec5"] else "No")+"</td><td>"+str(1+g["plus_ones"])+"</td><td>"+str(g["companions"]).replace("<","&lt;")+"</td></tr>"
    sugg = "".join(f"<li>{s['a']} ↔ {s['b']} <span class='pill'>suggested match — review manually</span></li>" for s in suggestions) or "<li>No suggested matches yet.</li>"
    body = f"""
    <section class="card"><div class="eyebrow">Private control centre</div><h2>RSVP dashboard</h2>
    <div class="grid"><div class="card"><div class="small">Unique guest records</div><h2>{totals['guests'] or 0}</h2></div>
    <div class="card"><div class="small">Dec 4 confirmed people*</div><h2>{totals['d4_people'] or 0}</h2></div>
    <div class="card"><div class="small">Dec 5 confirmed people*</div><h2>{totals['d5_people'] or 0}</h2></div>
    <div class="card"><div class="small">Records attending each date</div><h2>{totals['d4'] or 0} / {totals['d5'] or 0}</h2><div class="small">Dec 4 / Dec 5</div></div></div>
    <p class="small">*Counts include declared additional guests. Companion overlaps are not automatically deducted; review suggested matches to avoid double-counting.</p>
    <p><a class="btn secondary" href="/admin/export.csv">Export CSV</a> <a class="btn secondary" href="/admin/links">Create share link</a> <a class="btn secondary" href="/admin/logout">Sign out</a></p></section>
    <section class="card"><h2>Guest responses</h2><div style="overflow:auto"><table><thead><tr><th>Name</th><th>Mobile</th><th>Side</th><th>Invited by</th><th>Dec 4</th><th>Dec 5</th><th>Total people</th><th>Companions entered</th></tr></thead><tbody>{rows or '<tr><td colspan="8">No responses yet.</td></tr>'}</tbody></table></div></section>
    <section class="card"><h2>Potential friend matches</h2><p class="small">These are suggestions only. Confirm identities with the guests before treating them as one person.</p><ul>{sugg}</ul></section>
    """
    return render_template_string(PAGE, title="Admin dashboard", body=body)

@app.route("/admin/links", methods=["GET", "POST"])
def links():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    url = None
    if request.method == "POST":
        sender = (request.form.get("sender") or "Family").strip()[:80]
        side = (request.form.get("side") or "Not specified").strip()[:40]
        max_people = safe_int(request.form.get("max_people"), 2, 1, 7)
        url = PUBLIC_BASE_URL.rstrip("/") + "/?" + urlencode({"from": sender, "side": side, "max": max_people})
    link_html = ("<div class=\"flash\"><b>Copy this link into WhatsApp:</b><br><textarea rows=\"3\" readonly onclick=\"this.select()\">" + url + "</textarea></div>") if url else ""
    body = f"""<section class="card"><h2>Create a shareable RSVP link</h2><p class="sub">No guest names need to be entered first. Create a link for each person sending invitations.</p>
    <form method="post"><label>Sender label</label><input name="sender" required placeholder="e.g. Gopesh, Prachi, Chacha Ji">
    <label>Family side</label><select name="side"><option>Groom's side</option><option>Bride's side</option><option>Both families</option><option>Not specified</option></select>
    <label>Maximum people including invitee (family invitations)</label><select name="max_people">{''.join(f'<option value="{i}" {"selected" if i==2 else ""}>{i} total people</option>' for i in range(1,8))}</select>
    <button class="btn full" style="margin-top:16px">Generate link</button></form>
    {link_html}
    <p class="small">This is a sender-tagged share link, not a one-person invitation token. Anyone who receives it can forward it. Use a separate link with the appropriate guest limit for each audience.</p><p><a href="/admin">← Back to dashboard</a></p></section>"""
    return render_template_string(PAGE, title="Create RSVP link", body=body)

@app.route("/admin/export.csv")
def export_csv():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    import csv, io
    with db() as c:
        rows = c.execute("SELECT name,phone,side,invited_by,dec4,dec5,plus_ones,party_vibe,companions,notes,created_at,updated_at FROM guests ORDER BY name").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name","Mobile","Side","Invited by","Dec 4 attending","Dec 5 attending","Additional guests","Party vibe","Companions","Notes","Created at","Updated at"])
    for r in rows:
        writer.writerow([r["name"],r["phone"],r["side"],r["invited_by"],r["dec4"],r["dec5"],r["plus_ones"],r["party_vibe"],r["companions"],r["notes"],r["created_at"],r["updated_at"]])
    from flask import Response
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=wedding_rsvps.csv"})

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    if ADMIN_PASSWORD == "change-this-before-launch" or SECRET_KEY == "change-this-secret-before-launch":
        print("WARNING: Set RSVP_ADMIN_PASSWORD and RSVP_SECRET_KEY before exposing this app to the internet.")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
