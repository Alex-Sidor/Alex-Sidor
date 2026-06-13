import os
import json
import urllib.request
from datetime import datetime, timedelta

def main():
    username = "alex-sidor"
    token = os.environ.get("GITHUB_TOKEN")
    
    # GraphQL Query to get contribution data
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
    
    # Generate past 12 months dynamically based on the current date
    all_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    current_month_idx = datetime.now().month - 1 # 0-indexed
    
    # Order months from 11 months ago leading up to the current month
    past_12_months = [all_months[(current_month_idx - i) % 12] for i in range(11, -1, -1)]
    monthly_commits = {m: 0 for m in past_12_months}
    
    # Sum up daily counts into corresponding months
    for week in weeks:
        for day in week["contributionDays"]:
            date_obj = datetime.strptime(day["date"], "%Y-%m-%d")
            month_name = all_months[date_obj.month - 1]
            if month_name in monthly_commits:
                monthly_commits[month_name] += day["contributionCount"]
                
    values = [monthly_commits[m] for m in past_12_months]
    max_commits = max(values) if max(values) > 0 else 10 # Default fallback
    
    # Round max commits up to an even grid friendly number (multiples of 10 or 50)
    if max_commits < 50:
        max_scale = ((max_commits // 10) + 1) * 10
    else:
        max_scale = ((max_commits // 50) + 1) * 50
        
    # Calculate X/Y graph coordinates
    # Graph area bounding box dimensions: X from 70 to 510, Y from 50 to 170
    points = []
    for index, count in enumerate(values):
        x = 70 + (index * 40)
        y = 170 - ((count / max_scale) * 120)
        points.append((x, y))
        
    # Generate smooth Bezier curve commands using coordinate calculations
    path_d = f"M {points[0][0]} {points[0][1]}"
    for i in range(len(points) - 1):
        p0 = points[i]
        p1 = points[i+1]
        # Control points calculation for smoothing
        cp1_x = p0[0] + 15
        cp1_y = p0[1]
        cp2_x = p1[0] - 15
        cp2_y = p1[1]
        path_d += f" C {cp1_x} {cp1_y}, {cp2_x} {cp2_y}, {p1[0]} {p1[1]}"
        
    # Build Left-Scale Axis labels and background grids
    grid_lines = []
    scale_steps = [0, max_scale // 2, max_scale]
    for step in scale_steps:
        y_grid = 170 - ((step / max_scale) * 120)
        grid_lines.append(f"""
        <line x1="65" y1="{y_grid}" x2="510" y2="{y_grid}" stroke="#21262d" stroke-dasharray="4" />
        <text x="55" y="{y_grid + 4}" text-anchor="end" class="text">{step}</text>
        """)
    grid_str = "".join(grid_lines)
    
    # Build timeline points/labels
    dots_and_labels = []
    for index, (x, y) in enumerate(points):
        dots_and_labels.append(f"""
        <circle cx="{x}" cy="{y}" r="3.5" class="dot" />
        <text x="{x}" y="195" text-anchor="middle" class="text">{past_12_months[index]}</text>
        """)
    elements_str = "".join(dots_and_labels)
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 230" width="100%" height="100%">
    <style>
      .bg {{ fill: #0d1117; rx: 6px; }}
      .line {{ fill: none; stroke: #39d353; stroke-width: 3.5; stroke-linecap: round; stroke-linejoin: round; }}
      .dot {{ fill: #39d353; stroke: #0d1117; stroke-width: 1.5; }}
      .text {{ fill: #8b949e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 11px; }}
      .title {{ fill: #c9d1d9; font-size: 14px; font-weight: 600; }}
      .axis {{ stroke: #30363d; stroke-width: 1; }}
    </style>
    <rect width="540" height="230" class="bg" />
    <text x="25" y="30" class="text title">Past 12 Months Activity</text>
    
    {grid_str}
    
    <line x1="65" y1="50" x2="65" y2="170" class="axis" />
    
    <path d="{path_d}" class="line" />
    
    {elements_str}
  </svg>"""

    with open("monthly-activity.svg", "w") as f:
        f.write(svg)
    print("Sleek rolling graph generated successfully!")

if __name__ == "__main__":
    main()
