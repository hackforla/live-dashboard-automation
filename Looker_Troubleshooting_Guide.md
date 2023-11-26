# Troubleshooting Looker Dashboard

## Pre-requisites

You would need "Editor" access to the Looker dashboard you are trying to troubleshoot to execute the following instructions.

## Refreshing Data

### Problem Context: Google Sheets Update Not Reflected in Dashboard
You ran the workflow in GitHub Actions, waited for the workflow to finish running, hopped to the Looker dashboard, and noticed, from the last data pull datetime on the dashboard, that the data on the dashboard has not been updated. What happened?

Apparently, Looker updates data on set periods of time. By going to Resource > Manage added data sources > Edit (Data source of choice) > Data freshness, you can choose how frequently you want your data updated. The quickest and most frequent is 15 minutes (default). So that means even when the data in your Google Sheets has changed, the change might not show up immediately if it has not been 15 minutes since Looker's last update. 

![image](https://github.com/hackforla/live-dashboard-automation/assets/76601090/e696ce18-3706-45b8-9ee0-defa68b82a2c)
![image](https://github.com/hackforla/live-dashboard-automation/assets/76601090/627a791d-4402-4c51-8835-f4ae425d466c)

### How to Manually Force a Refresh of the Data?

1. In Edit mode of the Looker dashboard, go to the "View" tab in the navigation bar.

![image](https://github.com/hackforla/live-dashboard-automation/assets/76601090/b9e764e9-6d58-43c5-8f4d-bf6b22353de2)

2. Click "Refresh Data"

![image](https://github.com/hackforla/live-dashboard-automation/assets/76601090/7735d9d2-2a92-460f-9635-0ad52afd893e)

If you check your last data pull datetime on the dashboard now, you should see that it has changed to the recent pull time. You should now have the most updated data reflected in your dashboard.

## Troubleshooting Chart Breakdowns

Sometimes, Looker charts will display an error. If you are sure you have not made any changes that could have caused the chart to break (e.g. chart's data source, columns in Google Sheets data source, etc.), you can try reconnecting the data sources. This also helps to refresh the data should the previous method not work. 

### Reconnecting Data Sources

1. In Edit mode of the Looker dashboard, go to the "Resource" tab in the navigation bar.

![image](https://github.com/hackforla/live-dashboard-automation/assets/76601090/29858951-07dd-41b1-8999-aa0d81304a40)

2. Click "Manage added data resources"

![image](https://github.com/hackforla/live-dashboard-automation/assets/76601090/83b397ed-6616-4602-8285-ee997a98cd91)

3. Choose a data resource to edit by clicking "Edit"

![image](https://github.com/hackforla/live-dashboard-automation/assets/76601090/e30947f9-9f6d-498d-9452-acb85c3e6e09)

4. Click "Edit Connection"

![image](https://github.com/hackforla/live-dashboard-automation/assets/76601090/fb3e1783-461a-436d-acd8-b8f10bac125c)

5. Ensure the right worksheet is selected for connection (it is usually correct) and click the blue "Reconnect" button

![image](https://github.com/hackforla/live-dashboard-automation/assets/76601090/8ae34881-0bfa-4ff5-85bf-a26a2063f302)

6. From there, you can click the blue "Done" button on the next screen and repeat steps 1-6 as needed for other data sources.
