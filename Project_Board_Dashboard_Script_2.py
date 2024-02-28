#!/usr/bin/env python
# coding: utf-8

# In[1]:


# import libraries

import os
import requests
import pandas as pd
import numpy as np
import time
import json
import re
from urllib.parse import parse_qs, urlparse
from datetime import datetime
import pytz


# # Set Up for API Calls

# In[2]:


GitHub_token = os.environ["API_KEY_GITHUB_PROJECTBOARD_DASHBOARD"]
user = os.environ['API_TOKEN_USERNAME']


# # Get Cards in Project Board Columns

# In[3]:


def get_cards(url):
    complete_df = pd.DataFrame()
    
    # use impossible number of 1000 (99900 issues in project board column) to ensure issues from all page results are retrieved
    for i in range(1, 1000):
        params = {"per_page": 100, "page": i}
        response = requests.get(url, auth=(user, GitHub_token), params = params)
        df = pd.DataFrame(response.json())
        if len(df) > 0:
            complete_df = pd.concat([complete_df, df], ignore_index = True)
        else:
            break
        
    return complete_df


# In[4]:


# Ice Box
ice_box = get_cards('https://api.github.com/projects/columns/7198227/cards') 

# ER Column
er = get_cards('https://api.github.com/projects/columns/19403960/cards') 

# New Issue Approval Column
newissue_approval = get_cards('https://api.github.com/projects/columns/15235217/cards') 

# Prioritized Backlog Column
prioritized_backlog = get_cards('https://api.github.com/projects/columns/7198257/cards') 

# "In Progress (Actively Working)" Column
in_progress = get_cards('https://api.github.com/projects/columns/7198228/cards') 

# Questions/In Review Column
questions = get_cards('https://api.github.com/projects/columns/8178690/cards') 

# QA Column
QA = get_cards('https://api.github.com/projects/columns/15490305/cards') 

# UAT Column
UAT = get_cards('https://api.github.com/projects/columns/17206624/cards') 

# "QA - senior review" Column
QA_review = get_cards('https://api.github.com/projects/columns/19257634/cards') 


# # Prep Work: Create Variables with List of Main Complexity Labels and Status Breakdowns for Dashboard

# In[5]:


complexity_labels = ["Complexity: Prework", "Complexity: Missing", "Complexity: Large", 
                     "Complexity: Extra Large", "Complexity: Small", "good first issue", 
                     "Complexity: Medium", "Complexity: See issue making label", "prework", 
                     "Complexity: Good second issue"]


# In[6]:


extra_breakdown = ["Draft", "2 weeks inactive", "ready for product", 
                   "ready for dev lead", "Ready for Prioritization"]


# # Get Issue Links from Cards in Project Board Columns

# In[7]:


# Create function for cleaning and getting datasets to reduce script length

def cleaning(df_name):
    issues = list(df_name[~df_name['content_url'].isna()]['content_url']) 
    issues_df = pd.DataFrame()
    
    try:
        for url in issues:
            response = requests.get(url, auth=(user, GitHub_token))
            issue_data = pd.json_normalize(response.json())
            issues_df = pd.concat([issues_df, issue_data], ignore_index = True)
    except ValueError:
        time.sleep(3600)
        for url in issues:
            response = requests.get(url, auth=(user, GitHub_token))
            issue_data = pd.json_normalize(response.json())
            issues_df = pd.concat([issues_df, issue_data], ignore_index = True)
    
    # Get current time in LA
    datetime_LA = datetime.now(pytz.timezone('US/Pacific'))
    
    # Format the time as a string and add it in Runtime column
    issues_df["Runtime"] = "LA time: " + datetime_LA.strftime("%m/%d/%Y %H:%M:%S")
    
    # Drop unneccessary columns
    drop_columns = [x for x in issues_df.columns if re.match("url|id|closed|state|assignee|user|reactions|milestone|number|locked|comments|created|updated|author_association|active_lock_reason|body|performed_via_github_app", x)]
    issues_df.drop(columns = drop_columns, inplace = True)
    
    return issues_df


# In[8]:


