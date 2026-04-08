import logging
import re
from typing import List, Optional
from models.schemas import Lead

logger = logging.getLogger(__name__)

COLUMNS = ["Name", "City", "Instagram", "Phone", "Website", "Notes", "About"]
FIELD_MAP = ["name", "city", "instagram", "phone", "website", "notes", "about"]


def _extract_sheet_id(url: str) -> Optional[str]:
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    return m.group(1) if m else None


def push_to_sheets(leads: List[Lead], spreadsheet_url: str, credentials_path: Optional[str] = None) -> dict:
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return {"success": False, "error": "gspread or google-auth not installed. Run: pip install gspread google-auth"}

    sheet_id = _extract_sheet_id(spreadsheet_url)
    if not sheet_id:
        return {"success": False, "error": "Invalid Google Sheets URL"}

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_file = credentials_path or "service_account.json"
    try:
        creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
        gc = gspread.authorize(creds)
    except FileNotFoundError:
        return {"success": False, "error": f"Service account credentials not found at '{creds_file}'"}
    except Exception as e:
        return {"success": False, "error": f"Auth error: {e}"}

    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.sheet1

        existing = ws.get_all_values()
        if not existing or existing[0] != COLUMNS:
            ws.clear()
            ws.append_row(COLUMNS)
            existing_keys = set()
        else:
            existing_keys = set()
            for row in existing[1:]:
                if row:
                    existing_keys.add(f"{row[0]}|{row[3]}|{row[4]}")

        new_rows = []
        for lead in leads:
            key = f"{lead.name}|{lead.phone}|{lead.website}"
            if key not in existing_keys:
                existing_keys.add(key)
                new_rows.append([getattr(lead, f, "") for f in FIELD_MAP])

        if new_rows:
            ws.append_rows(new_rows, value_input_option="RAW")

        return {"success": True, "appended": len(new_rows), "skipped": len(leads) - len(new_rows)}

    except Exception as e:
        logger.error(f"Sheets error: {e}")
        return {"success": False, "error": str(e)}
