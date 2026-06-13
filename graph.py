import os
import json
import urllib.request
from datetime import datetime

def main():
    username = "alex-sidor"
    token = os.environ.get("GITHUB_TOKEN")
    
    # GraphQL Query to get a full year of contribution data
    query = f"""
    query {{
      user(login: "{username}") {{
        contributionsCollection {{
          contributionCalendar {{
            weeks {{
              contributionDays {{
                date
                contributionCount
              }}
            }}
          }}
        }}
      }}
    }}
    """
    
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        
    weeks = res_data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    
    months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_commits = {m: 0 for m in months_order}
    
    # Sum up daily counts into months
    for week in weeks:
        for day in week["contributionDays"]:
            date_obj = datetime.strptime(day["date"], "%Y-%m-%d")
            month_name = months_order[date_obj.month - 1]
            monthly_commits[month_name] += day["contributionCount"]
            
    values = list(monthly_commits.values())
    max_commits = max(values) if max(values) > 0 else 1
    
    # Calculate X/Y graph points
    points_list = []
    for index, count in enumerate(values):
        x = 40 + (index * 40)
        y = 160 - ((count / max_commits) * 120)
        points_list.append(f"{x},{y}")
    points_str = " ".join(points_list)
    
    # Build the SVG content
    svg_elements = []
    for index, count in enumerate(values):
        x = 40 + (index * 40)
        y = 160 - ((count / max_commits) * 120)
        label_text = f'<text x="{x}" y="{y - 10}" text-anchor="middle" class="text" fill="#c9d1d9">{count}</text>' if count > 0 else ''
        
        svg_elements.append(f"""
        <circle cx="{x}" cy="{y}" r="4" class="dot" />
        <text x="{x}" y="190" text-anchor="middle" class="text">{months_order[index]}</text>
        {label_text}
        """)
        
    elements_str = "".join(svg_elements)
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 220" width="100%" height="100%">
    <style>
      .bg {{ fill: #0d1117; rx: 6px; }}
      .line {{ fill: none; stroke: #238636; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }}
      .dot {{ fill: #238636; stroke: #0d1117; stroke-width: 2; }}
      .text {{ fill: #8b949e; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11px; }}
      .title {{ fill: #c9d1d9; font-size: 14px; font-weight: 600; }}
    </style>
    <rect width="520" height="220" class="bg" />
    <text x="20" y="30" class="text title">Monthly Commit Activity</text>
    <polyline points="{points_str}" class="line" />
    {elements_str}
  </svg>"""

    with open("monthly-activity.svg", "w") as f:
        f.write(svg)
    print("Monthly graph generated successfully!")

if __name__ == "__main__":
    main()