def cleaning2(df_name):
    # Flatten labels column
    flatten = df_name.to_json(orient = "records")
    parsed = json.loads(flatten)
    
    # Drop redundant labels columns
    issues_df2 = pd.json_normalize(parsed, record_path = ["labels"], record_prefix = "labels.", meta = ["Runtime", "html_url", "title"])
    issues_df2.drop(columns = ['labels.id', 'labels.node_id', 'labels.url', 'labels.description', 'labels.color', 'labels.default'], inplace = True)
    
    # Remove issues with ignore labels in column
    if len([label for label in issues_df2["labels.name"].unique() if re.search('ignore', label.lower())])>0:
        remove = list(issues_df2[issues_df2["labels.name"].str.contains("gnore")]["html_url"])
        issues_df2 = issues_df2[~issues_df2["html_url"].isin(remove)]
    else:
        remove = []
        
    # Finishing touches for icebox dataset (include issues with no labels)
    difference = list(set(df_name["html_url"]).difference(set(issues_df2["html_url"])))
    no_labels = list(set(difference).difference(set(remove)))
    no_labels_df = df_name[df_name["html_url"].isin(no_labels)][["Runtime", "html_url", "title"]]
    no_labels_df["labels.name"] = ""
    no_labels_df = no_labels_df[["labels.name", "Runtime", "html_url", "title"]]

    issues_df3 = pd.concat([issues_df2, no_labels_df], ignore_index = True)
    
    return issues_df2, issues_df3


# In[9]:


def final_cleaning(df_name):
    # retain only labels with "role" in it or complexity labels, and "Draft", "ready for product", "ready for prioritization", "ready for dev lead"
    final = df_name[(df_name["labels.name"].str.contains("role") | df_name["labels.name"].isin(complexity_labels) | 
                              df_name["labels.name"].isin(extra_breakdown) | df_name["labels.name"].str.contains("Ready", case=False))]

    # Make combined label for issues with front and backend labels
    wdataset = final[final["labels.name"].str.contains("front end") | final["labels.name"].str.contains("back end")]
    wdataset["front/back end count"] = wdataset.groupby(["html_url", "title"])["labels.name"].transform("count")

    final.loc[list(wdataset[wdataset["front/back end count"] == 2].index), "labels.name"] = "role: front end and backend/DevOps"

    final.drop_duplicates(inplace = True)

    final2 = final[["Runtime", "labels.name", "html_url", "title"]]
    
    return final2


# In[10]:


# Get Datasets for Icebox Column
icebox_issues_df = cleaning(ice_box)
icebox_issues_df2, icebox_issues_df3 = cleaning2(icebox_issues_df)
icebox_issues_df3["Project Board Column"] = "1 - Icebox"
final_icebox2 = final_cleaning(icebox_issues_df2)

# Get Datasets for Emergent Request Column
ER_issues_df = cleaning(er)
ER_issues_df2, ER_issues_df3 = cleaning2(ER_issues_df)
ER_issues_df3["Project Board Column"] = "2- ER"
final_ER2 = final_cleaning(ER_issues_df2)

# Get Datasets for New Issue Approval Column
NIA_issues_df = cleaning(newissue_approval)
NIA_issues_df2, NIA_issues_df3 = cleaning2(NIA_issues_df)
NIA_issues_df3["Project Board Column"] = "3 - New Issue Approval"
final_NIA2 = final_cleaning(NIA_issues_df2)

# Get Datasets for Prioritized Backlog Column
pb_issues_df = cleaning(prioritized_backlog)
pb_issues_df2, pb_issues_df3 = cleaning2(pb_issues_df)
pb_issues_df3["Project Board Column"] = "4 - Prioritized Backlog"
final_pb2 = final_cleaning(pb_issues_df2)

# Get Datasets for In Progress Column
ip_df = cleaning(in_progress)
ip_df2, ip_issues_df3 = cleaning2(ip_df)
ip_issues_df3["Project Board Column"] = "5 - In Progress"
final_ip2 = final_cleaning(ip_df2)

# Get Datasets for Questions/In Review Column
questions_issues_df = cleaning(questions)
questions_issues_df2, questions_issues_df3 = cleaning2(questions_issues_df)
questions_issues_df3["Project Board Column"] = "6 - Questions/ In Review"
final_questions2 = final_cleaning(questions_issues_df2)

# Get Datasets for QA Column
QA_issues_df = cleaning(QA)
QA_issues_df2, QA_issues_df3 = cleaning2(QA_issues_df)
QA_issues_df3["Project Board Column"] = "7 - QA"
final_QA2 = final_cleaning(QA_issues_df2)

