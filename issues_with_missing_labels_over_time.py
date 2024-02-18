import base64
import json
import os
from urllib.parse import parse_qs, urlparse
import pandas as pd

import duckdb
import requests
from shillelagh.backends.apsw.db import connect


def get_issues(page=1):
    github_token = os.environ["API_KEY_GITHUB_PROJECTBOARD_DASHBOARD"]
    github_user = os.environ["API_TOKEN_USERNAME"]
    response = requests.get(
        f"https://api.github.com/repos/hackforla/website/issues?state=all&page={page}&per_page=100",
        auth=(github_user, github_token),
    )
    if response.status_code != 200:
        raise requests.exceptions.HTTPError(response)
    issues = response.json()
    links = response.headers["Link"]
    links = links.split(",")
    next_link = links[1].split(";")[0].replace("<", "").replace(">", "").strip()
    last = parse_qs(urlparse(next_link).query)["page"][0]
    return issues, last


issues, last = get_issues()

for page in range(2, int(last) + 1):
    print(f"Fetching page: {page}/{last}")
    issues.extend(get_issues(page)[0])
print("Number of issues:", len(issues))

for issue in issues:
    issue["labels"] = ", ".join([label["name"] for label in issue["labels"]])

with open("issues.json", "w") as f:
    json.dump(issues, f)

from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe
from googleapiclient.discovery import build
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import gspread
import base64

scopes = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

key_base64 = os.environ["BASE64_PROJECT_BOARD_GOOGLECREDENTIAL"]
base64_bytes = key_base64.encode("ascii")
key_base64_bytes = base64.b64decode(base64_bytes)
key_content = key_base64_bytes.decode("ascii")

service_account_info = json.loads(key_content)

credentials = service_account.Credentials.from_service_account_info(service_account_info, scopes = scopes)

service_sheets = build('sheets', 'v4', credentials = credentials)

gc = gspread.authorize(credentials)

gauth = GoogleAuth()
drive = GoogleDrive(gauth)

from gspread_dataframe import set_with_dataframe

LabelCheck_GOOGLE_SHEETS_ID = '1-ltg0qMeZSgOnqrCU0nKUDQd1JOXTMWrNTK63VZjXdk'

LabelCheck_sheet_name = 'Official GitHub Labels'

gs = gc.open_by_key(LabelCheck_GOOGLE_SHEETS_ID)

LabelCheck_worksheet = gs.worksheet(LabelCheck_sheet_name)

LC_spreadsheet_data = LabelCheck_worksheet.get_all_records()
LC_df = pd.DataFrame.from_dict(LC_spreadsheet_data)

role_missing_label = str(list(LC_df[(LC_df["missing_series?"] == "Yes") & (LC_df["label_series"] == "role")]["label_name"]))[2:-2]
size_missing_label = str(list(LC_df[(LC_df["missing_series?"] == "Yes") & (LC_df["label_series"] == "size")]["label_name"]))[2:-2]
complexity_missing_label = str(list(LC_df[(LC_df["missing_series?"] == "Yes") & (LC_df["label_series"] == "complexity")]["label_name"]))[2:-2]
feature_missing_label = str(list(LC_df[(LC_df["missing_series?"] == "Yes") & (LC_df["label_series"] == "feature")]["label_name"]))[2:-2]

df = duckdb.sql(
    """
        SELECT
            CURRENT_DATE as "Date",
            SUM(CASE WHEN labels LIKE '%{0}%' AND state = 'open' THEN 1 ELSE 0 END) as "Role, Open",
            SUM(CASE WHEN labels LIKE '%{0}%' AND state = 'closed' THEN 1 ELSE 0 END) as "Role, Closed",
            SUM(CASE WHEN labels LIKE '%{1}%' AND state = 'open' THEN 1 ELSE 0 END) as "Complexity, Open",
            SUM(CASE WHEN labels LIKE '%{1}%' AND state = 'closed' THEN 1 ELSE 0 END) as "Complexity, Closed",
            SUM(CASE WHEN labels LIKE '%{2}%' AND state = 'open' THEN 1 ELSE 0 END) as "Size, Open",
            SUM(CASE WHEN labels LIKE '%{2}%' AND state = 'closed' THEN 1 ELSE 0 END) as "Size, Closed",
            SUM(CASE WHEN labels LIKE '%{3}%' AND state = 'open' THEN 1 ELSE 0 END) as "Feature, Open",
            SUM(CASE WHEN labels LIKE '%{3}%' AND state = 'closed' THEN 1 ELSE 0 END) as "Feature, Closed"
        FROM 'issues.json'
        WHERE (pull_request IS NULL AND labels NOT LIKE '%Ignore%');
    """.format(role_missing_label, complexity_missing_label, size_missing_label, feature_missing_label)
).df()
df["Date"] = df["Date"].dt.strftime("%m-%d-%Y")

connection = connect(
    ":memory:",
    adapter_kwargs={
        "gsheetsapi": {
            "service_account_info": service_account_info,
        },
    },
)

SQL = """
INSERT INTO "https://docs.google.com/spreadsheets/d/1aJ0yHkXYMWTtMz6eEeolTLmAQOBc2DyptmR5SAmUrjM/edit#gid=1516123154" 
SELECT * FROM df;
"""
connection.execute(SQL)
# kind of a hack to get the connection to close and prevent a segfault
connection = connect(":memory:")
