from flask import Flask, request, redirect, url_for, render_template_string, session, jsonify
import sqlite3
import requests
import math
import os
import secrets
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("DISASTER_X_SECRET", secrets.token_hex(32))
DATABASE = "disaster_x.db"

ADMIN_USERNAME = os.environ.get("DISASTER_X_ADMIN", "admin")
ADMIN_PASSWORD = os.environ.get("DISASTER_X_PASSWORD", "disasterx123")

IMD_URL = "https://mausam.imd.gov.in/"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

EMERGENCY_SERVICES = [
    ("Integrated Emergency", "112"),
    ("Police", "100"),
    ("Fire & Rescue", "101"),
    ("Ambulance", "102"),
    ("Ambulance / Medical", "108"),
    ("Disaster Management", "1070"),
    ("Child Helpline", "1098"),
    ("Cyber Crime", "1930"),
    ("Road Accident", "1073"),
]

CSS = r"""
:root{
  --bg:#07111f;--panel:#0d1b2d;--panel2:#11243a;--line:#20344d;
  --text:#eef6ff;--muted:#9db0c6;--red:#ef4444;--orange:#f59e0b;
  --green:#22c55e;--blue:#38bdf8;--purple:#a78bfa;--shadow:0 18px 50px rgba(0,0,0,.28)
}
*{box-sizing:border-box}
html, body{height:100%}
body{margin:0;background:radial-gradient(circle at 10% 0%,#132a44 0,#07111f 38%,#050b14 100%);
color:var(--text);font-family:Inter,Segoe UI,Arial,sans-serif;min-height:100vh}
a{color:inherit;text-decoration:none}
nav{position:sticky;top:0;z-index:1000;background:rgba(5,11,20,.88);backdrop-filter:blur(14px);
border-bottom:1px solid var(--line);padding:14px 24px;display:flex;align-items:center;justify-content:space-between}
.logo{font-size:24px;font-weight:900;letter-spacing:.5px}.logo span{color:var(--red)}
.navlinks{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.navlinks a{padding:9px 12px;border-radius:9px;color:var(--muted)}
.navlinks a:hover{background:var(--panel2);color:#fff}
.container{max-width:1250px;margin:auto;padding:28px 20px}
.hero{padding:70px 10px 40px;text-align:center}.hero h1{font-size:clamp(42px,7vw,78px);margin:0}
.hero h1 span{color:var(--red)}.hero p{max-width:760px;margin:18px auto;color:var(--muted);font-size:18px;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px}
.card{background:linear-gradient(145deg,rgba(17,36,58,.96),rgba(8,20,34,.96));border:1px solid var(--line);
border-radius:18px;padding:20px;box-shadow:var(--shadow)}
.card h3{margin:0 0 9px}.big{font-size:35px;font-weight:900}.muted{color:var(--muted)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:0;border-radius:11px;
padding:12px 17px;background:var(--red);color:white;font-weight:800;cursor:pointer;transition:.18s}
.btn:hover{transform:translateY(-1px);filter:brightness(1.08)}.btn.blue{background:#2563eb}.btn.green{background:#16a34a}
.btn.dark{background:#20344d}.btn.orange{background:#d97706}.btn.small{padding:8px 11px;font-size:13px}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
.form{max-width:900px;margin:auto;background:rgba(13,27,45,.97);border:1px solid var(--line);border-radius:20px;padding:26px;box-shadow:var(--shadow)}
label{display:block;margin:16px 0 7px;font-weight:700}input,select,textarea{width:100%;padding:12px 13px;border-radius:10px;
border:1px solid #2a405a;background:#071523;color:#fff;outline:none}input:focus,select:focus,textarea:focus{border-color:var(--blue)}
textarea{min-height:130px;resize:vertical}.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.four{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.alert{padding:13px 15px;border-radius:11px;background:#45161b;border:1px solid #7f1d1d;margin:12px 0}.success{background:#0c3322;border-color:#166534}
.info{padding:13px 15px;border-radius:11px;background:#0b2940;border:1px solid #155e75;margin:12px 0}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:14px;overflow:hidden}
th,td{padding:12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:#9edcff}
.tablewrap{overflow:auto}.badge{display:inline-block;padding:5px 9px;border-radius:999px;font-size:12px;font-weight:900}
.pending{background:#3a2b09;color:#fbbf24}.verified{background:#093a23;color:#4ade80}.rejected{background:#42151b;color:#f87171}
.deleted{background:#30343b;color:#cbd5e1}.low{color:#4ade80}.medium{color:#facc15}.high{color:#fb923c}.critical{color:#f87171}
#map{width:100%;height:600px;min-height:600px;border-radius:18px;border:1px solid var(--line);overflow:hidden}
.mapsmall{width:100%;height:320px;min-height:320px}
.map-shell{width:100%;height:600px;position:relative}
.map-shell #map{height:100%}
.service{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:14px;border:1px solid var(--line);
border-radius:13px;background:#0a1828;margin-bottom:9px;cursor:pointer}.service:hover{border-color:#4b6b8d}
.service .title{font-weight:850}.distance{color:var(--blue);font-weight:800}.danger{color:#ff7b7b}.successText{color:#4ade80}
.alertcard{border-left:5px solid var(--orange)}.alertcard.critical{border-left-color:var(--red)}.alertcard.high{border-left-color:var(--orange)}
.kicker{color:#67e8f9;font-weight:900;text-transform:uppercase;font-size:12px;letter-spacing:1.4px}
footer{text-align:center;padding:35px;color:#61758d}.hidden{display:none}.center{text-align:center}
@media(max-width:800px){nav{align-items:flex-start;gap:10px;flex-direction:column}.navlinks{justify-content:flex-start}.two,.three,.four{grid-template-columns:1fr}}
"""

BASE = r"""
<!doctype html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title or "Disaster X" }}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>{{ css }}</style>
</head><body>
<nav><a class="logo" href="/">DISASTER <span>X</span></a>
<div class="navlinks">
<a href="/">Home</a><a href="/alerts">Alerts</a><a href="/report">Report</a>
<a href="/map">Map</a><a href="/emergency">Emergency</a><a href="/emergency-mode">Emergency Mode</a>
{% if session.get("admin") %}<a href="/admin/reports">Admin Reports</a><a href="/admin/logout">Logout</a>{% else %}<a href="/admin/login">Admin</a>{% endif %}
</div></nav>
{{ body|safe }}
<footer>Disaster X • Community reporting • Verified alerts • Emergency assistance</footer>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</body></html>
"""

def page(body, title="Disaster X"):
    return render_template_string(BASE, body=body, title=title, css=CSS)

def db():
    c = sqlite3.connect(DATABASE)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = db()
    c.execute("""
    CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT NOT NULL,
        pin_code TEXT,
        latitude REAL,
        longitude REAL,
        disaster_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        description TEXT,
        people_affected INTEGER DEFAULT 0,
        people_needing_help INTEGER DEFAULT 0,
        injured INTEGER DEFAULT 0,
        missing INTEGER DEFAULT 0,
        displaced INTEGER DEFAULT 0,
        workforce TEXT,
        supplies TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TEXT NOT NULL,
        verified_at TEXT,
        rejected_at TEXT
    )""")
    c.commit()
    c.close()