# Get Datasets for UAT Column
UAT_issues_df = cleaning(UAT)
UAT_issues_df2, UAT_issues_df3 = cleaning2(UAT_issues_df)
UAT_issues_df3["Project Board Column"] = "8 - UAT"
final_UAT2 = final_cleaning(UAT_issues_df2)

# Get Datasets for QA - Senior Review Column
QA_review_issues_df = cleaning(QA_review)
QA_review_issues_df2, QA_review_issues_df3 = cleaning2(QA_review_issues_df)
QA_review_issues_df3["Project Board Column"] = "9 - QA (senior review)"
final_QA_review2 = final_cleaning(QA_review_issues_df2)


# # Create Data Source for Dashboard

# In[11]:


from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe
from googleapiclient.discovery import build
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import gspread
import base64


# In[12]:


scopes = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']


# In[13]:


## Read in offical GitHub labels from Google spreadsheet for weekly label check table

key_base64 = os.environ["BASE64_PROJECT_BOARD_GOOGLECREDENTIAL"]
base64_bytes = key_base64.encode('ascii')
key_base64_bytes = base64.b64decode(base64_bytes)
key_content = key_base64_bytes.decode('ascii')

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


# ## Create Functions for Data Manipulation 

# ### Add Columns for Counting Number of Issues with Specific Labels Indicating Status

# In[14]:


# Columns to add:
# 1) Draft, 2) 2 weeks inactive, 3) ready for product, 4) ready for dev lead, 5) Ready for Prioritization

def add_known_status_col(df_name, project_board_column):
    role = df_name[df_name["labels.name"].str.contains("role")]
    complexity = df_name[df_name["labels.name"].isin(complexity_labels)]

    dataset = role.merge(complexity, how = "outer", on = ["html_url", "title"])
    dataset.rename(columns = {"labels.name_x": "Role Label", "labels.name_y": "Complexity Label", "Runtime_x":"Runtime"}, inplace = True)

    runtime_nulls_loc = dataset[dataset["Runtime"].isna()].index
    dataset.loc[runtime_nulls_loc, "Runtime"]= dataset[~dataset["Runtime"].isna()].iloc[0,0]
    dataset.drop(columns = ["Runtime_y"], inplace = True)

    for label in extra_breakdown:
        if len(df_name[df_name["labels.name"]==label]) > 0:
            col_label = df_name[df_name["labels.name"]==label][["html_url", "title", "labels.name"]]
            dataset = dataset.merge(col_label, how = "left", on = ["html_url", "title"])
            dataset["labels.name"] = dataset["labels.name"].map(lambda x: 1 if x == label else 0)
            dataset.rename(columns = {"labels.name": label}, inplace = True)
        elif len(df_name[df_name["labels.name"]==label]) == 0:
            dataset[label] = 0
            
    dataset["Project Board Column"] = project_board_column
    
    dataset2 = dataset[["Project Board Column", "Runtime", "Role Label", "Complexity Label", "html_url", "title", "Draft", "2 weeks inactive", "ready for product", "ready for dev lead", "Ready for Prioritization"]]
        
    return dataset2


# ### Add Column for Counting Number of Issues with Unknown Status

# In[15]:


def add_unknown_status_col(copy_df, df_name, known_status_regex):
    # Create a column to identify issues with unknown status
    unknown_status_wdataset = copy_df.copy()
    unknown_status_wdataset["Known Status"] = unknown_status_wdataset["labels.name"].map(lambda x: 1 if (re.search(known_status_regex, str(x).lower())) else 0)
    known_status_issues = list(unknown_status_wdataset[unknown_status_wdataset["Known Status"] == 1]["html_url"].unique())
    df_name["Unknown Status"] = df_name["html_url"].map(lambda x: 0 if x in known_status_issues else 1)
    
    return df_name

# r"(ready|draft|^dependency$)" for icebox
# r"(ready|draft)" for all other columns


# ### Add Column with Link to Issues with Unknown Status

# In[16]:


# Transform all ready series labels and add them to the status link
ready_labels = list(LC_df[LC_df["label_series"] == "ready"]["label_name"].unique())
ready_labels_append = ""
for label in ready_labels:
    ready_labels_transformed = label.lower().replace(":", "%3A").replace(" ", "+")
    ready_labels_append = ready_labels_append+"+-label%3A%22"+ ready_labels_transformed+"%22"

