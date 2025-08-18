#!/usr/bin/env python3
"""
100-Day LeetCode Tracker Generator with GitHub Sync
Parses the markdown plan and generates a complete HTML tracker with:
- Dark mode interface
- Individual progress tracking for each problem
- Multi-device sync via GitHub Gist
- Local storage fallback
- CSV export functionality
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class Problem:
    number: str
    title: str
    difficulty: str
    url: str

@dataclass
class Task:
    description: str
    is_bonus: bool = False

@dataclass
class Day:
    number: int
    date: str
    title: str
    dsa_title: str
    dsa_problems: List[Problem]
    dsa_goal: str
    system_design_title: str
    system_design_tasks: List[Task]

@dataclass
class Week:
    number: int
    title: str
    date_range: str
    days: List[Day]

class MarkdownParser:
    def __init__(self, md_content: str):
        self.content = md_content
        self.weeks = []
        
    def parse(self) -> List[Week]:
        """Parse the markdown content and extract structured data."""
        
        # Split content by weeks
        week_sections = re.split(r'^## WEEK \d+:', self.content, flags=re.MULTILINE)[1:]
        
        for i, week_section in enumerate(week_sections, 1):
            week = self._parse_week(i, week_section)
            if week:
                self.weeks.append(week)
                
        return self.weeks
    
    def _parse_week(self, week_num: int, content: str) -> Week:
        """Parse a single week section."""
        lines = content.strip().split('\n')
        
        # Extract week title and date range
        title_line = lines[0].strip()
        title_match = re.search(r'(.+?)\s*\((.+?)\)', title_line)
        if title_match:
            week_title = title_match.group(1).strip()
            date_range = title_match.group(2).strip()
        else:
            week_title = title_line
            date_range = ""
        
        # Find all day sections
        day_sections = re.split(r'\*\*💥 MACHINE MODE: DAY \d+', content)[1:]
        
        days = []
        for day_section in day_sections:
            day = self._parse_day(day_section)
            if day:
                days.append(day)
        
        return Week(week_num, week_title, date_range, days)
    
    def _parse_day(self, content: str) -> Day:
        """Parse a single day section."""
        lines = content.strip().split('\n')
        
        # Extract day number, date, and title
        header_line = lines[0].strip()
        day_match = re.search(r'– (.+?)(?:\*\*|$)', header_line)
        if not day_match:
            return None
            
        day_info = day_match.group(1).strip()
        
        # Parse day number and date
        day_parts = day_info.split(': ', 1)
        if len(day_parts) >= 2:
            date_part = day_parts[0].strip()
            title_part = day_parts[1].strip()
        else:
            date_part = day_info
            title_part = ""
        
        # Extract day number from the original header
        day_num_match = re.search(r'DAY (\d+)', header_line)
        day_number = int(day_num_match.group(1)) if day_num_match else 0
        
        # Parse DSA section
        dsa_title, dsa_problems, dsa_goal = self._parse_dsa_section(content)
        
        # Parse System Design section
        sd_title, sd_tasks = self._parse_system_design_section(content)
        
        return Day(
            number=day_number,
            date=date_part,
            title=title_part,
            dsa_title=dsa_title,
            dsa_problems=dsa_problems,
            dsa_goal=dsa_goal,
            system_design_title=sd_title,
            system_design_tasks=sd_tasks
        )
    
    def _parse_dsa_section(self, content: str) -> tuple:
        """Parse DSA section and extract problems."""
        dsa_match = re.search(r'🎯 \*\*DSA: (.+?)\*\*\n(.*?)(?=🧠|\Z)', content, re.DOTALL)
        if not dsa_match:
            return "", [], ""
        
        dsa_title = dsa_match.group(1).strip()
        dsa_content = dsa_match.group(2).strip()
        
        problems = []
        goal = ""
        
        # Extract problems
        problem_matches = re.findall(r'\* LC (\d+): (.+)', dsa_content)
        for num, title in problem_matches:
            difficulty = self._guess_difficulty(int(num))
            url = f"https://leetcode.com/problems/{self._title_to_slug(title)}/"
            problems.append(Problem(num, title, difficulty, url))
        
        # Extract goal
        goal_match = re.search(r'📌 Goal: (.+)', dsa_content)
        if goal_match:
            goal = goal_match.group(1).strip()
        
        return dsa_title, problems, goal
    
    def _parse_system_design_section(self, content: str) -> tuple:
        """Parse System Design section and extract tasks."""
        sd_match = re.search(r'🧠 \*\*SYSTEM DESIGN: (.+?)\*\*\n(.*?)(?=---|\Z)', content, re.DOTALL)
        if not sd_match:
            return "", []
        
        sd_title = sd_match.group(1).strip()
        sd_content = sd_match.group(2).strip()
        
        tasks = []
        
        # Extract tasks
        task_matches = re.findall(r'\* (.+)', sd_content)
        for task_text in task_matches:
            is_bonus = task_text.startswith('Bonus:')
            tasks.append(Task(task_text, is_bonus))
        
        return sd_title, tasks
    
    def _title_to_slug(self, title: str) -> str:
        """Convert problem title to URL slug."""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def _guess_difficulty(self, problem_num: int) -> str:
        """Simple difficulty guessing."""
        if problem_num in [1, 13, 20, 21, 26, 27, 35, 53, 58, 66, 70, 88, 104, 121, 125, 136, 141, 155, 169, 206, 217, 242, 268, 283, 344, 349, 485, 509, 704, 724]:
            return "easy"
        elif problem_num in [10, 23, 25, 30, 37, 42, 51, 72, 76, 84, 124, 140, 212, 239, 295, 297]:
            return "hard"
        else:
            return "medium"

class HTMLGenerator:
    def __init__(self, weeks: List[Week]):
        self.weeks = weeks
        
    def generate_html(self) -> str:
        """Generate complete HTML with all weeks and days."""
        
        html = self._get_html_template()
        
        # Generate weeks content
        weeks_html = ""
        for week in self.weeks:
            weeks_html += self._generate_week_html(week)
        
        # Replace placeholder with actual content
        html = html.replace("{{WEEKS_CONTENT}}", weeks_html)
        
        return html
    
    def _generate_week_html(self, week: Week) -> str:
        """Generate HTML for a single week."""
        days_html = ""
        for day in week.days:
            days_html += self._generate_day_html(day)
        
        return f'''
    <!-- WEEK {week.number}: {week.title} -->
    <div class="week-section" data-week="week{week.number}">
        <div class="week-header" onclick="toggleWeek(this)">
            WEEK {week.number}: {week.title} ({week.date_range})
            <span class="collapse-icon">▼</span>
        </div>
        <div class="week-content">
{days_html}
        </div>
    </div>
'''
    
    def _generate_day_html(self, day: Day) -> str:
        """Generate HTML for a single day."""
        dsa_problems_html = ""
        for problem in day.dsa_problems:
            dsa_problems_html += f'''
                                <li class="problem-item">
                                    <input type="checkbox" class="problem-checkbox" onchange="updateStats()">
                                    <a href="{problem.url}" class="problem-link" target="_blank">LC {problem.number}: {problem.title}</a>
                                    <span class="problem-difficulty {problem.difficulty}">{problem.difficulty.title()}</span>
                                </li>'''
        
        sd_tasks_html = ""
        for task in day.system_design_tasks:
            sd_tasks_html += f'''
                                <li class="task-item">
                                    <input type="checkbox" class="task-checkbox" onchange="updateStats()">
                                    <span>{task.description}</span>
                                </li>'''
        
        return f'''
            <!-- DAY {day.number} -->
            <div class="day-section">
                <div class="day-header" onclick="toggleDay(this)">
                    💥 DAY {day.number} - {day.date}: {day.title}
                    <span class="collapse-icon">▼</span>
                </div>
                <div class="day-content">
                    <div class="section-grid">
                        <div class="dsa-section">
                            <div class="section-title">🎯 DSA: {day.dsa_title}</div>
                            <ul class="problem-list">{dsa_problems_html}
                            </ul>
                            <div class="goal-section">
                                <div class="goal-title">📌 Goal:</div>
                                <div>{day.dsa_goal}</div>
                            </div>
                        </div>
                        <div class="system-design-section">
                            <div class="section-title">🧠 SYSTEM DESIGN: {day.system_design_title}</div>
                            <ul class="problem-list">{sd_tasks_html}
                            </ul>
                        </div>
                    </div>
                    <div class="date-completed">
                        <label for="day{day.number}-date">📅 Date Completed:</label>
                        <input type="date" id="day{day.number}-date" class="date-input">
                    </div>
                </div>
            </div>'''
    
    def _get_html_template(self) -> str:
        """Return the complete HTML template."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complete 100-Day LeetCode Tracker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0d1117;
            color: #e6edf3;
            padding: 20px;
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, #1f6feb 0%, #8b5cf6 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(31, 111, 235, 0.3);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        
        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #7c3aed;
        }
        
        .progress-bar {
            background-color: #21262d;
            border-radius: 10px;
            padding: 4px;
            margin: 20px 0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .progress-fill {
            background: linear-gradient(135deg, #1f6feb 0%, #8b5cf6 100%);
            height: 25px;
            border-radius: 6px;
            width: 0%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 14px;
            font-weight: bold;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }
        
        .controls {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        
        .btn {
            background: linear-gradient(135deg, #1f6feb 0%, #8b5cf6 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(31, 111, 235, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(31, 111, 235, 0.4);
        }
        
        .filter-bar {
            background: #161b22;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }
        
        .filter-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            align-items: center;
        }
        
        .filter-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #7d8590;
        }
        
        .filter-input {
            width: 100%;
            padding: 8px 12px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #e6edf3;
            font-size: 14px;
        }
        
        .filter-input:focus {
            outline: none;
            border-color: #1f6feb;
            box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.3);
        }
        
        .week-section {
            margin-bottom: 30px;
            background: #161b22;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border: 1px solid #30363d;
        }
        
        .week-header {
            background: linear-gradient(135deg, #1f6feb 0%, #8b5cf6 100%);
            color: white;
            padding: 20px;
            font-weight: bold;
            font-size: 18px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }
        
        .week-header:hover {
            background: linear-gradient(135deg, #0969da 0%, #7c3aed 100%);
        }
        
        .collapse-icon {
            font-size: 20px;
            transition: transform 0.3s ease;
        }
        
        .week-content {
            display: none;
        }
        
        .week-content.expanded {
            display: block;
        }
        
        .day-section {
            border-bottom: 1px solid #30363d;
            background: #0d1117;
        }
        
        .day-section:last-child {
            border-bottom: none;
        }
        
        .day-header {
            background: #21262d;
            padding: 15px 20px;
            font-weight: bold;
            color: #58a6ff;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #30363d;
        }
        
        .day-header:hover {
            background: #262c36;
        }
        
        .day-content {
            padding: 20px;
            display: none;
        }
        
        .day-content.expanded {
            display: block;
        }
        
        .section-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .dsa-section, .system-design-section {
            background: #161b22;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #30363d;
        }
        
        .dsa-section {
            border-left: 4px solid #f85149;
        }
        
        .system-design-section {
            border-left: 4px solid #3fb950;
        }
        
        .section-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #e6edf3;
        }
        
        .dsa-section .section-title {
            color: #ff7b72;
        }
        
        .system-design-section .section-title {
            color: #56d364;
        }
        
        .problem-list {
            list-style: none;
        }
        
        .problem-item {
            display: flex;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #21262d;
            transition: all 0.3s ease;
        }
        
        .problem-item:last-child {
            border-bottom: none;
        }
        
        .problem-item:hover {
            background: rgba(88, 166, 255, 0.1);
            border-radius: 4px;
            padding-left: 8px;
            margin-left: -8px;
            margin-right: -8px;
        }
        
        .problem-checkbox {
            margin-right: 12px;
            transform: scale(1.2);
            accent-color: #1f6feb;
        }
        
        .problem-link {
            color: #58a6ff;
            text-decoration: none;
            flex: 1;
            font-weight: 500;
        }
        
        .problem-link:hover {
            color: #79c0ff;
            text-decoration: underline;
        }
        
        .problem-difficulty {
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }
        
        .easy {
            background: rgba(0, 184, 122, 0.2);
            color: #56d364;
        }
        
        .medium {
            background: rgba(255, 193, 7, 0.2);
            color: #f0c040;
        }
        
        .hard {
            background: rgba(255, 23, 68, 0.2);
            color: #ff7b72;
        }
        
        .goal-section {
            background: rgba(139, 92, 246, 0.1);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .goal-title {
            color: #a78bfa;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .task-item {
            display: flex;
            align-items: flex-start;
            padding: 6px 0;
            color: #e6edf3;
        }
        
        .task-checkbox {
            margin-right: 10px;
            margin-top: 2px;
            transform: scale(1.1);
            accent-color: #3fb950;
            flex-shrink: 0;
        }
        
        .date-completed {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 15px;
            padding: 10px;
            background: #21262d;
            border-radius: 6px;
        }
        
        .date-input {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 4px;
            color: #e6edf3;
            padding: 6px 10px;
            font-size: 14px;
        }
        
        .date-input:focus {
            outline: none;
            border-color: #1f6feb;
        }
        
        .hidden {
            display: none;
        }
        
        /* Modal Styles */
        .modal {
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.7);
            backdrop-filter: blur(5px);
        }
        
        .modal-content {
            background: #161b22;
            margin: 5% auto;
            padding: 30px;
            border: 1px solid #30363d;
            border-radius: 12px;
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
        }
        
        .close {
            color: #7d8590;
            float: right;
            font-size: 28px;
            font-weight: bold;
            position: absolute;
            right: 20px;
            top: 15px;
            cursor: pointer;
        }
        
        .close:hover {
            color: #e6edf3;
        }
        
        .modal h2 {
            color: #e6edf3;
            margin-bottom: 20px;
        }
        
        .modal h3 {
            color: #58a6ff;
            margin: 20px 0 10px 0;
        }
        
        .modal p {
            color: #e6edf3;
            margin-bottom: 15px;
        }
        
        .modal ol {
            color: #e6edf3;
            margin-left: 20px;
            margin-bottom: 20px;
        }
        
        .modal ol li {
            margin-bottom: 8px;
        }
        
        .modal a {
            color: #58a6ff;
            text-decoration: none;
        }
        
        .modal a:hover {
            text-decoration: underline;
        }
        
        .modal-input {
            width: 100%;
            padding: 12px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #e6edf3;
            font-size: 14px;
            margin-bottom: 15px;
        }
        
        .modal-input:focus {
            outline: none;
            border-color: #1f6feb;
            box-shadow: 0 0 0 3px rgba(31, 111, 235, 0.3);
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
        }
        
        .btn-secondary:hover {
            background: linear-gradient(135deg, #5a6268 0%, #3d4043 100%);
        }
        
        .sync-status {
            padding: 10px;
            border-radius: 6px;
            margin: 10px 0;
            text-align: center;
            font-weight: bold;
        }
        
        .sync-success {
            background: rgba(56, 211, 100, 0.2);
            color: #56d364;
            border: 1px solid rgba(56, 211, 100, 0.3);
        }
        
        .sync-error {
            background: rgba(248, 81, 73, 0.2);
            color: #ff7b72;
            border: 1px solid rgba(248, 81, 73, 0.3);
        }
        
        @media (max-width: 768px) {
            .section-grid {
                grid-template-columns: 1fr;
            }
            
            .filter-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Complete 100-Day LeetCode Preparation Tracker</h1>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="total-problems">0</div>
                <div>Total Problems</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="completed-problems">0</div>
                <div>Completed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="completion-rate">0%</div>
                <div>Completion Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="days-completed">0</div>
                <div>Days Completed</div>
            </div>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" id="overall-progress">0%</div>
        </div>
        <div class="controls">
            <button class="btn" onclick="saveProgress()">💾 Save Progress</button>
            <button class="btn" onclick="loadProgress()">📂 Load Progress</button>
            <button class="btn" onclick="exportToCSV()">📊 Export CSV</button>
            <button class="btn" onclick="expandAllWeeks()">📋 Expand All</button>
            <button class="btn" onclick="collapseAllWeeks()">📁 Collapse All</button>
            <button class="btn" onclick="showGitHubSync()" id="github-btn">🔗 Setup GitHub Sync</button>
        </div>
    </div>

    <!-- GitHub Sync Modal -->
    <div id="github-modal" class="modal" style="display: none;">
        <div class="modal-content">
            <span class="close" onclick="closeGitHubModal()">&times;</span>
            <h2>🔗 GitHub Sync Setup</h2>
            <p>Sync your progress across all devices using GitHub Gist!</p>
            
            <div id="github-setup" style="display: block;">
                <h3>Step 1: Create GitHub Token</h3>
                <ol>
                    <li>Go to <a href="https://github.com/settings/tokens" target="_blank">GitHub Settings → Developer settings → Personal access tokens</a></li>
                    <li>Click "Generate new token (classic)"</li>
                    <li>Give it a name like "LeetCode Tracker"</li>
                    <li>Select scope: <strong>gist</strong> (only this permission needed)</li>
                    <li>Click "Generate token" and copy it</li>
                </ol>
                
                <h3>Step 2: Enter Token</h3>
                <input type="password" id="github-token" placeholder="Paste your GitHub token here" class="modal-input">
                <button class="btn" onclick="setupGitHubSync()">🔗 Connect GitHub</button>
            </div>
            
            <div id="github-connected" style="display: none;">
                <h3>✅ GitHub Connected!</h3>
                <p>Your progress will now sync across all devices.</p>
                <button class="btn" onclick="syncToGitHub()">☁️ Sync Now</button>
                <button class="btn btn-secondary" onclick="disconnectGitHub()">🔌 Disconnect</button>
            </div>
        </div>
    </div>

    <div class="filter-bar">
        <div class="filter-grid">
            <div class="filter-group">
                <label for="search-problems">Search Problems</label>
                <input type="text" id="search-problems" class="filter-input" placeholder="Search by problem name or number..." oninput="filterProblems()">
            </div>
            <div class="filter-group">
                <label for="filter-difficulty">Filter by Difficulty</label>
                <select id="filter-difficulty" class="filter-input" onchange="filterProblems()">
                    <option value="">All Difficulties</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="filter-status">Filter by Status</label>
                <select id="filter-status" class="filter-input" onchange="filterProblems()">
                    <option value="">All Problems</option>
                    <option value="completed">Completed</option>
                    <option value="pending">Pending</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="filter-week">Filter by Week</label>
                <select id="filter-week" class="filter-input" onchange="filterProblems()">
                    <option value="">All Weeks</option>
                    <option value="week1">Week 1</option>
                    <option value="week2">Week 2</option>
                    <option value="week3">Week 3</option>
                    <option value="week4">Week 4</option>
                    <option value="week5">Week 5</option>
                    <option value="week6">Week 6</option>
                    <option value="week7">Week 7</option>
                    <option value="week8">Week 8</option>
                    <option value="week9">Week 9</option>
                    <option value="week10">Week 10</option>
                    <option value="week11">Week 11</option>
                    <option value="week12">Week 12</option>
                    <option value="week13">Week 13</option>
                    <option value="week14">Week 14</option>
                </select>
            </div>
        </div>
    </div>

{{WEEKS_CONTENT}}

    <script>
        // GitHub Sync Configuration
        let githubToken = localStorage.getItem('github-token');
        let gistId = localStorage.getItem('gist-id');
        
        // GitHub API Functions
        async function createGist(data) {
            const response = await fetch('https://api.github.com/gists', {
                method: 'POST',
                headers: {
                    'Authorization': `token ${githubToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    description: 'LeetCode 100-Day Tracker Progress',
                    public: false,
                    files: {
                        'leetcode-progress.json': {
                            content: JSON.stringify(data, null, 2)
                        }
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error(`GitHub API error: ${response.status}`);
            }
            
            return await response.json();
        }
        
        async function updateGist(gistId, data) {
            const response = await fetch(`https://api.github.com/gists/${gistId}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `token ${githubToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    files: {
                        'leetcode-progress.json': {
                            content: JSON.stringify(data, null, 2)
                        }
                    }
                })
            });
            
            if (!response.ok) {
                throw new Error(`GitHub API error: ${response.status}`);
            }
            
            return await response.json();
        }
        
        async function loadFromGist(gistId) {
            const response = await fetch(`https://api.github.com/gists/${gistId}`, {
                headers: {
                    'Authorization': `token ${githubToken}`,
                }
            });
            
            if (!response.ok) {
                throw new Error(`GitHub API error: ${response.status}`);
            }
            
            const gist = await response.json();
            const content = gist.files['leetcode-progress.json'].content;
            return JSON.parse(content);
        }
        
        // GitHub Sync UI Functions
        function showGitHubSync() {
            document.getElementById('github-modal').style.display = 'block';
            
            if (githubToken) {
                document.getElementById('github-setup').style.display = 'none';
                document.getElementById('github-connected').style.display = 'block';
                document.getElementById('github-btn').textContent = '☁️ GitHub Sync';
            } else {
                document.getElementById('github-setup').style.display = 'block';
                document.getElementById('github-connected').style.display = 'none';
            }
        }
        
        function closeGitHubModal() {
            document.getElementById('github-modal').style.display = 'none';
        }
        
        async function setupGitHubSync() {
            const token = document.getElementById('github-token').value.trim();
            
            if (!token) {
                alert('Please enter your GitHub token');
                return;
            }
            
            try {
                // Test the token by making a simple API call
                const response = await fetch('https://api.github.com/user', {
                    headers: {
                        'Authorization': `token ${token}`,
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Invalid token');
                }
                
                // Save token
                githubToken = token;
                localStorage.setItem('github-token', token);
                
                // Show connected state
                document.getElementById('github-setup').style.display = 'none';
                document.getElementById('github-connected').style.display = 'block';
                document.getElementById('github-btn').textContent = '☁️ GitHub Sync';
                
                showStatus('✅ GitHub connected successfully!', 'success');
                
                // Auto-sync current progress
                await syncToGitHub();
                
            } catch (error) {
                console.error('GitHub setup error:', error);
                alert('Failed to connect to GitHub. Please check your token.');
            }
        }
        
        function disconnectGitHub() {
            githubToken = null;
            gistId = null;
            localStorage.removeItem('github-token');
            localStorage.removeItem('gist-id');
            
            document.getElementById('github-setup').style.display = 'block';
            document.getElementById('github-connected').style.display = 'none';
            document.getElementById('github-btn').textContent = '🔗 Setup GitHub Sync';
            document.getElementById('github-token').value = '';
            
            showStatus('🔌 GitHub disconnected', 'error');
        }
        
        async function syncToGitHub() {
            if (!githubToken) {
                alert('Please setup GitHub sync first');
                return;
            }
            
            try {
                // Get current progress
                const data = getCurrentProgress();
                data.lastSync = new Date().toISOString();
                
                let result;
                if (gistId) {
                    // Update existing gist
                    result = await updateGist(gistId, data);
                } else {
                    // Create new gist
                    result = await createGist(data);
                    gistId = result.id;
                    localStorage.setItem('gist-id', gistId);
                }
                
                showStatus('☁️ Progress synced to GitHub!', 'success');
                
            } catch (error) {
                console.error('Sync error:', error);
                showStatus('❌ Sync failed: ' + error.message, 'error');
            }
        }
        
        async function loadFromGitHubSync() {
            if (!githubToken || !gistId) {
                return false;
            }
            
            try {
                const data = await loadFromGist(gistId);
                applyProgress(data);
                showStatus('☁️ Progress loaded from GitHub!', 'success');
                return true;
            } catch (error) {
                console.error('Load from GitHub error:', error);
                showStatus('❌ Failed to load from GitHub: ' + error.message, 'error');
                return false;
            }
        }
        
        function getCurrentProgress() {
            const data = {
                checkboxes: [],
                dates: [],
                timestamp: new Date().toISOString()
            };
            
            document.querySelectorAll('input[type="checkbox"]').forEach((cb, index) => {
                data.checkboxes[index] = cb.checked;
            });
            
            document.querySelectorAll('input[type="date"]').forEach((input, index) => {
                data.dates[index] = input.value;
            });
            
            return data;
        }
        
        function applyProgress(data) {
            if (data.checkboxes) {
                document.querySelectorAll('input[type="checkbox"]').forEach((cb, index) => {
                    if (data.checkboxes[index]) cb.checked = true;
                });
            }
            
            if (data.dates) {
                document.querySelectorAll('input[type="date"]').forEach((input, index) => {
                    if (data.dates[index]) input.value = data.dates[index];
                });
            }
            
            updateStats();
        }
        
        function showStatus(message, type) {
            const existingStatus = document.querySelector('.sync-status');
            if (existingStatus) {
                existingStatus.remove();
            }
            
            const status = document.createElement('div');
            status.className = `sync-status sync-${type}`;
            status.textContent = message;
            
            const modal = document.querySelector('.modal-content');
            modal.appendChild(status);
            
            setTimeout(() => {
                status.remove();
            }, 3000);
        }
        
        // Original Functions (Enhanced with GitHub Sync)
        function toggleWeek(header) {
            const content = header.nextElementSibling;
            const icon = header.querySelector('.collapse-icon');
            
            if (content.classList.contains('expanded')) {
                content.classList.remove('expanded');
                icon.textContent = '▼';
            } else {
                content.classList.add('expanded');
                icon.textContent = '▲';
            }
        }

        function toggleDay(header) {
            const content = header.nextElementSibling;
            const icon = header.querySelector('.collapse-icon');
            
            if (content.classList.contains('expanded')) {
                content.classList.remove('expanded');
                icon.textContent = '▼';
            } else {
                content.classList.add('expanded');
                icon.textContent = '▲';
            }
        }

        function expandAllWeeks() {
            document.querySelectorAll('.week-content').forEach(content => {
                content.classList.add('expanded');
            });
            document.querySelectorAll('.week-header .collapse-icon').forEach(icon => {
                icon.textContent = '▲';
            });
            document.querySelectorAll('.day-content').forEach(content => {
                content.classList.add('expanded');
            });
            document.querySelectorAll('.day-header .collapse-icon').forEach(icon => {
                icon.textContent = '▲';
            });
        }

        function collapseAllWeeks() {
            document.querySelectorAll('.week-content').forEach(content => {
                content.classList.remove('expanded');
            });
            document.querySelectorAll('.week-header .collapse-icon').forEach(icon => {
                icon.textContent = '▼';
            });
            document.querySelectorAll('.day-content').forEach(content => {
                content.classList.remove('expanded');
            });
            document.querySelectorAll('.day-header .collapse-icon').forEach(icon => {
                icon.textContent = '▼';
            });
        }

        function updateStats() {
            const allCheckboxes = document.querySelectorAll('input[type="checkbox"]');
            const checkedBoxes = document.querySelectorAll('input[type="checkbox"]:checked');
            const problemCheckboxes = document.querySelectorAll('.problem-checkbox');
            const checkedProblems = document.querySelectorAll('.problem-checkbox:checked');
            
            const totalProblems = problemCheckboxes.length;
            const completedProblems = checkedProblems.length;
            const completionRate = totalProblems > 0 ? Math.round((completedProblems / totalProblems) * 100) : 0;
            
            let daysCompleted = 0;
            document.querySelectorAll('.day-section').forEach(day => {
                const dayCheckboxes = day.querySelectorAll('input[type="checkbox"]');
                const dayChecked = day.querySelectorAll('input[type="checkbox"]:checked');
                if (dayCheckboxes.length > 0 && dayCheckboxes.length === dayChecked.length) {
                    daysCompleted++;
                }
            });
            
            document.getElementById('total-problems').textContent = totalProblems;
            document.getElementById('completed-problems').textContent = completedProblems;
            document.getElementById('completion-rate').textContent = completionRate + '%';
            document.getElementById('days-completed').textContent = daysCompleted;
            
            const progressBar = document.getElementById('overall-progress');
            const overallProgress = allCheckboxes.length > 0 ? Math.round((checkedBoxes.length / allCheckboxes.length) * 100) : 0;
            progressBar.style.width = overallProgress + '%';
            progressBar.textContent = overallProgress + '%';
        }

        function filterProblems() {
            const searchTerm = document.getElementById('search-problems').value.toLowerCase();
            const difficultyFilter = document.getElementById('filter-difficulty').value;
            const statusFilter = document.getElementById('filter-status').value;
            const weekFilter = document.getElementById('filter-week').value;

            document.querySelectorAll('.week-section').forEach(week => {
                let weekVisible = false;
                
                if (weekFilter && !week.dataset.week.includes(weekFilter)) {
                    week.classList.add('hidden');
                    return;
                }

                week.querySelectorAll('.problem-item').forEach(item => {
                    const problemText = item.querySelector('.problem-link').textContent.toLowerCase();
                    const difficulty = item.querySelector('.problem-difficulty').classList.contains('easy') ? 'easy' :
                                     item.querySelector('.problem-difficulty').classList.contains('medium') ? 'medium' : 'hard';
                    const isCompleted = item.querySelector('.problem-checkbox').checked;
                    const status = isCompleted ? 'completed' : 'pending';

                    let visible = true;

                    if (searchTerm && !problemText.includes(searchTerm)) {
                        visible = false;
                    }

                    if (difficultyFilter && difficulty !== difficultyFilter) {
                        visible = false;
                    }

                    if (statusFilter && status !== statusFilter) {
                        visible = false;
                    }

                    if (visible) {
                        item.classList.remove('hidden');
                        weekVisible = true;
                    } else {
                        item.classList.add('hidden');
                    }
                });

                if (weekVisible || !weekFilter) {
                    week.classList.remove('hidden');
                } else {
                    week.classList.add('hidden');
                }
            });
        }

        async function saveProgress() {
            // Save locally first
            const data = getCurrentProgress();
            localStorage.setItem('leetcode-tracker-progress', JSON.stringify(data));
            
            // Try to sync to GitHub if connected
            if (githubToken) {
                await syncToGitHub();
            } else {
                const btn = event.target;
                const originalText = btn.textContent;
                btn.textContent = '✅ Saved Locally!';
                btn.style.background = 'linear-gradient(135deg, #3fb950 0%, #56d364 100%)';
                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.style.background = 'linear-gradient(135deg, #1f6feb 0%, #8b5cf6 100%)';
                }, 2000);
            }
        }

        async function loadProgress() {
            let loaded = false;
            
            // Try GitHub first if connected
            if (githubToken && gistId) {
                loaded = await loadFromGitHubSync();
            }
            
            // Fallback to localStorage if GitHub fails
            if (!loaded) {
                const saved = localStorage.getItem('leetcode-tracker-progress');
                if (saved) {
                    const data = JSON.parse(saved);
                    applyProgress(data);
                    
                    const btn = event.target;
                    const originalText = btn.textContent;
                    btn.textContent = '✅ Loaded from Local!';
                    btn.style.background = 'linear-gradient(135deg, #3fb950 0%, #56d364 100%)';
                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.style.background = 'linear-gradient(135deg, #1f6feb 0%, #8b5cf6 100%)';
                    }, 2000);
                } else {
                    alert('No saved progress found');
                }
            }
        }

        function exportToCSV() {
            const rows = [];
            rows.push(['Week', 'Day', 'Date', 'Problem/Task', 'Type', 'Difficulty', 'Completed', 'Date Completed']);
            
            document.querySelectorAll('.week-section').forEach((week, weekIndex) => {
                const weekTitle = week.querySelector('.week-header').textContent.trim();
                
                week.querySelectorAll('.day-section').forEach((day, dayIndex) => {
                    const dayTitle = day.querySelector('.day-header').textContent.trim();
                    const dateInput = day.querySelector('input[type="date"]');
                    const dateCompleted = dateInput ? dateInput.value : '';
                    
                    day.querySelectorAll('.problem-item').forEach(problem => {
                        const problemText = problem.querySelector('.problem-link').textContent;
                        const difficulty = problem.querySelector('.problem-difficulty').textContent;
                        const isCompleted = problem.querySelector('.problem-checkbox').checked ? 'Yes' : 'No';
                        
                        rows.push([
                            weekTitle,
                            dayTitle,
                            dayTitle.split(' - ')[1] || '',
                            problemText,
                            'LeetCode Problem',
                            difficulty,
                            isCompleted,
                            dateCompleted
                        ]);
                    });
                    
                    day.querySelectorAll('.task-item').forEach(task => {
                        const taskText = task.querySelector('span').textContent;
                        const isCompleted = task.querySelector('.task-checkbox').checked ? 'Yes' : 'No';
                        
                        rows.push([
                            weekTitle,
                            dayTitle,
                            dayTitle.split(' - ')[1] || '',
                            taskText,
                            'System Design Task',
                            'N/A',
                            isCompleted,
                            dateCompleted
                        ]);
                    });
                });
            });
            
            const csv = rows.map(row => row.map(cell => '"' + cell + '"').join(',')).join('\\n');
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '100-day-leetcode-tracker.csv';
            a.click();
            
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = '✅ Exported!';
            btn.style.background = 'linear-gradient(135deg, #3fb950 0%, #56d364 100%)';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = 'linear-gradient(135deg, #1f6feb 0%, #8b5cf6 100%)';
            }, 2000);
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', async function() {
            updateStats();
            
            // Auto-expand first week
            const firstWeek = document.querySelector('.week-content');
            if (firstWeek) {
                firstWeek.classList.add('expanded');
                document.querySelector('.week-header .collapse-icon').textContent = '▲';
            }
            
            // Update GitHub button text if connected
            if (githubToken) {
                document.getElementById('github-btn').textContent = '☁️ GitHub Sync';
            }
            
            // Auto-load progress on startup
            if (githubToken && gistId) {
                await loadFromGitHubSync();
            } else {
                // Load from localStorage as fallback
                const saved = localStorage.getItem('leetcode-tracker-progress');
                if (saved) {
                    const data = JSON.parse(saved);
                    applyProgress(data);
                }
            }
        });
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('github-modal');
            if (event.target === modal) {
                closeGitHubModal();
            }
        }
    </script>