def admin_required(fn):
    @wraps(fn)
    def wrap(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return fn(*a, **kw)
    return wrap

def geocode(q):
    try:
        r = requests.get(
            NOMINATIM_URL,
            params={"q": q + ", India", "format": "json", "addressdetails": 1, "limit": 1},
            headers={"User-Agent": "DisasterX/1.0"},
            timeout=10
        )
        data = r.json()
        if not data:
            return None
        x = data[0]
        addr = x.get("address", {})
        return {
            "lat": float(x["lat"]),
            "lon": float(x["lon"]),
            "pin": addr.get("postcode", ""),
            "display": x.get("display_name", q)
        }
    except Exception:
        return None

def distance_km(a, b, c, d):
    R = 6371
    p1, p2 = math.radians(a), math.radians(c)
    dp = math.radians(c - a)
    dl = math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))

def route(a, b, c, d):
    try:
        url = f"{OSRM_URL}/{b},{a};{d},{c}"
        r = requests.get(url, params={"overview": "full", "geometries": "geojson", "steps": "true"}, timeout=12)
        j = r.json()
        if j.get("code") != "Ok" or not j.get("routes"):
            return None
        rt = j["routes"][0]
        return {
            "distance": rt["distance"] / 1000,
            "duration": rt["duration"] / 60,
            "geometry": rt["geometry"],
            "steps": rt.get("legs", [{}])[0].get("steps", [])
        }
    except Exception:
        return None

def overpass_services(lat, lon):
    """
    Find nearby hospitals, police stations and fire stations.

    Uses multiple Overpass servers because one server can sometimes
    be unavailable, rate-limited, or slow from cloud hosting such as Render.
    Falls back to Nominatim if Overpass cannot return results.
    """

    overpass_servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter"
    ]

    query = f"""
    [out:json][timeout:20];
    (
      nwr["amenity"="hospital"](around:15000,{lat},{lon});
      nwr["amenity"="clinic"](around:15000,{lat},{lon});
      nwr["amenity"="police"](around:15000,{lat},{lon});
      nwr["amenity"="fire_station"](around:15000,{lat},{lon});
    );
    out center tags;
    """

    headers = {
        "User-Agent": "DisasterX/1.0 (emergency management application)"
    }

    # ---------------------------------------------------------
    # TRY OVERPASS SERVERS
    # ---------------------------------------------------------

    for server in overpass_servers:

        try:

            response = requests.post(
                server,
                data=query,
                headers=headers,
                timeout=25
            )

            response.raise_for_status()

            data = response.json()

            services = []

            for element in data.get("elements", []):

                tags = element.get("tags", {})

                # Nodes have lat/lon directly.
                # Ways/relations have coordinates in "center".
                if "lat" in element and "lon" in element:

                    service_lat = element["lat"]
                    service_lon = element["lon"]

                elif "center" in element:

                    service_lat = element["center"].get("lat")
                    service_lon = element["center"].get("lon")

                else:
                    continue

                if service_lat is None or service_lon is None:
                    continue

                amenity = tags.get("amenity", "service")

                if amenity == "hospital":
                    service_type = "Hospital"

                elif amenity == "clinic":
                    service_type = "Medical Clinic"

                elif amenity == "police":
                    service_type = "Police Station"

                elif amenity == "fire_station":
                    service_type = "Fire Station"

                else:
                    service_type = "Emergency Service"

                name = (
                    tags.get("name")
                    or tags.get("official_name")
                    or service_type
                )

                distance = distance_km(
                    lat,
                    lon,
                    float(service_lat),
                    float(service_lon)
                )

                services.append({
                    "name": name,
                    "type": service_type,
                    "lat": float(service_lat),
                    "lon": float(service_lon),
                    "distance": float(distance)
                })

            services.sort(key=lambda x: x["distance"])

            # If this server successfully returned services,
            # use the results.
            if services:

                print(
                    f"[Disaster X] Found {len(services)} nearby services "
                    f"using {server}"
                )

                return services[:50]

            # Empty result is still a valid Overpass response.
            # Try the next server before falling back.
            print(
                f"[Disaster X] Overpass returned no services: {server}"
            )

        except Exception as e:

            print(
                f"[Disaster X] Overpass failed: {server} -> {e}"
            )

    # ---------------------------------------------------------
    # NOMINATIM FALLBACK
    # ---------------------------------------------------------

    print("[Disaster X] Using Nominatim fallback.")

    services = []

    searches = [
        ("hospital", "Hospital"),
        ("clinic", "Medical Clinic"),
        ("police station", "Police Station"),
        ("fire station", "Fire Station")
    ]

    for search_term, service_type in searches:

        try:

            response = requests.get(
                NOMINATIM_URL,
                params={
                    "q": f"{search_term} near {lat},{lon}",
                    "format": "json",
                    "limit": 10,
                    "addressdetails": 1
                },
                headers=headers,
                timeout=15
            )

            response.raise_for_status()

            results = response.json()

            for result in results:

                try:

                    service_lat = float(result["lat"])
                    service_lon = float(result["lon"])

                except Exception:
                    continue

                distance = distance_km(
                    lat,
                    lon,
                    service_lat,
                    service_lon
                )

                services.append({
                    "name": result.get("display_name", service_type)
                    .split(",")[0],

                    "type": service_type,

                    "lat": service_lat,

                    "lon": service_lon,

                    "distance": float(distance)
                })

        except Exception as e:

            print(
                f"[Disaster X] Nominatim fallback failed "
                f"for {service_type}: {e}"
            )

    services.sort(key=lambda x: x["distance"])

    print(
        f"[Disaster X] Nominatim found {len(services)} services"
    )

    return services[:50]