# Transform all ignore series labels and add them to the status link
ignore_labels = list(LC_df[LC_df["label_series"] == "ignore"]["label_name"].unique())
ignore_labels_append = ""
for label in ignore_labels:
    ignore_labels_transformed = label.lower().replace(":", "%3A").replace(" ", "+")
    ignore_labels_append = ignore_labels_append+"+-label%3A%22"+ ignore_labels_transformed+"%22"
        
transformed_readyignorelabels = ready_labels_append + ignore_labels_append


# In[17]:


icebox_static_link_base = 'https://github.com/hackforla/website/projects/7?card_filter_query=-label%3Adraft%22+-label%3A%22dependency%22'+ transformed_readyignorelabels
other_static_link_base = 'https://github.com/hackforla/website/projects/7?card_filter_query=-label%3Adraft' + transformed_readyignorelabels


# In[18]:


# Create nested dictionary for static links

def add_unknownstatus_link(base_link, df_name):
    unique_roles = [x for x in df_name["Role Label"].unique() if pd.isna(x) == False]
    unique_roles2 = [x for x in unique_roles if x != "role: front end and backend/DevOps"]
    unique_complexity = [x for x in df_name["Complexity Label"].unique() if pd.isna(x) == False]  

    link_dict = { }

    for role in unique_roles2:
        link_dict[role] = {}
        for complexity in unique_complexity:
            role_transformed = role.lower().replace(":", "%3A").replace(" ", "+")
            complexity_transformed = complexity.lower().replace(":", "%3A").replace(" ", "+")
            link_dict[role][complexity] = base_link+"+label%3A%22"+role_transformed+"%22"+"+label%3A%22"+complexity_transformed+"%22"

    link_dict["role: front end and backend/DevOps"] = {}     
    for complexity in unique_complexity:
        frontend_transformed = "role: front end".lower().replace(":", "%3A").replace(" ", "+")
        backend_transformed = "role: back end/devOps".lower().replace(":", "%3A").replace(" ", "+")
        complexity_transformed = complexity.lower().replace(":", "%3A").replace(" ", "+")
        link_dict["role: front end and backend/DevOps"][complexity] = base_link+"+label%3A%22"+frontend_transformed+"%22"+"+label%3A%22"+backend_transformed+"%22"+"+label%3A%22"+complexity_transformed+"%22"

    df_name["Role-based Link for Unknown Status"] = ""
    for role in link_dict.keys():
        df = df_name[df_name["Role Label"] == role]
        for complexity in link_dict[list(link_dict.keys())[0]].keys(): #same for all roles
            df2 = df[df["Complexity Label"] == complexity]
            indexes = df2.index
            df_name.loc[indexes, "Role-based Link for Unknown Status"] = link_dict[role][complexity]
            
    return df_name


# ### Apply the Functions to Each Project Board Column Dataset

# In[23]:


# Icebox
icebox_dataset2 = add_known_status_col(final_icebox2, "1 - Icebox")
icebox_dataset2 = add_unknown_status_col(icebox_issues_df2, icebox_dataset2, r"(ready|draft|^dependency$)")
icebox_dataset2 = add_unknownstatus_link(icebox_static_link_base, icebox_dataset2)

# Emergent Request
ER_dataset2 = add_known_status_col(final_ER2, "2 - ER")
ER_dataset2 = add_unknown_status_col(ER_issues_df2, ER_dataset2, r"(ready|draft)")
ER_dataset2 = add_unknownstatus_link(other_static_link_base, ER_dataset2)

# New Issue Approval
NIA_dataset2 = add_known_status_col(final_NIA2, "3 - New Issue Approval")
NIA_dataset2 = add_unknown_status_col(NIA_issues_df2, NIA_dataset2, r"(ready|draft)")
NIA_dataset2 = add_unknownstatus_link(other_static_link_base, NIA_dataset2)

# Prioritized Backlog
pb_dataset2 = add_known_status_col(final_pb2, "4 - Prioritized Backlog")
pb_dataset2 = add_unknown_status_col(pb_issues_df2, pb_dataset2, r"(ready|draft)")
pb_dataset2 = add_unknownstatus_link(other_static_link_base, pb_dataset2)

