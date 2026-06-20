import os
import sys
import types

sys.path.insert(0, os.getcwd())

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

app = create_app()
app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False)