def weather_alerts(lat, lon, place):
    try:
        p = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,precipitation,rain",
            "hourly": "precipitation_probability,precipitation,wind_speed_10m,weather_code",
            "forecast_days": 3,
            "timezone": "auto"
        }
        j = requests.get(OPEN_METEO_URL, params=p, timeout=10).json()
        cur = j.get("current", {})
        wind = float(cur.get("wind_speed_10m") or 0)
        rain = float(cur.get("rain") or 0)
        temp = float(cur.get("temperature_2m") or 0)
        alerts = []
        if wind >= 60:
            alerts.append(("High Wind", "High", f"Wind around {wind:.0f} km/h", 15000))
        elif wind >= 40:
            alerts.append(("Strong Wind", "Medium", f"Wind around {wind:.0f} km/h", 12000))
        if rain >= 15:
            alerts.append(("Heavy Rain", "High", f"Current rain around {rain:.1f} mm", 12000))
        elif rain >= 5:
            alerts.append(("Rain Advisory", "Medium", f"Current rain around {rain:.1f} mm", 10000))
        if temp >= 45:
            alerts.append(("Extreme Heat", "Critical", f"Temperature around {temp:.0f}°C", 15000))
        elif temp >= 40:
            alerts.append(("Heat Advisory", "High", f"Temperature around {temp:.0f}°C", 12000))
        return [
            {
                "id": f"wx-{i}-{int(lat*100)}",
                "title": x[0],
                "risk": x[1],
                "description": x[2],
                "region": place,
                "lat": lat,
                "lon": lon,
                "radius": x[3],
                "source": "Open-Meteo weather data",
                "official": "IMD",
                "source_url": IMD_URL,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            for i, x in enumerate(alerts)
        ]
    except Exception:
        return []

@app.route("/")
def home():
    body = """
    <div class="container">

        <section class="hero">

            <div class="kicker">
                Smart disaster management
            </div>

            <h1>
                DISASTER <span>X</span>
            </h1>

            <p>
                Report disasters, see verified incidents and weather alerts,
                find nearby emergency services and get route assistance.
            </p>

            <div class="actions" style="justify-content:center">

                <a class="btn" href="/report">
                    🚨 Report Disaster
                </a>

                <a class="btn blue" href="/emergency-mode">
                    🧭 Emergency Mode
                </a>

                <a class="btn dark" href="/map">
                    🗺️ Open Disaster Map
                </a>

            </div>

        </section>


        <!-- DISASTER PREPAREDNESS QUOTE -->

        <section
            class="card"
            style="
                max-width:950px;
                margin:20px auto 40px;
                text-align:center;
                padding:35px 30px;
            "
        >

            <div class="kicker">
                Disaster preparedness
            </div>

            <div
                style="
                    font-size:clamp(20px,3vw,30px);
                    line-height:1.5;
                    font-weight:700;
                    margin:15px auto;
                "
            >
                “We cannot stop natural disasters,
                but we can arm ourselves with knowledge.”
            </div>

            <div
                class="muted"
                style="
                    font-size:16px;
                    margin-top:12px;
                "
            >
                — Petra Nemcova
            </div>

        </section>


        <!-- QUICK INFORMATION -->

        <section
            class="grid"
            style="
                max-width:950px;
                margin:auto;
            "
        >

            <div class="card">
                <h3>🚨 Report</h3>
                <p class="muted">
                    Submit information about a disaster
                    in your area for verification.
                </p>
                <a class="btn small" href="/report">
                    Report Now
                </a>
            </div>


            <div class="card">
                <h3>🗺️ Disaster Map</h3>
                <p class="muted">
                    View verified affected areas,
                    alerts and live location assistance.
                </p>
                <a class="btn blue small" href="/map">
                    Open Map
                </a>
            </div>


            <div class="card">
                <h3>🚑 Emergency</h3>
                <p class="muted">
                    Find nearby emergency services
                    and get route assistance.
                </p>
                <a class="btn dark small" href="/emergency">
                    Emergency Services
                </a>
            </div>

        </section>

    </div>
    """

    return page(body)
REPORT = r"""
<div class="container"><div class="form">
<div class="kicker">Community request</div><h1>🚨 Report a Disaster</h1>
<p class="muted">Enter a general area. Disaster X will find the location, PIN code and coordinates.</p>
{% if error %}<div class="alert">{{ error }}</div>{% endif %}
<label>Area / locality</label><div class="two"><input id="area" name="area" form="reportForm" placeholder="e.g. Salt Lake, Kolkata" required>
<button type="button" class="btn blue" onclick="findLocation()">📍 Find Location</button></div>
<div id="loc" class="info hidden"></div><div id="preview" class="hidden" style="margin-top:12px"><div id="miniMap" class="mapsmall"></div></div>
<form id="reportForm" method="post" action="/report">
<input type="hidden" id="lat" name="latitude"><input type="hidden" id="lon" name="longitude"><input type="hidden" id="pin" name="pin_code">
<input type="hidden" id="areaHidden" name="area">
<div class="two"><div><label>Disaster type</label><select name="disaster_type" required>
<option value="">Select type</option><option>Flood</option><option>Cyclone</option><option>Earthquake</option><option>Fire</option><option>Landslide</option><option>Drought</option><option>Storm</option><option>Tsunami</option><option>Industrial Accident</option><option>Other</option></select></div>
<div><label>Severity / risk</label><select name="severity" required><option value="">Select risk</option><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select></div></div>
<label>Description</label><textarea name="description" placeholder="What happened? What help is needed?"></textarea>
<div class="four">
<div><label>People affected</label><input type="number" name="people_affected" min="0" value="0"></div>
<div><label>Need immediate help</label><input type="number" name="people_needing_help" min="0" value="0"></div>
<div><label>Injured</label><input type="number" name="injured" min="0" value="0"></div>
<div><label>Missing</label><input type="number" name="missing" min="0" value="0"></div></div>
<label>People displaced</label><input type="number" name="displaced" min="0" value="0">
<div class="two"><div><label>Workforce required</label><input name="workforce" placeholder="e.g. 20 rescue workers, 2 medical teams"></div>
<div><label>Supplies required</label><input name="supplies" placeholder="e.g. water, food, tents, medicines"></div></div>
<div class="actions"><button class="btn" type="submit">Submit Request</button><a class="btn dark" href="/">Cancel</a></div>
</form></div></div>
<script>
let m=null,marker=null;
async function findLocation(){
 const area=document.getElementById('area').value.trim(), box=document.getElementById('loc');
 if(!area){box.className='alert';box.textContent='Enter an area first.';return}
 box.className='info';box.textContent='Finding location...';
 try{
  const r=await fetch('/api/geocode?area='+encodeURIComponent(area)); const d=await r.json();
  if(!d.success){box.className='alert';box.textContent=d.message;return}
  document.getElementById('areaHidden').value=area;document.getElementById('lat').value=d.lat;
  document.getElementById('lon').value=d.lon;document.getElementById('pin').value=d.pin||'';
  box.innerHTML='<b>Location found</b><br>'+d.display+'<br>PIN: '+(d.pin||'Not available')+' • Lat: '+d.lat.toFixed(6)+' • Lon: '+d.lon.toFixed(6);
  document.getElementById('preview').classList.remove('hidden');
  if(!m){
    m=L.map('miniMap').setView([d.lat,d.lon],14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap'}).addTo(m)
  } else {
    m.setView([d.lat,d.lon],14);
  }
  if(marker)m.removeLayer(marker);
  marker=L.marker([d.lat,d.lon]).addTo(m).bindPopup(d.display).openPopup();
  setTimeout(()=>m.invalidateSize(),200);
 }catch(e){box.className='alert';box.textContent='Location service is unavailable. Try again.'}
}
document.getElementById('reportForm').addEventListener('submit',e=>{
 if(!document.getElementById('lat').value){e.preventDefault();alert('Find the location before submitting.')}
});
</script>
"""

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "GET":
        return page(render_template_string(REPORT, error=None), "Report Disaster")
    area = request.form.get("area", "").strip()
    lat = request.form.get("latitude")
    lon = request.form.get("longitude")
    if not area or not lat or not lon:
        return page(render_template_string(REPORT, error="Please find the area location before submitting."), "Report Disaster")
    try:
        vals = {k: int(request.form.get(k, 0) or 0) for k in ["people_affected", "people_needing_help", "injured", "missing", "displaced"]}
        if min(vals.values()) < 0:
            raise ValueError
        la, lo = float(lat), float(lon)
    except ValueError:
        return page(render_template_string(REPORT, error="Impact numbers and coordinates must be valid non-negative values."), "Report Disaster")
    c = db()
    c.execute("""insert into reports(area,pin_code,latitude,longitude,disaster_type,severity,description,
    people_affected,people_needing_help,injured,missing,displaced,workforce,supplies,status,created_at)
    values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (area, request.form.get("pin_code", ""), la, lo, request.form.get("disaster_type", ""),
    request.form.get("severity", ""), request.form.get("description", ""), vals["people_affected"], vals["people_needing_help"],
    vals["injured"], vals["missing"], vals["displaced"], request.form.get("workforce", ""), request.form.get("supplies", ""),
    "Pending", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    c.commit()
    c.close()
    return redirect(url_for("report_submitted"))

@app.route("/report-submitted")
def report_submitted():
    return page('<div class="container center"><div class="card"><h1>✅ Request submitted</h1><p class="muted">Your report is now a pending request. An administrator must verify it before it appears on the public disaster map.</p><a class="btn" href="/">Back Home</a></div></div>')

@app.route("/api/geocode")
def api_geocode():
    q = request.args.get("area", "").strip()
    if not q:
        return jsonify(success=False, message="Area is required"),400
    x = geocode(q)
    return jsonify(success=bool(x), **(x or {"message":"Location not found"}))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USERNAME and request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_reports"))
        error = "Invalid username or password."
    body = f"""<div class="container"><div class="form" style="max-width:480px"><div class="kicker">Restricted access</div>
    <h1>Admin Login</h1>{'<div class="alert">'+error+'</div>' if error else ''}
    <form method="post"><label>Username</label><input name="username" required><label>Password</label><input type="password" name="password" required>
    <div class="actions"><button class="btn" type="submit">Login</button></div></form></div></div>"""
    return page(body,"Admin Login")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/admin/reports")
@admin_required
def admin_reports():

    c = db()

    rows = [
        dict(x)
        for x in c.execute(
            "select * from reports order by id desc"
        ).fetchall()
    ]

    total = c.execute(
        "select count(*) n from reports"
    ).fetchone()["n"]

    verified = c.execute(
        "select count(*) n from reports where status='Verified'"
    ).fetchone()["n"]

    pending = c.execute(
        "select count(*) n from reports where status='Pending'"
    ).fetchone()["n"]

    c.close()


    # ---------------------------------------------------------
    # REPORT CARDS
    # ---------------------------------------------------------

    cards = ""

    for r in rows:

        cards += f"""
        <div class="card">

            <div class="two">

                <div>

                    <h3>
                        Request #{r['id']} • {r['area']}
                    </h3>

                    <div class="muted">
                        {r['created_at']}
                        •
                        {r['disaster_type']}
                        •
                        <span class="{r['severity'].lower()}">
                            {r['severity']}
                        </span>
                    </div>

                    <p>
                        {r['description'] or 'No description'}
                    </p>

                    <p>
                        <b>Impact:</b>
                        {r['people_affected']} affected
                        •
                        {r['people_needing_help']} need help
                        •
                        {r['injured']} injured
                        •
                        {r['missing']} missing
                        •
                        {r['displaced']} displaced
                    </p>

                    <p>
                        <b>Workforce:</b>
                        {r['workforce'] or 'Not specified'}
                        <br>

                        <b>Supplies:</b>
                        {r['supplies'] or 'Not specified'}
                    </p>

                    <p class="muted">
                        PIN {r['pin_code'] or 'N/A'}
                        •
                        {r['latitude']:.6f},
                        {r['longitude']:.6f}
                    </p>

                </div>


                <div>

                    <p>
                        Status:

                        <span
                            class="badge {r['status'].lower()}"
                        >
                            {r['status']}
                        </span>
                    </p>


                    <div class="actions">

                        <form
                            method="post"
                            action="/admin/report/{r['id']}/verify"
                        >
                            <button
                                class="btn green small"
                                type="submit"
                            >
                                ✓ Verify
                            </button>
                        </form>


                        <form
                            method="post"
                            action="/admin/report/{r['id']}/reject"
                        >
                            <button
                                class="btn orange small"
                                type="submit"
                            >
                                ✕ Reject
                            </button>
                        </form>


                        <form
                            method="post"
                            action="/admin/report/{r['id']}/delete"
                            onsubmit="
                                return confirm(
                                    'Permanently delete this request?'
                                )
                            "
                        >
                            <button
                                class="btn dark small"
                                type="submit"
                            >
                                🗑 Delete
                            </button>
                        </form>

                    </div>

                </div>

            </div>

        </div>
        """


    # ---------------------------------------------------------
    # ADMIN PAGE
    # ---------------------------------------------------------

    body = f"""

    <div class="container">

        <div class="kicker">
            Administrator
        </div>

        <h1>
            Reports Dashboard
        </h1>

        <p class="muted">
            Manage community disaster reports.
            Only verified requests are shown publicly
            on the disaster map.
        </p>


        <!-- STATISTICS MOVED FROM HOME -->

        <div
            class="grid"
            style="
                margin:25px 0;
            "
        >

            <div class="card">

                <div class="muted">
                    Total Reports
                </div>

                <div class="big">
                    {total}
                </div>

            </div>


            <div class="card">

                <div class="muted">
                    Verified
                </div>

                <div
                    class="big"
                    style="color:#4ade80"
                >
                    {verified}
                </div>

            </div>


            <div class="card">

                <div class="muted">
                    Pending
                </div>

                <div
                    class="big"
                    style="color:#fbbf24"
                >
                    {pending}
                </div>

            </div>

        </div>


        <!-- REPORT LIST -->

        <div
            style="
                margin-top:30px;
            "
        >

            <div class="kicker">
                Community Reports
            </div>

            <h2>
                All Requests
            </h2>

            {cards or '''
            <div class="card">

                <h3>
                    No reports yet
                </h3>

                <p class="muted">
                    Community disaster reports
                    will appear here when submitted.
                </p>

            </div>
            '''}

        </div>

    </div>

    """

    return page(body, "Admin Reports")
@app.route("/admin/report/<int:rid>/verify", methods=["POST"])
@admin_required
def verify(rid):
    c = db()
    c.execute("update reports set status='Verified',verified_at=? where id=?", (datetime.now().isoformat(timespec="seconds"), rid))
    c.commit()
    c.close()
    return redirect(url_for("admin_reports"))

@app.route("/admin/report/<int:rid>/reject", methods=["POST"])
@admin_required
def reject(rid):
    c = db()
    c.execute("update reports set status='Rejected',rejected_at=? where id=?", (datetime.now().isoformat(timespec="seconds"), rid))
    c.commit()
    c.close()
    return redirect(url_for("admin_reports"))

@app.route("/admin/report/<int:rid>/delete", methods=["POST"])
@admin_required
def delete_report(rid):
    c = db()
    c.execute("delete from reports where id=?", (rid,))
    c.commit()
    c.close()
    return redirect(url_for("admin_reports"))

@app.route("/api/verified-reports")
def verified_reports():
    c = db()
    rows = [dict(x) for x in c.execute("select * from reports where status='Verified' order by id desc").fetchall()]
    c.close()
    return jsonify(rows)

@app.route("/map")
def disaster_map():
    body = r"""
    <div class="container">

        <div class="kicker">Live disaster monitoring</div>

        <h1>🗺️ Disaster Map</h1>

        <p class="muted">
            Live location, verified disaster reports and weather-derived
            affected areas are shown together.
        </p>

        <div id="locationStatus" class="info">
            📍 Requesting your live location...
        </div>

        <div class="two" style="align-items:start">

            <!-- MAP -->
            <div>
                <div class="map-shell">
                    <div id="map"></div>
                </div>

                <div class="card" style="margin-top:14px">
                    <h3>🧭 Selected Destination</h3>
                    <div id="routeInfo" class="muted">
                        Select an affected area from the list to see
                        the route and directions.
                    </div>
                </div>
            </div>

            <!-- AFFECTED AREAS -->
            <div>

                <div class="card">

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        gap:10px;
                    ">
                        <div>
                            <h3 style="margin-bottom:4px">
                                🚨 Affected Areas
                            </h3>

                            <div class="muted">
                                Distance and direction from your location
                            </div>
                        </div>

                        <button
                            class="btn blue small"
                            onclick="refreshMap()"
                        >
                            🔄 Refresh
                        </button>
                    </div>

                    <div
                        id="affectedList"
                        style="margin-top:15px"
                    >
                        <p class="muted">
                            Finding affected areas...
                        </p>
                    </div>

                </div>

            </div>

        </div>

    </div>

    <script>

    let map = null;
    let myMarker = null;
    let accuracyCircle = null;

    let routeLayer = null;

    let currentLat = null;
    let currentLon = null;

    let affectedAreas = [];

    let locationWatch = null;


    /*
     * ---------------------------------------------------------
     * DISTANCE
     * ---------------------------------------------------------
     */

    function distanceKm(lat1, lon1, lat2, lon2) {

        const R = 6371;

        const p1 = lat1 * Math.PI / 180;
        const p2 = lat2 * Math.PI / 180;

        const dp = (lat2 - lat1) * Math.PI / 180;
        const dl = (lon2 - lon1) * Math.PI / 180;

        const a =
            Math.sin(dp / 2) * Math.sin(dp / 2) +
            Math.cos(p1) *
            Math.cos(p2) *
            Math.sin(dl / 2) *
            Math.sin(dl / 2);

        const c = 2 * Math.atan2(
            Math.sqrt(a),
            Math.sqrt(1 - a)
        );

        return R * c;
    }


    /*
     * ---------------------------------------------------------
     * DIRECTION
     * ---------------------------------------------------------
     */

    function getDirection(lat1, lon1, lat2, lon2) {

        const lat1Rad = lat1 * Math.PI / 180;
        const lat2Rad = lat2 * Math.PI / 180;

        const dLon =
            (lon2 - lon1) * Math.PI / 180;

        const y = Math.sin(dLon) * Math.cos(lat2Rad);

        const x =
            Math.cos(lat1Rad) * Math.sin(lat2Rad) -
            Math.sin(lat1Rad) *
            Math.cos(lat2Rad) *
            Math.cos(dLon);

        let bearing =
            Math.atan2(y, x) * 180 / Math.PI;

        bearing = (bearing + 360) % 360;

        const directions = [
            "North",
            "North-East",
            "East",
            "South-East",
            "South",
            "South-West",
            "West",
            "North-West"
        ];

        const index =
            Math.round(bearing / 45) % 8;

        return {
            name: directions[index],
            bearing: Math.round(bearing)
        };
    }


    /*
     * ---------------------------------------------------------
     * CREATE MAP
     * ---------------------------------------------------------
     */

    function createMap(lat, lon) {

        if (map) {
            map.setView([lat, lon], 13);
            return;
        }

        map = L.map("map").setView(
            [lat, lon],
            13
        );

        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,
                attribution: "© OpenStreetMap"
            }
        ).addTo(map);

        setTimeout(function() {
            map.invalidateSize();
        }, 300);
    }


    /*
     * ---------------------------------------------------------
     * UPDATE MY LOCATION
     * ---------------------------------------------------------
     */

    function updateMyLocation(lat, lon, accuracy) {

        currentLat = lat;
        currentLon = lon;

        createMap(lat, lon);

        if (!myMarker) {

            myMarker = L.marker(
                [lat, lon]
            )
            .addTo(map)
            .bindPopup(
                "<b>📍 Your Live Location</b>"
            );

        } else {

            myMarker.setLatLng([lat, lon]);

        }

        if (!accuracyCircle) {

            accuracyCircle = L.circle(
                [lat, lon],
                {
                    radius: accuracy || 30,
                    color: "#38bdf8",
                    fillColor: "#38bdf8",
                    fillOpacity: 0.10,
                    weight: 2
                }
            ).addTo(map);

        } else {

            accuracyCircle.setLatLng([lat, lon]);

            if (accuracy) {
                accuracyCircle.setRadius(accuracy);
            }

        }

        document.getElementById(
            "locationStatus"
        ).innerHTML =
            "📍 <b>Live location active</b><br>" +
            "<span class='muted'>" +
            lat.toFixed(6) +
            ", " +
            lon.toFixed(6) +
            "</span>";

        updateAffectedList();

    }


    /*
     * ---------------------------------------------------------
     * LOAD VERIFIED REPORTS + WEATHER ALERTS
     * ---------------------------------------------------------
     */

    async function loadAffectedAreas() {

        try {

            const reportResponse =
                await fetch(
                    "/api/verified-reports"
                );

            const reports =
                await reportResponse.json();

            affectedAreas = [];

            reports.forEach(function(x) {

                if (
                    x.latitude === null ||
                    x.longitude === null
                ) {
                    return;
                }

                affectedAreas.push({

                    id: "report-" + x.id,

                    type: "Verified Report",

                    title:
                        x.disaster_type +
                        " — " +
                        x.area,

                    area: x.area,

                    lat: Number(x.latitude),

                    lon: Number(x.longitude),

                    severity: x.severity,

                    description:
                        x.description ||
                        "Verified disaster report.",

                    people:
                        Number(x.people_affected || 0),

                    color:
                        x.severity === "Critical"
                            ? "#ef4444"
                            : x.severity === "High"
                                ? "#f97316"
                                : x.severity === "Medium"
                                    ? "#eab308"
                                    : "#22c55e"

                });

            });


            /*
             * Weather alerts are calculated using
             * the user's live location.
             */

            if (
                currentLat !== null &&
                currentLon !== null
            ) {

                const alertResponse =
                    await fetch(
                        "/api/alerts?lat=" +
                        encodeURIComponent(currentLat) +
                        "&lon=" +
                        encodeURIComponent(currentLon) +
                        "&place=Your area"
                    );

                const alerts =
                    await alertResponse.json();

                alerts.forEach(function(x) {

                    affectedAreas.push({

                        id: x.id,

                        type: "Weather Alert",

                        title:
                            x.title +
                            " — " +
                            x.region,

                        area: x.region,

                        lat: Number(x.lat),

                        lon: Number(x.lon),

                        severity: x.risk,

                        description:
                            x.description,

                        people: 0,

                        color: "#a78bfa"

                    });

                });

            }

            drawAffectedAreas();

            updateAffectedList();

        } catch (error) {

            console.error(error);

            document.getElementById(
                "affectedList"
            ).innerHTML =
                "<div class='alert'>" +
                "Could not load affected areas." +
                "</div>";

        }

    }


    /*
     * ---------------------------------------------------------
     * DRAW DISASTER AREAS ON MAP
     * ---------------------------------------------------------
     */

    function drawAffectedAreas() {

        if (!map) {
            return;
        }

        /*
         * Remove old disaster layers.
         */

        map.eachLayer(function(layer) {

            if (
                layer._disasterXArea
            ) {
                map.removeLayer(layer);
            }

        });


        affectedAreas.forEach(function(area) {

            const distance =
                distanceKm(
                    currentLat,
                    currentLon,
                    area.lat,
                    area.lon
                );


            let radius = 1000;

            if (
                area.type === "Verified Report"
            ) {

                radius = Math.min(
                    1000 +
                    area.people * 8,
                    15000
                );

            } else {

                radius = 5000;

            }


            const circle =
                L.circle(
                    [area.lat, area.lon],
                    {
                        radius: radius,

                        color: area.color,

                        fillColor: area.color,

                        fillOpacity: 0.20,

                        weight: 2
                    }
                ).addTo(map);


            circle._disasterXArea = true;


            circle.bindPopup(
                "<b>" +
                area.type +
                "</b><br>" +

                area.title +
                "<br>" +

                "Risk: " +
                area.severity +
                "<br>" +

                "Distance: " +
                distance.toFixed(2) +
                " km"
            );

        });

    }


    /*
     * ---------------------------------------------------------
     * AFFECTED AREA LIST
     * ---------------------------------------------------------
     */

    function updateAffectedList() {

        const box =
            document.getElementById(
                "affectedList"
            );

        if (
            currentLat === null ||
            currentLon === null
        ) {

            box.innerHTML =
                "<p class='muted'>" +
                "Waiting for your location..." +
                "</p>";

            return;

        }


        if (!affectedAreas.length) {

            box.innerHTML =
                "<div class='card'>" +
                "<h3>✓ No affected areas</h3>" +
                "<p class='muted'>" +
                "No verified reports or current " +
                "weather-derived affected areas " +
                "were found." +
                "</p>" +
                "</div>";

            return;

        }


        const sorted =
            affectedAreas
            .map(function(area) {

                const distance =
                    distanceKm(
                        currentLat,
                        currentLon,
                        area.lat,
                        area.lon
                    );

                const direction =
                    getDirection(
                        currentLat,
                        currentLon,
                        area.lat,
                        area.lon
                    );

                return {
                    area: area,
                    distance: distance,
                    direction: direction
                };

            })
            .sort(function(a, b) {

                return a.distance -
                    b.distance;

            });


        box.innerHTML = "";


        sorted.forEach(function(item, index) {

            const area = item.area;

            const typeClass =
                area.type === "Verified Report"
                    ? "danger"
                    : "successText";


            box.innerHTML += `

                <div
                    class="card affected-item"
                    style="
                        margin-bottom:12px;
                        border-left:5px solid ${area.color};
                    "
                >

                    <div style="
                        display:flex;
                        justify-content:space-between;
                        gap:10px;
                        align-items:flex-start;
                    ">

                        <div>

                            <div class="kicker">
                                ${area.type}
                            </div>

                            <h3 style="
                                margin:5px 0;
                            ">
                                ${area.title}
                            </h3>

                        </div>

                        <span
                            class="badge"
                            style="
                                background:${area.color}22;
                                color:${area.color};
                            "
                        >
                            ${area.severity}
                        </span>

                    </div>


                    <p class="muted">
                        ${area.description}
                    </p>


                    <div
                        style="
                            display:grid;
                            grid-template-columns:
                                1fr 1fr;
                            gap:8px;
                            margin-top:12px;
                        "
                    >

                        <div class="info"
                            style="margin:0"
                        >
                            📏 <b>
                            ${item.distance.toFixed(2)}
                            km
                            </b>
                            <br>
                            <span class="muted">
                                From your location
                            </span>
                        </div>


                        <div class="info"
                            style="margin:0"
                        >
                            🧭 <b>
                            ${item.direction.name}
                            </b>
                            <br>
                            <span class="muted">
                                Bearing:
                                ${item.direction.bearing}°
                            </span>
                        </div>

                    </div>


                    <div class="actions">

                        <button
                            class="btn blue small"
                            onclick="
                                showWay(
                                    ${area.lat},
                                    ${area.lon},
                                    '${encodeURIComponent(area.title)}'
                                )
                            "
                        >
                            🧭 Show Way
                        </button>


                        <button
                            class="btn dark small"
                            onclick="
                                focusArea(
                                    ${area.lat},
                                    ${area.lon}
                                )
                            "
                        >
                            🔎 View Area
                        </button>

                    </div>

                </div>

            `;

        });

    }


    /*
     * ---------------------------------------------------------
     * FOCUS ON DISASTER
     * ---------------------------------------------------------
     */

    function focusArea(lat, lon) {

        if (!map) {
            return;
        }

        map.setView(
            [lat, lon],
            14
        );

    }


    /*
     * ---------------------------------------------------------
     * SHOW ROUTE / WAY
     * ---------------------------------------------------------
     */

    async function showWay(
        lat,
        lon,
        encodedTitle
    ) {

        if (
            currentLat === null ||
            currentLon === null
        ) {

            alert(
                "Your live location is not available yet."
            );

            return;

        }


        const title =
            decodeURIComponent(
                encodedTitle
            );


        const info =
            document.getElementById(
                "routeInfo"
            );


        info.innerHTML =
            "<h3>🧭 Calculating route...</h3>" +
            "<p class='muted'>" +
            "Finding the best available road route." +
            "</p>";


        try {

            const response =
                await fetch(
                    "/api/route" +
                    "?from_lat=" +
                    encodeURIComponent(currentLat) +
                    "&from_lon=" +
                    encodeURIComponent(currentLon) +
                    "&to_lat=" +
                    encodeURIComponent(lat) +
                    "&to_lon=" +
                    encodeURIComponent(lon)
                );


            const data =
                await response.json();


            if (routeLayer) {

                map.removeLayer(
                    routeLayer
                );

                routeLayer = null;

            }


            if (data.geometry) {

                routeLayer =
                    L.geoJSON(
                        data.geometry,
                        {
                            style: {
                                weight: 7,
                                color: "#38bdf8",
                                opacity: 0.9
                            }
                        }
                    ).addTo(map);


                map.fitBounds(
                    routeLayer.getBounds(),
                    {
                        padding: [40, 40]
                    }
                );

            } else {

                /*
                 * Routing service unavailable.
                 * Still show straight-line direction.
                 */

                routeLayer =
                    L.polyline(
                        [
                            [currentLat, currentLon],
                            [lat, lon]
                        ],
                        {
                            color: "#38bdf8",
                            weight: 5,
                            dashArray: "10 8"
                        }
                    ).addTo(map);

            }


            const distance =
                data.distance ||
                distanceKm(
                    currentLat,
                    currentLon,
                    lat,
                    lon
                );


            const duration =
                data.duration || 0;


            const direction =
                getDirection(
                    currentLat,
                    currentLon,
                    lat,
                    lon
                );


            info.innerHTML = `

                <h3>🧭 Route to ${title}</h3>

                <p>
                    <b>📏 Distance:</b>
                    ${Number(distance).toFixed(2)}
                    km
                </p>

                <p>
                    <b>⏱️ Estimated travel time:</b>
                    ${
                        duration
                            ? Math.round(duration) +
                              " minutes"
                            : "Unavailable"
                    }
                </p>

                <p>
                    <b>🧭 Direction:</b>
                    ${direction.name}
                    (${direction.bearing}°)
                </p>

                <p class="muted">
                    The blue line shows the
                    available road route from
                    your current location to
                    the affected area.
                </p>

                <div class="actions">

                    <button
                        class="btn dark small"
                        onclick="clearRoute()"
                    >
                        ✕ Clear Route
                    </button>

                </div>

            `;

        } catch (error) {

            console.error(error);

            info.innerHTML =
                "<div class='alert'>" +
                "Could not calculate the route." +
                "</div>";

        }

    }


    /*
     * ---------------------------------------------------------
     * CLEAR ROUTE
     * ---------------------------------------------------------
     */

    function clearRoute() {

        if (routeLayer) {

            map.removeLayer(
                routeLayer
            );

            routeLayer = null;

        }


        document.getElementById(
            "routeInfo"
        ).innerHTML =
            "<span class='muted'>" +
            "Select an affected area from the " +
            "list to see the route and directions." +
            "</span>";

    }


    /*
     * ---------------------------------------------------------
     * REFRESH
     * ---------------------------------------------------------
     */

    async function refreshMap() {

        if (
            currentLat === null ||
            currentLon === null
        ) {
            return;
        }

        await loadAffectedAreas();

    }


    /*
     * ---------------------------------------------------------
     * LIVE GPS
     * ---------------------------------------------------------
     */

    function startLiveLocation() {

        if (
            !navigator.geolocation
        ) {

            document.getElementById(
                "locationStatus"
            ).innerHTML =
                "<div class='alert'>" +
                "Your browser does not support " +
                "live location." +
                "</div>";

            /*
             * Fallback to Kolkata.
             */

            currentLat = 22.5726;
            currentLon = 88.3639;

            createMap(
                currentLat,
                currentLon
            );

            loadAffectedAreas();

            return;

        }


        navigator.geolocation.getCurrentPosition(

            function(position) {

                updateMyLocation(
                    position.coords.latitude,
                    position.coords.longitude,
                    position.coords.accuracy
                );

                loadAffectedAreas();

            },

            function(error) {

                console.warn(
                    "Location error:",
                    error
                );

                document.getElementById(
                    "locationStatus"
                ).innerHTML =
                    "<div class='alert'>" +
                    "⚠️ Live location permission " +
                    "was denied. Showing Kolkata " +
                    "as the fallback location." +
                    "</div>";

                currentLat = 22.5726;
                currentLon = 88.3639;

                createMap(
                    currentLat,
                    currentLon
                );

                loadAffectedAreas();

            },

            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 5000
            }

        );


        /*
         * Continuously watch the user's location.
         */

        locationWatch =
            navigator.geolocation.watchPosition(

                function(position) {

                    updateMyLocation(
                        position.coords.latitude,
                        position.coords.longitude,
                        position.coords.accuracy
                    );

                },

                function(error) {

                    console.warn(
                        "Live location update failed:",
                        error
                    );

                },

                {
                    enableHighAccuracy: true,
                    maximumAge: 5000,
                    timeout: 10000
                }

            );

    }


    /*
     * ---------------------------------------------------------
     * START
     * ---------------------------------------------------------
     */

    startLiveLocation();

    </script>

    <style>

        .affected-item {
            transition: .18s;
        }

        .affected-item:hover {
            transform: translateY(-2px);
            border-color: #4b6b8d;
        }

        @media(max-width:900px) {

            .two {
                grid-template-columns: 1fr !important;
            }

        }

    </style>
    """

    return page(body, "Disaster Map")
@app.route("/api/alerts")
def api_alerts():
    lat = float(request.args.get("lat", 22.5726))
    lon = float(request.args.get("lon", 88.3639))
    place = request.args.get("place", "India")
    return jsonify(weather_alerts(lat, lon, place))

@app.route("/alerts")
def alerts():
    body = r"""
    <div class="container"><div class="kicker">Weather & official sources</div><h1>🌦️ Alerts</h1>
    <p class="muted">Allow location access to see weather-derived risk around you. Government warning information is linked to the official IMD portal.</p>
    <div id="status" class="info">Getting your location...</div><div id="alerts" class="grid"></div>
    <div class="card" style="margin-top:18px"><h3>Trusted source</h3><p class="muted">India Meteorological Department (IMD) warnings, nowcasts and APIs.</p>
    <a class="btn blue" href="https://mausam.imd.gov.in/" target="_blank" rel="noopener">Open IMD</a></div></div>
    <script>
    function load(lat,lon){
      fetch('/api/alerts?lat='+lat+'&lon='+lon+'&place=Your area').then(r=>r.json()).then(a=>{
        const box=document.getElementById('alerts');box.innerHTML='';
        if(!a.length){box.innerHTML='<div class="card"><h3>✓ No derived weather alert</h3><p class="muted">No threshold-based alert was detected from current weather data.</p></div>';return}
        a.forEach(x=>{box.innerHTML+=`<div class="card alertcard ${x.risk.toLowerCase()}"><h3>⚠️ ${x.title}</h3><p>${x.description}</p><p><b>Region:</b> ${x.region}<br><b>Risk:</b> ${x.risk}<br><b>Source:</b> ${x.source}</p></div>`})
      }).catch(()=>document.getElementById('status').textContent='Unable to load weather data.')
    }
    navigator.geolocation.getCurrentPosition(
      p=>{document.getElementById('status').textContent='Location detected.';load(p.coords.latitude,p.coords.longitude)},
      ()=>{document.getElementById('status').textContent='Location unavailable; showing India-center weather.';load(22.5726,88.3639)}
    );
    </script>
    """
    return page(body,"Alerts")


@app.route("/emergency")
def emergency():
    cards = ""

    for name, num in EMERGENCY_SERVICES:
        cards += f"""
        <div class="card emergency-card">

            <div class="emergency-header">
                <div class="emergency-icon">🚨</div>

                <div>
                    <h3>{name}</h3>
                    <div class="muted">Emergency assistance</div>
                </div>
            </div>

            <div class="emergency-number">
                {num}
            </div>

            <div class="actions emergency-actions">

                <a
                    class="btn call-btn"
                    href="tel:{num}"
                >
                    📞 Call {num}
                </a>

                <a
                    class="btn blue"
                    href="sms:{num}"
                >
                    💬 Text
                </a>

                <button
                    class="btn dark"
                    type="button"
                    onclick="prepareSMS('{num}', {name!r})"
                >
                    📍 Text Location
                </button>

            </div>

        </div>
        """

    body = f"""
    <div class="container">

        <div class="kicker">Get help quickly</div>

        <h1>🚨 Emergency Services</h1>

        <p class="muted">
            Quickly contact emergency services or send your location.
        </p>

        <div class="alert">
            <strong>⚠️ Immediate Emergency</strong><br>
            For a general emergency in India, call
            <strong>112</strong>.
        </div>

        <div class="grid">
            {cards}
        </div>

        <div
            id="smsBox"
            class="card hidden"
            style="margin-top:18px"
        ></div>

    </div>

    <script>
    function prepareSMS(number, serviceName) {{

        const box = document.getElementById("smsBox");

        if (!navigator.geolocation) {{
            box.classList.remove("hidden");

            box.innerHTML =
                "<h3>📍 Location unavailable</h3>" +
                "<p class='muted'>" +
                "Your browser does not support location services." +
                "</p>";

            return;
        }}

        box.classList.remove("hidden");

        box.innerHTML =
            "<h3>📍 Getting your location...</h3>" +
            "<p class='muted'>Please allow location access.</p>";

        navigator.geolocation.getCurrentPosition(

            function(position) {{

                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                const mapsLink =
                    "https://maps.google.com/?q=" +
                    lat + "," + lon;

                const message =
                    "DISASTER X EMERGENCY\\n" +
                    "Service: " + serviceName + "\\n" +
                    "Location: " + mapsLink + "\\n" +
                    "Coordinates: " +
                    lat.toFixed(6) + ", " +
                    lon.toFixed(6);

                const smsURL =
                    "sms:" +
                    number +
                    "?body=" +
                    encodeURIComponent(message);

                box.innerHTML =
                    "<h3>📍 Location Message Ready</h3>" +
                    "<p style='white-space:pre-wrap'>" +
                    message +
                    "</p>" +

                    "<div class='actions'>" +

                    "<a class='btn blue' " +
                    "href='" + smsURL + "'>" +
                    "💬 Open SMS" +
                    "</a>" +

                    "<button class='btn dark' " +
                    "onclick='copyEmergencyMessage(" +
                    JSON.stringify(message) +
                    ")'>" +
                    "📋 Copy Message" +
                    "</button>" +

                    "</div>";
            }},

            function(error) {{

                box.classList.remove("hidden");

                box.innerHTML =
                    "<h3>⚠️ Location Permission Required</h3>" +
                    "<p class='muted'>" +
                    "Disaster X could not access your location. " +
                    "Allow location access in your browser and try again." +
                    "</p>";
            }},

            {{
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 5000
            }}
        );
    }}


    function copyEmergencyMessage(message) {{

        if (navigator.clipboard) {{

            navigator.clipboard.writeText(message)
                .then(function() {{

                    alert("Emergency message copied.");

                }})
                .catch(function() {{

                    alert("Could not copy the message.");

                }});

        }} else {{

            alert("Copy is not supported by this browser.");

        }}
    }}
    </script>

    <style>

    .emergency-card {{
        position: relative;
        overflow: hidden;
    }}

    .emergency-header {{
        display: flex;
        align-items: center;
        gap: 14px;
    }}

    .emergency-header h3 {{
        margin: 0 0 5px 0;
    }}

    .emergency-icon {{
        width: 55px;
        height: 55px;
        border-radius: 14px;

        display: flex;
        align-items: center;
        justify-content: center;

        background: rgba(239, 68, 68, .12);
        border: 1px solid rgba(239, 68, 68, .3);

        font-size: 28px;
    }}

    .emergency-number {{
        font-size: 42px;
        font-weight: 900;

        margin-top: 22px;
        margin-bottom: 5px;

        color: #fff;
    }}

    .emergency-actions {{
        margin-top: 16px;
    }}

    .call-btn {{
        background: #dc2626;
    }}

    .call-btn:hover {{
        background: #b91c1c;
    }}

    @media(max-width:600px) {{

        .emergency-number {{
            font-size: 36px;
        }}

        .emergency-actions {{
            flex-direction: column;
        }}

        .emergency-actions .btn {{
            width: 100%;
        }}

    }}

    </style>
    """

    return page(body, "Emergency Services")
@app.route("/emergency-mode")
def emergency_mode():
    body = r"""
    <div class="container"><div class="kicker">Live assistance</div><h1>🧭 Emergency Mode</h1>
    <div id="status" class="info">Requesting live location...</div>
    <div class="two" style="align-items:start">
      <div><div class="map-shell"><div id="map"></div></div></div>
      <div>
        <div class="card"><h3>Nearby services within 10 km</h3><div id="services"><p class="muted">Finding hospitals, police stations and fire stations...</p></div></div>
        <div id="routeCard" class="card hidden" style="margin-top:12px"></div>
      </div>
    </div></div>

    <script>
    let map, me, routeLayer, watchId, services = [];

    function renderServices(lat, lon) {
      const box = document.getElementById('services');
      box.innerHTML = '';
      if (!services.length) {
        box.innerHTML = '<p class="muted">No mapped services were found within 10 km.</p>';
        return;
      }
      services.forEach((s, i) => {
        box.innerHTML += `<div class="service" onclick="selectService(${i}, ${lat}, ${lon})">
          <div><div class="title">📍 ${s.name}</div><div class="muted">${s.type}</div></div>
          <div class="distance">${s.distance.toFixed(2)} km</div>
        </div>`;
      });
    }

    function initMap(lat, lon) {
      map = L.map('map').setView([lat, lon], 13);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
      }).addTo(map);

      me = L.marker([lat, lon]).addTo(map).bindPopup('Your live location').openPopup();
      setTimeout(()=>map.invalidateSize(), 250);

      fetch('/api/nearby?lat=' + lat + '&lon=' + lon)
        .then(r => r.json())
        .then(d => {
          services = Array.isArray(d.services) ? d.services : [];
          renderServices(lat, lon);
          services.forEach((s, i) => {
            s.marker = L.marker([s.lat, s.lon]).addTo(map)
              .bindPopup('<b>' + s.name + '</b><br>' + s.type + '<br>' + s.distance.toFixed(2) + ' km');
            s.marker.on('click', () => selectService(i, lat, lon));
          });
        })
        .catch(() => {
          document.getElementById('services').innerHTML =
            '<div class="alert">Could not load nearby services right now.</div>';
        });

      if (navigator.geolocation && navigator.geolocation.watchPosition) {
        watchId = navigator.geolocation.watchPosition(
          p => {
            if (me) me.setLatLng([p.coords.latitude, p.coords.longitude]);
          },
          () => {},
          { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
        );
      }
    }

    function selectService(i, lat, lon) {
      const s = services[i];
      fetch(`/api/route?from_lat=${lat}&from_lon=${lon}&to_lat=${s.lat}&to_lon=${s.lon}`)
        .then(r => r.json())
        .then(d => {
          const km = d.distance || s.distance;
          const mins = d.duration || Math.round(km / 0.5);

          document.getElementById('routeCard').classList.remove('hidden');
          document.getElementById('routeCard').innerHTML =
            '<h3>📍 ' + s.name + '</h3>' +
            '<p><b>Distance:</b> ' + km.toFixed(2) + ' km<br><b>Estimated time:</b> ' + Math.round(mins) + ' min</p>' +
            '<div class="actions"><button class="btn green" onclick="showRoute()">▶ Start Directions</button><button class="btn dark" onclick="stopRoute()">■ Stop</button></div>' +
            '<div id="steps" class="muted" style="margin-top:12px"></div>';

          if (routeLayer) map.removeLayer(routeLayer);
          if (d.geometry) {
            routeLayer = L.geoJSON(d.geometry, { style: { weight: 6, color: '#38bdf8' } }).addTo(map);
            map.fitBounds(routeLayer.getBounds(), { padding: [30, 30] });
          }
          window.currentRoute = d;
          window.currentService = s;
        });
    }

    function showRoute() {
      const d = window.currentRoute;
      if (!d || !d.steps) {
        document.getElementById('steps').textContent = 'Follow the highlighted route.';
        return;
      }
      const steps = d.steps.slice(0, 12).map((x, n) =>
        `${n + 1}. ${x.maneuver && x.maneuver.instruction ? x.maneuver.instruction : (x.name ? 'Continue on ' + x.name : 'Continue')}`
      ).join('<br>');
      document.getElementById('steps').innerHTML = '<b>Assisted directions</b><br>' + steps;
    }

    function stopRoute() {
      if (routeLayer) {
        map.removeLayer(routeLayer);
        routeLayer = null;
      }
      document.getElementById('routeCard').classList.add('hidden');
    }

    navigator.geolocation.getCurrentPosition(
      p => {
        document.getElementById('status').textContent = 'Live location active.';
        initMap(p.coords.latitude, p.coords.longitude);
      },
      () => {
        document.getElementById('status').textContent = 'Location permission denied. Showing Kolkata center.';
        initMap(22.5726, 88.3639);
      },
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
    );
    </script>
    """
    return page(body, "Emergency Mode")

@app.route("/api/nearby")
def api_nearby():

    try:

        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))

        if not (-90 <= lat <= 90):
            raise ValueError

        if not (-180 <= lon <= 180):
            raise ValueError

    except Exception:

        return jsonify({
            "services": [],
            "error": "Invalid GPS coordinates"
        }), 400

    try:

        services = overpass_services(lat, lon)

        return jsonify({
            "services": services,
            "count": len(services)
        })

    except Exception as e:

        print(
            f"[Disaster X] Nearby service error: {e}"
        )

        return jsonify({
            "services": [],
            "count": 0,
            "error": "Nearby service lookup failed"
        })
@app.route("/api/route")
def api_route():
    try:
        a = float(request.args["from_lat"])
        b = float(request.args["from_lon"])
        c = float(request.args["to_lat"])
        d = float(request.args["to_lon"])
    except Exception:
        return jsonify(error="Invalid coordinates"), 400
    r = route(a, b, c, d)
    if not r:
        return jsonify(error="Routing service unavailable", distance=distance_km(a, b, c, d), duration=0)
    return jsonify(r)

@app.route("/api/health")
def health():
    return jsonify(ok=True, app="Disaster X")

if __name__ == "__main__":
    init_db()
    print("=" * 55)
    print("DISASTER X")
    print("http://127.0.0.1:5000")
    print("=" * 55)
if __name__ == "__main__":
    init_db()

    port = int(os.environ.get("PORT", 5000))

    print("=" * 55)
    print("DISASTER X")
    print(f"Running on port {port}")
    print("=" * 55)

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