# In Progress
IP_dataset2 = add_known_status_col(final_ip2, "5 - In Progress")
IP_dataset2 = add_unknown_status_col(ip_df2, IP_dataset2, r"(ready|draft)")
IP_dataset2 = add_unknownstatus_link(other_static_link_base, IP_dataset2)

# Questions/In Review
Q_dataset2 = add_known_status_col(final_questions2, "6 - Questions/ In Review")
Q_dataset2 = add_unknown_status_col(questions_issues_df2, Q_dataset2, r"(ready|draft)")
Q_dataset2 = add_unknownstatus_link(other_static_link_base, Q_dataset2)

# QA
QA_dataset2 = add_known_status_col(final_QA2, "7 - QA")
QA_dataset2 = add_unknown_status_col(QA_issues_df2, QA_dataset2, r"(ready|draft)")
QA_dataset2 = add_unknownstatus_link(other_static_link_base, QA_dataset2)

# UAT
UAT_dataset2 = add_known_status_col(final_UAT2, "8 - UAT")
UAT_dataset2 = add_unknown_status_col(UAT_issues_df2, UAT_dataset2, r"(ready|draft)")
UAT_dataset2 = add_unknownstatus_link(other_static_link_base, UAT_dataset2)

# QA - senior review
QA_review_dataset2 = add_known_status_col(final_QA_review2, "9 - QA (senior review)")
QA_review_dataset2 = add_unknown_status_col(QA_review_issues_df2, QA_review_dataset2, r"(ready|draft)")
QA_review_dataset2 = add_unknownstatus_link(other_static_link_base, QA_review_dataset2)


# ## Combine Data from All Project Board Columns

# In[24]:


# Concat the dataset and see whether dashboard would work
final_dataset = pd.concat([icebox_dataset2, ER_dataset2, NIA_dataset2, pb_dataset2, IP_dataset2, Q_dataset2, QA_dataset2, UAT_dataset2, QA_review_dataset2], ignore_index = True)

final_dataset.loc[final_dataset[final_dataset["Complexity Label"] == "good first issue"].index, "Complexity Label"] = "1 - good first issue"
final_dataset.loc[final_dataset[final_dataset["Complexity Label"] == "Complexity: Small"].index, "Complexity Label"] = "2 - Complexity: Small"
final_dataset.loc[final_dataset[final_dataset["Complexity Label"] == "Complexity: Medium"].index, "Complexity Label"] = "3 - Complexity: Medium"
final_dataset.loc[final_dataset[final_dataset["Complexity Label"] == "Complexity: Large"].index, "Complexity Label"] = "4 - Complexity: Large"
final_dataset.loc[final_dataset[final_dataset["Complexity Label"] == "Complexity: Extra Large"].index, "Complexity Label"] = "5 - Complexity: Extra Large"


# ## Create Anomaly Detection Dataset

# In[25]:


# Concat the dataframes from all columns

anomaly_detection = pd.concat([icebox_issues_df3, ER_issues_df3, NIA_issues_df3, pb_issues_df3, ip_issues_df3, questions_issues_df3, QA_issues_df3, UAT_issues_df3, QA_review_issues_df3], ignore_index = True)
anomaly_detection["keep"] = anomaly_detection["labels.name"].map(lambda x: 1 if (re.search(r"(size|feature|role|complexity|good first issue|prework|^$)", str(x).lower())) else 0)
anomaly_detection_df = anomaly_detection[anomaly_detection["keep"] == 1]
anomaly_detection_df.drop(columns = ["keep"], inplace = True)

outdated_labels = list(LC_df[LC_df["in_use?"] == "No"]["label_name"].unique())
official_active_labels = list(set(list(LC_df["label_name"])).difference(set(outdated_labels)))

anomaly_detection_df["labels_need_action"] = anomaly_detection_df["labels.name"].map(lambda x: 1 if x not in official_active_labels else 0)
anomaly_detection_df["outdated_label"] = anomaly_detection_df["labels.name"].map(lambda x: 1 if x in outdated_labels else 0)
anomaly_detection_df["unknown_label"] = anomaly_detection_df["labels.name"].map(lambda x: 1 if (x not in official_active_labels and x not in outdated_labels) else 0)
anomaly_detection_df["Label Transformed"] = anomaly_detection_df["labels.name"].map(lambda x: x.lower().replace(":", "%3A").replace(" ", "+") if pd.isna(x) == False else x)
anomaly_detection_df["Link for Quick Correction"] = anomaly_detection_df["Label Transformed"].map(lambda x: "https://github.com/hackforla/website/issues?q=is%3Aissue+label%3A"+str(x) if pd.isna(x) == False else np.nan)

