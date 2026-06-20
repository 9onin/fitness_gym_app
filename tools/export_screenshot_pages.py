import base64
import os
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots" / "html"

sys.path.insert(0, str(ROOT))

dotenv = types.ModuleType("dotenv")
dotenv.load_dotenv = lambda *args, **kwargs: None
dotenv.find_dotenv = lambda *args, **kwargs: ""
sys.modules["dotenv"] = dotenv

report_service = types.ModuleType("services.report_service")
report_service.generate_pdf_report = lambda *args, **kwargs: b""
report_service.generate_excel_report = lambda *args, **kwargs: b""
sys.modules["services.report_service"] = report_service

os.environ.setdefault("MAIL_SUPPRESS_SEND", "True")

from app import create_app
from models.database import db
from models.models import User


TAILWIND_FALLBACK = """
*{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif;color:#0f172a}.container{max-width:1180px;margin-left:auto;margin-right:auto}.mx-auto{margin-left:auto;margin-right:auto}.px-4{padding-left:1rem;padding-right:1rem}.py-3{padding-top:.75rem;padding-bottom:.75rem}.py-4{padding-top:1rem;padding-bottom:1rem}.py-6{padding-top:1.5rem;padding-bottom:1.5rem}.py-8{padding-top:2rem;padding-bottom:2rem}.p-4{padding:1rem}.p-5{padding:1.25rem}.p-6{padding:1.5rem}.mb-2{margin-bottom:.5rem}.mb-3{margin-bottom:.75rem}.mb-4{margin-bottom:1rem}.mb-6{margin-bottom:1.5rem}.mb-8{margin-bottom:2rem}.mt-2{margin-top:.5rem}.mt-3{margin-top:.75rem}.mt-4{margin-top:1rem}.mt-6{margin-top:1.5rem}.mt-8{margin-top:2rem}.mr-2{margin-right:.5rem}.ml-2{margin-left:.5rem}.min-h-screen{min-height:100vh}.flex{display:flex}.inline-flex{display:inline-flex}.grid{display:grid}.hidden{display:none}.block{display:block}.items-center{align-items:center}.items-start{align-items:flex-start}.justify-between{justify-content:space-between}.justify-center{justify-content:center}.gap-2{gap:.5rem}.gap-3{gap:.75rem}.gap-4{gap:1rem}.gap-6{gap:1.5rem}.space-x-4>*+*{margin-left:1rem}.space-y-2>*+*{margin-top:.5rem}.space-y-3>*+*{margin-top:.75rem}.space-y-4>*+*{margin-top:1rem}.flex-col{flex-direction:column}.flex-1{flex:1}.w-full{width:100%}.h-5{height:1.25rem}.w-5{width:1.25rem}.h-6{height:1.5rem}.w-6{width:1.5rem}.h-10{height:2.5rem}.w-10{width:2.5rem}.rounded{border-radius:.25rem}.rounded-lg{border-radius:.5rem}.rounded-xl{border-radius:.75rem}.rounded-2xl{border-radius:1rem}.shadow{box-shadow:0 1px 3px rgba(15,23,42,.18)}.shadow-md{box-shadow:0 4px 12px rgba(15,23,42,.18)}.shadow-lg{box-shadow:0 12px 24px rgba(15,23,42,.18)}.border{border:1px solid #e2e8f0}.border-t{border-top:1px solid #e2e8f0}.border-b{border-bottom:1px solid #e2e8f0}.bg-white{background:#fff}.bg-gray-50{background:#f9fafb}.bg-gray-100{background:#f3f4f6}.bg-slate-50{background:#f8fafc}.bg-slate-100{background:#f1f5f9}.bg-indigo-50{background:#eef2ff}.bg-indigo-100{background:#e0e7ff}.bg-indigo-600{background:#4f46e5}.bg-indigo-700{background:#4338ca}.bg-indigo-800{background:#3730a3}.bg-blue-50{background:#eff6ff}.bg-blue-100{background:#dbeafe}.bg-green-50{background:#f0fdf4}.bg-green-100{background:#dcfce7}.bg-purple-50{background:#faf5ff}.bg-yellow-50{background:#fefce8}.bg-red-50{background:#fef2f2}.text-white{color:#fff}.text-slate-500{color:#64748b}.text-slate-600{color:#475569}.text-slate-700{color:#334155}.text-slate-800{color:#1e293b}.text-slate-900{color:#0f172a}.text-gray-500{color:#6b7280}.text-gray-600{color:#4b5563}.text-gray-700{color:#374151}.text-gray-800{color:#1f2937}.text-indigo-100{color:#e0e7ff}.text-indigo-200{color:#c7d2fe}.text-indigo-600{color:#4f46e5}.text-indigo-700{color:#4338ca}.text-blue-700{color:#1d4ed8}.text-green-700{color:#15803d}.text-red-600{color:#dc2626}.text-xs{font-size:.75rem}.text-sm{font-size:.875rem}.text-base{font-size:1rem}.text-lg{font-size:1.125rem}.text-xl{font-size:1.25rem}.text-2xl{font-size:1.5rem}.text-3xl{font-size:1.875rem}.text-4xl{font-size:2.25rem}.font-bold{font-weight:700}.font-semibold{font-weight:600}.font-medium{font-weight:500}.leading-tight{line-height:1.25}.text-center{text-align:center}.hover\\:text-indigo-200:hover{color:#c7d2fe}.hover\\:bg-indigo-900:hover{background:#312e81}a{text-decoration:none}.underline{text-decoration:underline}ul{margin:0;padding-left:1.35rem}button,.btn,a[class*='bg-indigo']{cursor:pointer}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}.overflow-hidden{overflow:hidden}.overflow-x-auto{overflow-x:auto}.relative{position:relative}.absolute{position:absolute}.sticky{position:sticky}.top-0{top:0}.z-40{z-index:40}.object-cover{object-fit:cover}.max-w-2xl{max-width:42rem}.max-w-3xl{max-width:48rem}.max-w-4xl{max-width:56rem}.max-w-6xl{max-width:72rem}.table-auto{table-layout:auto}.min-w-full{min-width:100%}table{border-collapse:collapse;width:100%}th,td{padding:.65rem;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top}thead th{background:#f8fafc;font-weight:700}.grid-cols-1{grid-template-columns:repeat(1,minmax(0,1fr))}@media(min-width:768px){.md\\:block{display:block}.md\\:hidden{display:none}.md\\:flex{display:flex}.md\\:grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.md\\:grid-cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}.md\\:grid-cols-4{grid-template-columns:repeat(4,minmax(0,1fr))}.md\\:text-5xl{font-size:3rem}}@media(min-width:1024px){.lg\\:grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.lg\\:grid-cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}.lg\\:grid-cols-4{grid-template-columns:repeat(4,minmax(0,1fr))}}
"""


