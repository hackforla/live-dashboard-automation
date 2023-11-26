# Purpose of Repository

This repository is created to drive automation efforts for informing and updating Hack for LA's Looker dashboards on schedule or on demand:
- GitHub Dashboard: HackforLA.org Website Team ([Issue 4921](https://github.com/hackforla/website/issues/4921))
- The Onboarding Analysis portion of [Hack for LA's Looker dashboard](https://www.hackforla.org/dashboard/)([Issue 4152](https://github.com/hackforla/website/issues/4152))

# Context of Projects using This Repository

## Hack for LA Onboarding Impact Analysis 

Refer to [Issue 4152](https://github.com/hackforla/website/issues/4152)

The Onboarding Impact Analysis is a data analytics project of Hack for LA to support decision-making to mazimize return-on-investment for onboarding efforts. Through this project, we analyze issues completed by onboarded developers (identified through closed prework issues) and aim to identify patterns and insights from new developer behavior through various metrics and data visualizations in a Looker dashboard available on the Hack for LA website. Automatic update to analysis in Looker dashboard as new data comes in would be desirable.

### Purpose of Analysis
By joining Hack for LA, new developers are provided basic training during onboarding and opportunities to improve their developer skills by working on volunteer projects made available by Hack for LA. A lot of time and effort is invested in onboarding new developers. Therefore, we want to ensure that we are allocating our time and resources properly to new developers invested in honing their skills and growing to seasoned developers. 

## GitHub Dashboard for HackforLA.org Website Team

Refer to [Issue 4921](https://github.com/hackforla/website/issues/4921)

While analyzing patterns in new developer behavior for Hack for LA's Onboarding Impact Analysis, a question popped up: "What if new developers are completing less issues of a certain complexity because there aren't enough of them to work on?" Additionally, it was noticed during analysis that there were issues that were inappropriately labeled.

Hence, it was determined that a Looker dashboard that helps website team developers and other roles to:

1. Track how many issues per complexity level by role are there in each project board column
2. Get an overview of the status of these issues (e.g. how many are drafts, 2 weeks inactive, Ready for dev lead, etc.)
3. Detect anomalies in labeling and be able to quickly correct them, 

would be beneficial. 

# Technology used

- Jupyter Notebook/ Google Colab for data retrieval, cleaning, and dataset creation script
- GitHub Actions and Secrets
- Google Sheets API
- Google Developer Console
- Google Looker Studio
- Visual Studio Code

# How to contribute

Since this repository was created to support issues involving automation and Looker dashboards, contribution would be based on issue requirements.

Currently, this repository supports the following issues:
- [Issue 4152](https://github.com/hackforla/website/issues/4152)
- [Issue 4921](https://github.com/hackforla/website/issues/4921)
- [Issue 5810](https://github.com/hackforla/website/issues/5810) (Still looking for someone to work on)

# Working with forks and branches

Follow Hack for LA's [Contributing.md guidelines/instructions](https://github.com/hackforla/website/blob/gh-pages/CONTRIBUTING.md#part-1-setting-up-the-development-environment).


# Working with pull requests and reviews

Currently, all data analysts working on issues that require making changes to this repository (add or edit files) have access to merge pull requests they have made. There are currently no pull request reviewers.

## Testing

N/A

# Licensing

None as of yet.