anomaly_detection_df.drop(columns = ["Label Transformed"], inplace = True)

anomaly_detection_df = anomaly_detection_df[["Project Board Column", "Runtime", "html_url", "title", "labels.name", "labels_need_action", "outdated_label", "unknown_label", "Link for Quick Correction"]]

# In[49]:

anomaly_detection_df2_base = anomaly_detection_df.copy()
anomaly_detection_df2_base.drop(columns = ["labels_need_action"], inplace = True)
anomaly_detection_df2_base.drop(columns = ["outdated_label"], inplace = True)
anomaly_detection_df2_base.drop(columns = ["unknown_label"], inplace = True)
anomaly_detection_df2_base.drop(columns = ["Link for Quick Correction"], inplace = True)

# Includes official labels that are current and outdated
official_complexity = list(LC_df[LC_df["label_series"] == "complexity"]["label_name"])
official_feature = list(LC_df[LC_df["label_series"] == "feature"]["label_name"])
official_role = list(LC_df[LC_df["label_series"] == "role"]["label_name"])
official_size = list(LC_df[LC_df["label_series"] == "size"]["label_name"])

anomaly_detection_df2_base["Complexity Label"] = anomaly_detection_df2_base["labels.name"].map(lambda x: 1 if x in official_complexity else 0)
anomaly_detection_df2_base["Feature Label"] = anomaly_detection_df2_base["labels.name"].map(lambda x: 1 if x in official_feature else 0)
anomaly_detection_df2_base["Role Label"] = anomaly_detection_df2_base["labels.name"].map(lambda x: 1 if x in official_role else 0)
anomaly_detection_df2_base["Size Label"]= anomaly_detection_df2_base["labels.name"].map(lambda x: 1 if x in official_size else 0)

complexity_missing_series = list(LC_df[(LC_df["label_series"] == "complexity") & (LC_df["missing_series?"] == "Yes")]["label_name"])[0]
feature_missing_series = list(LC_df[(LC_df["label_series"] == "feature") & (LC_df["missing_series?"] == "Yes")]["label_name"])[0]
role_missing_series = list(LC_df[(LC_df["label_series"] == "role") & (LC_df["missing_series?"] == "Yes")]["label_name"])[0]
size_missing_series = list(LC_df[(LC_df["label_series"] == "size") & (LC_df["missing_series?"] == "Yes")]["label_name"])[0]

anomaly_detection_df2_base["Complexity Missing Label"] = anomaly_detection_df2_base["labels.name"].map(lambda x: 1 if x == complexity_missing_series else 0)
anomaly_detection_df2_base["Feature Missing Label"] = anomaly_detection_df2_base["labels.name"].map(lambda x: 1 if x == feature_missing_series else 0)
anomaly_detection_df2_base["Role Missing Label"] = anomaly_detection_df2_base["labels.name"].map(lambda x: 1 if x == role_missing_series else 0)
anomaly_detection_df2_base["Size Missing Label"]= anomaly_detection_df2_base["labels.name"].map(lambda x: 1 if x == size_missing_series else 0)
 
anomaly_detection_df2 = anomaly_detection_df2_base.groupby(["Project Board Column", "Runtime", "html_url", "title"])[["Complexity Label", "Feature Label", "Role Label", "Size Label", "Complexity Missing Label", "Feature Missing Label", "Role Missing Label", "Size Missing Label"]].sum().reset_index()

anomaly_detection_df2["Complexity defined label"] = anomaly_detection_df2["Complexity Label"]-anomaly_detection_df2["Complexity Missing Label"]
anomaly_detection_df2["Feature defined label"] = anomaly_detection_df2["Feature Label"]-anomaly_detection_df2["Feature Missing Label"]
anomaly_detection_df2["Role defined label"] = anomaly_detection_df2["Role Label"]-anomaly_detection_df2["Role Missing Label"]
anomaly_detection_df2["Size defined label"] = anomaly_detection_df2["Size Label"]-anomaly_detection_df2["Size Missing Label"]

