import base64
import json
import os
from urllib.parse import parse_qs, urlparse

import duckdb
import requests
from shillelagh.backends.apsw.db import connect


github_token = os.environ["API_KEY_GITHUB_PROJECTBOARD_DASHBOARD"]
github_user = os.environ["API_TOKEN_USERNAME"]
response = requests.get("https://api.github.com/repos/hackforla/website/issues?state=all", auth=("hackforla", github_token))
issues = response.json()

# Link format
# '<https://api.github.com/repositories/130000551/issues?page=2>; rel="next"'
links = response.headers["Link"]
links = links.split(",")
next_link = links[1].split(";")[0].replace("<", "").replace(">", "").strip()
last = parse_qs(urlparse(next_link).query)["page"][0]
print("Last page:", last)
page = 2
while page <= int(last):
    print(f"Fetching page: {page}/{last}")
    response = requests.get("https://api.github.com/repos/hackforla/website/issues?state=all&page=" + str(page), headers={"Authorization": "Bearer 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"})
    issues.extend(response.json())
    page += 1
print("Number of issues:", len(issues))

for issue in issues:
    issue["labels"] = ", ".join([label["name"] for label in issue["labels"]])

with open("issues.json", "w") as f:
    json.dump(issues, f)

duckdb.read_json("issues.json")
df = duckdb.sql(
    """
            SELECT
                CURRENT_DATE as "Date",
                SUM(CASE WHEN labels LIKE '%role missing%' AND state = 'open' THEN 1 ELSE 0 END) as "Role, Open",
                SUM(CASE WHEN labels LIKE '%role missing%' AND state = 'closed' THEN 1 ELSE 0 END) as "Role, Closed",
                SUM(CASE WHEN labels LIKE '%Complexity: Missing%' AND state = 'open' THEN 1 ELSE 0 END) as "Complexity, Open",
                SUM(CASE WHEN labels LIKE '%Complexity: Missing%' AND state = 'closed' THEN 1 ELSE 0 END) as "Complexity, Closed",
                SUM(CASE WHEN labels LIKE '%size: missing%' AND state = 'open' THEN 1 ELSE 0 END) as "Size, Open",
                SUM(CASE WHEN labels LIKE '%size: missing%' AND state = 'closed' THEN 1 ELSE 0 END) as "Size, Closed",
                SUM(CASE WHEN labels LIKE '%Feature Missing%' AND state = 'open' THEN 1 ELSE 0 END) as "Feature, Open",
                SUM(CASE WHEN labels LIKE '%Feature Missing%' AND state = 'closed' THEN 1 ELSE 0 END) as "Feature, Closed"
            FROM 'issues.json'
        """
).df()
print(df)

key_base64 = os.environ["BASE64_PROJECT_BOARD_GOOGLECREDENTIAL"]
base64_bytes = key_base64.encode("ascii")
key_base64_bytes = base64.b64decode(base64_bytes)
key_content = key_base64_bytes.decode("ascii")

service_account_info = json.loads(key_content)
connection = connect(
    ":memory:",
    adapter_kwargs={
        "gsheetsapi": {
            "service_account_info": service_account_info,
        },
    },
)

cursor = connection.cursor()
SQL = """
INSERT INTO "https://docs.google.com/spreadsheets/d/16yC91C_ZTJoAhG0qVWqpEZ9kREPraubcARfZi9bkFcY/edit#gid=0"
SELECT * FROM df
"""
cursor.execute(SQL)