</body>
</html>'''

def main():
    """Main function to generate the HTML tracker."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 generate_tracker.py <markdown_file>")
        print("Example: python3 generate_tracker.py dsa100.md")
        sys.exit(1)
    
    md_file = sys.argv[1]
    
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{md_file}' not found.")
        sys.exit(1)
    
    parser = MarkdownParser(md_content)
    weeks = parser.parse()
    
    print(f"Parsed {len(weeks)} weeks with {sum(len(week.days) for week in weeks)} days total.")
    
    generator = HTMLGenerator(weeks)
    html_content = generator.generate_html()
    
    output_file = "100_day_leetcode_tracker.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated HTML tracker: {output_file}")
    print(f"Total problems found: {sum(len(day.dsa_problems) for week in weeks for day in week.days)}")
    print(f"Total system design tasks: {sum(len(day.system_design_tasks) for week in weeks for day in week.days)}")
    print(f"Total weeks: {len(weeks)}")
    print(f"Total days: {sum(len(week.days) for week in weeks)}")
    print(f"\\n🚀 Success! Open '{output_file}' in your browser to start tracking your progress!")
    print(f"💡 Don't forget to set up GitHub Sync for multi-device access!")

if __name__ == "__main__":
    main()

# Features included:
# ✅ Complete 100-day plan with all LeetCode problems
# ✅ Dark mode professional interface  
# ✅ Multi-device sync via GitHub Gist
# ✅ Local storage fallback
# ✅ Progress statistics and filtering
# ✅ CSV export for external analysis