anomaly_detection_df2_join = anomaly_detection_df2_base[anomaly_detection_df2_base["Role Label"] == 1][["html_url", "labels.name"]]
anomaly_detection_df2 = anomaly_detection_df2.merge(anomaly_detection_df2_join, how = "left", on = ["html_url"])
epic_issues = list(anomaly_detection[anomaly_detection['labels.name'] == 'epic']['html_url'].unique())
ER_issues = list(anomaly_detection[anomaly_detection['labels.name'] == 'ER']['html_url'].unique())
anomaly_detection_df2['Epic Issue?'] = anomaly_detection_df2['html_url'].map(lambda x: 1 if x in epic_issues else 0)
anomaly_detection_df2['ER Issue?'] = anomaly_detection_df2['html_url'].map(lambda x: 1 if x in ER_issues else 0)

# change role label of issues with front end and back end labels
anomaly_detection_wdataset = anomaly_detection_df2[anomaly_detection_df2["labels.name"].str.contains("front end") | anomaly_detection_df2["labels.name"].str.contains("back end")]
anomaly_detection_wdataset["front/back end count"] = anomaly_detection_wdataset.groupby(["html_url", "title"])["labels.name"].transform("count")

anomaly_detection_df2.loc[list(anomaly_detection_wdataset[anomaly_detection_wdataset["front/back end count"] == 2].index), "labels.name"] = "role: front end and backend/DevOps"

# Drop duplicates that have been created by the change
anomaly_detection_df2.drop_duplicates(inplace = True)


# ## Create dataset that detects issues with missing dependencies in icebox

# In[26]:


missing_dependency_label = list(LC_df[(LC_df["label_series"] == "dependency") & (LC_df["missing_series?"] == "Yes")]["label_name"])[0]
missing_dependency = anomaly_detection[(anomaly_detection["labels.name"] == missing_dependency_label) & (anomaly_detection["Project Board Column"] == "1 - Icebox")]
icebox_issues = list(anomaly_detection[anomaly_detection["Project Board Column"] == "1 - Icebox"]["html_url"].unique())
icebox_issues_with_dependency = list(anomaly_detection[(anomaly_detection["Project Board Column"] == "1 - Icebox") & (anomaly_detection["labels.name"] == "Dependency")]["html_url"].unique())
icebox_issues_without_dependency = list(set(icebox_issues).difference(set(icebox_issues_with_dependency)))
no_dependency = anomaly_detection[anomaly_detection["html_url"].isin(icebox_issues_without_dependency)]
missing_dependency = pd.concat([missing_dependency, no_dependency], ignore_index = True)

missing_dependency = missing_dependency.iloc[:, [1,4,2,3,0]]

if len(missing_dependency) == 0:
    missing_dependency.loc[0] = [" "," "," "," "," "]
else:
    missing_dependency


# ## Create dataset with issues that have labels in missing series (to be joined for anomaly report in Looker)

# In[27]:


missingseries_labels = list(LC_df[LC_df["missing_series?"] == "Yes"]["label_name"])
issues_w_missinglabels = anomaly_detection[anomaly_detection['labels.name'].isin(missingseries_labels)][["Project Board Column", "html_url", "title", "labels.name"]]


# ## Create new table that draws in all issues with ER title that do not have ER label

# In[28]:


ER_label_check = ER_issues_df3.copy()
ER_label_check["ER Label?"] = ER_label_check['html_url'].map(lambda x: 1 if x in ER_issues else 0)
No_ER_label = ER_label_check[ER_label_check["ER Label?"] == 0]
No_ER_label_filtered = No_ER_label[~No_ER_label["title"].str.contains("ER from TLDL", case = False)]
No_ER_label_filtered.drop(columns = ["labels.name"], inplace = True)
No_ER_label_filtered.drop_duplicates(inplace = True)

if len(No_ER_label_filtered) == 0:
    No_ER_label_filtered = pd.DataFrame(columns = ["Runtime", "html_url", "title", "Project Board Column", "ER Label?", "state"])
    No_ER_label_filtered.loc[0] = [" "," "," "," "," "," "]