def ensure_users(app):
    with app.app_context():
        for email, first, last, is_admin in [
            ("user@example.com", "Иван", "Иванов", False),
            ("admin@example.com", "Админ", "Администраторов", True),
        ]:
            user = User.query.filter_by(email=email).first()
            if user is None:
                user = User(email=email, first_name=first, last_name=last, is_admin=is_admin)
                db.session.add(user)
            user.first_name = first
            user.last_name = last
            user.is_admin = is_admin
            user.set_password("password")
        db.session.commit()


def inline_assets(html):
    css = (ROOT / "static" / "css" / "main.css").read_text(encoding="utf-8")
    bg = ROOT / "static" / "images" / "homepage-gym-bg.png"
    bg_data = "data:image/png;base64," + base64.b64encode(bg.read_bytes()).decode("ascii")
    html = html.replace('<script src="https://cdn.tailwindcss.com"></script>', "")
    html = html.replace('<link rel="stylesheet" href="/static/css/main.css">', f"<style>{TAILWIND_FALLBACK}\n{css}</style>")
    html = html.replace('/static/images/homepage-gym-bg.png', bg_data)
    html = html.replace('href="/', 'href="#')
    html = html.replace('src="/', 'src="#')
    return html


def login(client, email):
    with client.application.app_context():
        user = User.query.filter_by(email=email).first()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True
        sess["_id"] = "screenshot-session"


def save_page(client, route, filename):
    response = client.get(route, follow_redirects=True)
    response.raise_for_status = lambda: None
    html = response.get_data(as_text=True)
    (OUT / filename).write_text(inline_assets(html), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    app = create_app()
    ensure_users(app)

    with app.test_client() as client:
        save_page(client, "/", "homepage_public.html")

    with app.test_client() as client:
        login(client, "user@example.com")
        save_page(client, "/", "homepage_user.html")
        save_page(client, "/user/workouts", "user_workouts.html")
        save_page(client, "/user/schedule", "user_schedule.html")

    with app.test_client() as client:
        login(client, "admin@example.com")
        save_page(client, "/admin/dashboard", "admin_dashboard.html")
        save_page(client, "/admin/users", "admin_users.html")

    print(OUT)


if __name__ == "__main__":
    main()
