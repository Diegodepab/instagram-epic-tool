# User Guide

CircleScope is designed for people who want to understand their Instagram community without sharing a password.

Select **Interactive guide** in the header for a functional tour. It creates a fictional session, demonstrates graph and directory filters, performs an example search, visits the security controls, and deletes all demo information when it finishes or is closed.

If the Instagram export is not ready yet, select **Explore with sample data** on the welcome screen. The demo uses fictional profiles and supports the same graph, list, filter, and export workflow.

## 1. Download Your Instagram Information

Instagram may change the exact wording of its menus, but the general process is:

1. Open Instagram and go to **Settings and activity**.
2. Open **Accounts Center**.
3. Select **Your information and permissions**.
4. Choose **Download your information** or **Download or transfer information**.
5. Select the Instagram profile to analyze.
6. Request at least the **Followers and following** information.
7. Select **Download to device** and choose **JSON**, not HTML.
8. Download the ZIP when Instagram notifies you that it is ready.

Choose the complete history or **all time** when Instagram asks for a date range. A one-year export may include only followers added during that interval and can therefore produce incomplete current metrics. CircleScope compares relationship timestamps and displays a warning when the follower range appears partial.

Do not unzip the file when using the web interface. CircleScope accepts the official ZIP directly.

## 2. Import the Export

1. Open CircleScope in your browser.
2. Enter the username belonging to the export. The `@` symbol is optional.
3. Drag the ZIP into the upload area or select it from your computer.
4. Press **Analyze my community**.

The ZIP may be up to 1 GiB and must contain Instagram's JSON relationship files. Large exports commonly include photos, videos, and messages; CircleScope ignores those entries and reads only `followers_N.json` and `following.json`. HTML exports are intentionally rejected.

During large uploads, CircleScope shows the transferred percentage and then changes to **Processing relationships**. You can cancel while the file is being uploaded; cancelled files are closed and are not retained.

## 3. Understand the Results

- **Followers:** accounts that follow you.
- **Following:** accounts you follow.
- **Mutuals:** you follow each other.
- **Only follow you:** they follow you, but you do not follow them.
- **Do not follow you:** you follow them, but they do not follow you.

The graph uses the same colors as the metrics. Arrows show the direction of a follow relationship.

## 4. Explore the Graph

- Drag an empty area to move around.
- Use the mouse wheel or trackpad to zoom.
- Drag a node to reorganize the map.
- Search for a username with the search field.
- Click a person to center the graph and inspect relationships known by the imported dataset.

If CircleScope says there are no additional known connections, the export contains no more data for that person. The application will not contact Instagram or infer missing relationships.

The map uses adaptive repulsion, longer links, and collision radii based on node size. After the simulation settles it automatically fits the complete layout into the available space.

For large accounts, CircleScope displays a balanced selection of up to 600 profiles in the graph. Metrics and relationship lists still use the complete imported dataset.

## 5. Use Lists and CSV Files

Select **Directory** at the top of the analysis to work with all imported profiles. You can:

- filter mutual relationships, followers, followed accounts, people who only follow you, or people who do not follow you;
- search by username;
- move through results in pages of 50 profiles;
- download the selected category as a CSV file.

CSV files contain the username, relationship category, and number of connections known inside the authorized dataset. They may contain personal data, so store and share them carefully.

## 6. Merge Another Authorized Export

Open **Add another export** in the sidebar, enter the username that owns that ZIP, select the official JSON archive, and choose **Merge network**. CircleScope never contacts Instagram: it combines the two validated datasets temporarily in the current session.

- Import a ZIP only when its owner has provided it and consented to the analysis.
- Importing the same owner twice is rejected to avoid ambiguous or duplicated evidence.
- The first imported profile remains the center of metrics and filters.
- Profiles with their own imported ZIP can expose real second-degree connections when selected.
- Relationship dates are retained when present in Meta's JSON; older or unusual exports may omit them.

## 7. End the Session

Select **Close and delete session** or **Change file**. Sessions also expire automatically after one hour. Analysis data is held only in backend memory and disappears when the service restarts.

## 8. Advanced Functions

The **Security** view documents optional integrations and enforced limits. The unofficial own-account connector is disabled by default and should remain disabled outside a short, authorized local evaluation. It is separate from the ZIP workflow and may violate Instagram's terms. Never use it with an account you do not own or lack explicit permission to assess.

## Common Problems

### “Select the official ZIP in JSON format”

The selected file is not a `.zip`, or the export was requested as HTML. Request a new export from Instagram and choose JSON.

### Missing followers or followed accounts

Instagram exports can be split into several `followers_N.json` files. CircleScope reads all of them. If data is still missing, verify that the requested Instagram download included all dates and the Followers and following category.

### The session expired

For privacy, sessions last one hour. Import the ZIP again to start a new analysis.