else:
    no_ERlabel_issuestate = pd.DataFrame()

    for url in No_ER_label_filtered["html_url"]:
        issue_number = re.findall(r'[0-9]+$', url)[0]
        html = "https://api.github.com/repos/hackforla/website/issues/"+issue_number
        response = requests.get(html, auth=(user, GitHub_token))
        df = pd.json_normalize(response.json())[["html_url", "state"]]
        no_ERlabel_issuestate = pd.concat([no_ERlabel_issuestate, df], ignore_index = True)

    No_ER_label_filtered = No_ER_label_filtered.merge(no_ERlabel_issuestate, how = "left", on = "html_url")


# ## Create a table that displays issues with Complexity: Missing label with first comment being an empty description

# In[29]:


excluded_columns = ["1 - Icebox", "2 - ER", "3 - New Issue Approval"]
empty_description_search = final_dataset[(~final_dataset["Project Board Column"].isin(excluded_columns)) & (final_dataset["Complexity Label"] == "Complexity: Missing")]

empty_comment = []

for url in empty_description_search["html_url"]:
    issue_number = re.findall(r'[0-9]+$', url)[0]
    html = "https://api.github.com/repos/hackforla/website/issues/"+issue_number+"/timeline"
    response = requests.get(html, auth=(user, GitHub_token))
    df = pd.DataFrame(response.json())
    if ("body" not in list(df.columns)):
        if (df.iloc[0]["actor"]['login'] != 'github-actions[bot]' and df.iloc[0]["event"] == "cross-referenced"):
            empty_comment.append(url)
    elif ("body" in list(df.columns)):
        if (pd.isna(df.iloc[0]["body"]) == True and df.iloc[0]["actor"]['login'] != 'github-actions[bot]' and df.iloc[0]["event"] == "cross-referenced"):
            empty_comment.append(url)
    else:
        continue

complexity_missing_emptycomment = final_dataset[final_dataset["html_url"].isin(empty_comment)][["Project Board Column", "Role Label", "Complexity Label", "html_url", "title"]]
if len(complexity_missing_emptycomment) == 0:
    complexity_missing_emptycomment.loc[0] = [" "," "," "," "," "]
else:
    complexity_missing_emptycomment


# # Send Data to Google Sheets

# In[30]:


### Send to Google Sheet

Main_GOOGLE_SHEETS_ID = '1aJ0yHkXYMWTtMz6eEeolTLmAQOBc2DyptmR5SAmUrjM'

sheet_name1 = 'Dataset 2'

gs = gc.open_by_key(Main_GOOGLE_SHEETS_ID)

worksheet1 = gs.worksheet(sheet_name1)

worksheet1.clear()

# Insert dataframe of issues into Google Sheet

set_with_dataframe(worksheet = worksheet1, dataframe = final_dataset, include_index = False, include_column_header = True, resize = True)

sheet_name2 = 'Labels to note'
worksheet2 = gs.worksheet(sheet_name2)
worksheet2.clear()
set_with_dataframe(worksheet = worksheet2, dataframe = anomaly_detection_df, include_index = False, include_column_header = True, resize = True)

sheet_name3 = 'Missing Labels'
worksheet3 = gs.worksheet(sheet_name3)
worksheet3.clear()
set_with_dataframe(worksheet = worksheet3, dataframe = anomaly_detection_df2, include_index = False, include_column_header = True, resize = True)

sheet_name4 = 'Issues with Missing Series Labels'
worksheet4 = gs.worksheet(sheet_name4)
worksheet4.clear()
set_with_dataframe(worksheet = worksheet4, dataframe = issues_w_missinglabels, include_index = False, include_column_header = True, resize = True)

sheet_name5 = 'Icebox Issues with Missing or No Dependency'
worksheet5 = gs.worksheet(sheet_name5)
worksheet5.clear()
set_with_dataframe(worksheet = worksheet5, dataframe = missing_dependency, include_index = False, include_column_header = True, resize = True)

sheet_name6 = 'Missing ER Label'
worksheet6 = gs.worksheet(sheet_name6)
worksheet6.clear()
set_with_dataframe(worksheet = worksheet6, dataframe = No_ER_label_filtered, include_index = False, include_column_header = True, resize = True)

sheet_name7 = 'Complexity Missing Issues with Empty 1st Comment'
worksheet7 = gs.worksheet(sheet_name7)
worksheet7.clear()
set_with_dataframe(worksheet = worksheet7, dataframe = complexity_missing_emptycomment, include_index = False, include_column_header = True, resize = True)


# In[ ]:




