import base64
import json
import os
from urllib.parse import parse_qs, urlparse

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
df["Date"] = df["Date"].dt.strftime("%m-%d-%Y")
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

connection.execute(
    """
        INSERT INTO "https://docs.google.com/spreadsheets/d/1aJ0yHkXYMWTtMz6eEeolTLmAQOBc2DyptmR5SAmUrjM/edit#gid=1516123154" 
        SELECT * FROM df;
    """
)
# kind of a hack to get the connection to close and prevent a segfault
connection = connect(":memory:")
