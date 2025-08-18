#!/usr/bin/env python3
"""
Minimal Elegant LeetCode Tracker Generator
Creates a clean, modern HTML tracker with auto GitHub sync
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
        
        # Extract week title
        title_line = lines[0].strip()
        title_match = re.search(r'(.+?)\s*\(', title_line)
        if title_match:
            week_title = title_match.group(1).strip()
        else:
            week_title = title_line
        
        # Find all day sections
        day_sections = re.split(r'\*\*💥 MACHINE MODE: DAY \d+', content)[1:]
        
        days = []
        for i, day_section in enumerate(day_sections):
            # Calculate global day number: (week-1) * 7 + day_in_week
            global_day_num = (week_num - 1) * 7 + (i + 1)
            day = self._parse_day(global_day_num, day_section)
            if day:
                days.append(day)
        
        return Week(week_num, week_title, days)
    
    def _parse_day(self, global_day_num: int, content: str) -> Day:
        """Parse a single day section."""
        lines = content.strip().split('\n')
        
        # Just use the day number - no dates
        day_title = f"Day {global_day_num}"
        
        # Parse DSA section
        dsa_title, dsa_problems, dsa_goal = self._parse_dsa_section(content)
        
        # Parse System Design section
        sd_title, sd_tasks = self._parse_system_design_section(content)
        
        return Day(global_day_num, day_title, dsa_title, dsa_problems, dsa_goal, sd_title, sd_tasks)
    
    def _parse_dsa_section(self, content: str):
        """Parse DSA section and extract all tasks/problems."""
        # Find DSA section - look for 🎯 **DSA: pattern
        dsa_match = re.search(r'🎯 \*\*DSA: (.+?)\*\*\n(.*?)(?=🧠|\Z)', content, re.DOTALL)
        if not dsa_match:
            return "", [], ""
        
        dsa_title = dsa_match.group(1).strip()
        dsa_content = dsa_match.group(2).strip()
        
        problems = []
        goal = ""
        
        # Extract goal - look for 📌 Goal: pattern or 🎯 Goal: pattern
        goal_match = re.search(r'[📌🎯] Goal: (.+)', dsa_content)
        if goal_match:
            goal = goal_match.group(1).strip()
        
        # Extract ALL bullet points as trackable items
        bullet_matches = re.findall(r'\* (.+)', dsa_content)
        for item_text in bullet_matches:
            # Skip if this line contains the goal
            if 'Goal:' in item_text:
                # Extract goal from this line if not already found
                if not goal:
                    goal_in_line = re.search(r'[📌🎯] Goal: (.+)', item_text)
                    if goal_in_line:
                        goal = goal_in_line.group(1).strip()
                    # Remove the goal part and keep the main task
                    item_text = re.sub(r'\s*[📌🎯] Goal:.*', '', item_text).strip()
                    if not item_text:  # If nothing left after removing goal
                        continue
                
            # Check if it's a LeetCode problem (LC 123: format)
            lc_match = re.match(r'LC (\d+): (.+)', item_text)
            if lc_match:
                number, title = lc_match.groups()
                difficulty = self._guess_difficulty(int(number))
                url = f"https://leetcode.com/problems/{self._title_to_slug(title)}/"
                problems.append(Problem(number, title, difficulty, url))
            else:
                # Treat as a general task/problem
                problems.append(Problem("", item_text, "task", "#"))
        
        return dsa_title, problems, goal
    
    def _parse_system_design_section(self, content: str):
        """Parse System Design section and extract tasks."""
        sd_match = re.search(r'🧠 \*\*SYSTEM DESIGN: (.+?)\*\*\n(.*?)(?=---|\Z)', content, re.DOTALL)
        if not sd_match:
            return "", []
        
        sd_title = sd_match.group(1).strip()
        sd_content = sd_match.group(2).strip()
        
        tasks = []
        
        # Extract tasks - look for * Task: or * Watch: or * Bonus: patterns
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
        """Simple difficulty guessing based on common patterns."""
        # Known easy problems
        easy_problems = {1, 13, 20, 21, 26, 27, 35, 53, 58, 66, 70, 88, 104, 121, 125, 136, 141, 155, 
                        169, 206, 217, 242, 268, 283, 344, 349, 485, 509, 704, 724, 217, 242, 268, 283, 
                        344, 349, 485, 509, 704, 724, 232, 225, 682}
        
        # Known hard problems
        hard_problems = {10, 23, 25, 30, 37, 42, 51, 72, 76, 84, 124, 140, 212, 239, 295, 297, 
                        684, 685, 1135, 1489, 1579, 1697, 1349, 778}
        
        # Special ranges - typically easy problems are low numbers, hard are high complexity
        if problem_num in easy_problems or problem_num < 50:
            return "easy"
        elif problem_num in hard_problems or problem_num > 1000:
            return "hard"
        else:
            return "medium"

class HTMLGenerator:
    def __init__(self, weeks: List[Week]):
        self.weeks = weeks
        
    def generate_html(self) -> str:
        """Generate complete minimal HTML."""
        
        weeks_html = ""
        for week in self.weeks:
            weeks_html += self._generate_week_html(week)
        
        html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LeetCode Tracker</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            line-height: 1.6;
            font-size: 14px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header */
        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header p {
            color: #888;
            font-size: 14px;
            margin-bottom: 20px;
        }

        /* Tab Navigation */
        .tab-nav {
            display: flex;
            gap: 8px;
            justify-content: center;
            margin-bottom: 0;
        }

        .tab-btn {
            background: #111;
            border: 1px solid #333;
            color: #888;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .tab-btn:hover {
            background: #222;
            border-color: #444;
            color: #fff;
        }

        .tab-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: #fff;
        }

        /* Tab Content */
        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Stats Grid */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
        }

        .stat-card {
            background: #111;
            border: 1px solid #222;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            transition: all 0.2s ease;
        }

        .stat-card:hover {
            border-color: #333;
            transform: translateY(-2px);
        }

        .stat-number {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .stat-label {
            color: #888;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Progress Bar */
        .progress-container {
            background: #222;
            border: 1px solid #333;
            border-radius: 8px;
            height: 20px;
            margin-bottom: 16px;
            overflow: hidden;
            position: relative;
        }

        .progress-container:last-of-type {
            margin-bottom: 24px;
        }

        .progress-label {
            font-size: 11px;
            color: #888;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .progress-bar {
            height: 100%;
            border-radius: 8px;
            width: 0%;
            transition: width 0.3s ease;
            min-width: 2px; /* Always show some progress bar */
        }

        #dsa-progress {
            background: linear-gradient(90deg, #f97316 0%, #ea580c 100%);
        }

        #sd-progress {
            background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%);
        }

        #dsa-only-progress {
            background: linear-gradient(90deg, #f97316 0%, #ea580c 100%);
        }

        #system-only-progress {
            background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%);
        }

        /* Controls */
        .controls {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }

        .btn {
            background: #111;
            border: 1px solid #333;
            color: #fff;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .btn:hover {
            background: #222;
            border-color: #444;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
        }

        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .sync-status {
            margin-left: auto;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .sync-connected {
            background: rgba(34, 197, 94, 0.1);
            color: #22c55e;
            border: 1px solid rgba(34, 197, 94, 0.2);
        }

        .sync-disconnected {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.2);
        }

        /* Filters */
        .filters {
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
        }

        .filters-row {
            display: grid;
            grid-template-columns: 1fr auto auto auto;
            gap: 12px;
            align-items: center;
        }

        .search-input, .filter-select {
            background: #0a0a0a;
            border: 1px solid #333;
            color: #fff;
            padding: 6px 10px;
            border-radius: 4px;
            font-size: 12px;
        }

        .search-input:focus, .filter-select:focus {
            outline: none;
            border-color: #667eea;
        }

        /* Week Sections */
        .week-section {
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            margin-bottom: 12px;
            overflow: hidden;
        }

        .week-header {
            background: #0a0a0a;
            padding: 12px 16px;
            border-bottom: 1px solid #222;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s ease;
            font-size: 13px;
            font-weight: 600;
        }

        .week-header:hover {
            background: #111;
        }

        .week-toggle {
            color: #888;
            transition: transform 0.2s ease;
            font-size: 12px;
        }

        .week-collapsed .week-toggle {
            transform: rotate(-90deg);
        }

        .week-content {
            padding: 0;
        }

        .week-collapsed .week-content {
            display: none;
        }

        /* Day Sections */
        .day-section {
            border-bottom: 1px solid #1a1a1a;
        }

        .day-section:last-child {
            border-bottom: none;
        }

        .day-header {
            background: #0f0f0f;
            padding: 10px 16px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            font-weight: 500;
            color: #ccc;
        }

        .day-header:hover {
            background: #151515;
        }

        .day-content {
            padding: 16px;
        }

        .day-collapsed .day-content {
            display: none;
        }

        /* Problem Lists */
        .sections-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .section {
            background: #0a0a0a;
            border-radius: 8px;
            padding: 16px;
            border: 2px solid transparent;
        }

        .section.full-width {
            width: 100%;
            max-width: 800px;
            margin: 0 auto;
        }

        .dsa-section {
            border-color: #f97316;
            background: linear-gradient(145deg, #0a0a0a 0%, rgba(249, 115, 22, 0.05) 100%);
        }

        .system-section {
            border-color: #22c55e;
            background: linear-gradient(145deg, #0a0a0a 0%, rgba(34, 197, 94, 0.05) 100%);
        }

        /* Content visibility based on active tab */
        .overview-content { display: block; }
        .dsa-content { display: none; }
        .system-content { display: none; }

        .tab-content.active .overview-content { display: block; }
        .tab-content.active .dsa-content { display: none; }
        .tab-content.active .system-content { display: none; }

        #dsa-tab.active ~ .container .overview-content { display: none; }
        #dsa-tab.active ~ .container .dsa-content { display: block; }
        #dsa-tab.active ~ .container .system-content { display: none; }

        #system-tab.active ~ .container .overview-content { display: none; }
        #system-tab.active ~ .container .dsa-content { display: none; }
        #system-tab.active ~ .container .system-content { display: block; }

        /* Global content visibility */
        .content-overview .overview-content { display: block; }
        .content-overview .dsa-content { display: none; }
        .content-overview .system-content { display: none; }

        .content-dsa .overview-content { display: none; }
        .content-dsa .dsa-content { display: block; }
        .content-dsa .system-content { display: none; }

        .content-system .overview-content { display: none; }
        .content-system .dsa-content { display: none; }
        .content-system .system-content { display: block; }

        .section-title {
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
            padding-bottom: 8px;
            border-bottom: 1px solid #222;
        }

        .dsa-section .section-title {
            color: #f97316;
            border-bottom-color: rgba(249, 115, 22, 0.3);
        }

        .system-section .section-title {
            color: #22c55e;
            border-bottom-color: rgba(34, 197, 94, 0.3);
        }

        .problem-item, .task-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 4px 0;
            font-size: 12px;
        }

        .problem-checkbox, .task-checkbox {
            width: 14px;
            height: 14px;
            border: 1px solid #333;
            border-radius: 2px;
            background: transparent;
            cursor: pointer;
            position: relative;
            flex-shrink: 0;
        }

        .problem-checkbox:checked, .task-checkbox:checked {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: #667eea;
        }

        .problem-checkbox:checked::after, .task-checkbox:checked::after {
            content: '✓';
            position: absolute;
            top: -2px;
            left: 1px;
            color: white;
            font-size: 10px;
            font-weight: bold;
        }

        .problem-link {
            color: #fff;
            text-decoration: none;
            flex: 1;
        }

        .problem-link:hover {
            color: #667eea;
        }

        .task-text {
            color: #ccc;
            flex: 1;
        }

        .goal-text {
            margin-top: 8px;
            padding: 6px 8px;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 4px;
            font-size: 11px;
            color: #888;
            border-left: 2px solid #667eea;
        }

        .difficulty {
            padding: 1px 6px;
            border-radius: 3px;
            font-size: 9px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        .difficulty.easy {
            background: rgba(34, 197, 94, 0.1);
            color: #22c55e;
        }

        .difficulty.medium {
            background: rgba(249, 115, 22, 0.1);
            color: #f97316;
        }

        .difficulty.hard {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
        }

        .difficulty.task {
            background: rgba(168, 85, 247, 0.1);
            color: #a855f7;
        }

        /* GitHub Modal */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .modal-content {
            background: #111;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 24px;
            max-width: 500px;
            width: 90%;
        }

        .modal h2 {
            margin-bottom: 16px;
            color: #667eea;
        }

        .modal input {
            width: 100%;
            background: #0a0a0a;
            border: 1px solid #333;
            color: #fff;
            padding: 8px 12px;
            border-radius: 6px;
            margin: 8px 0;
        }

        .close {
            float: right;
            font-size: 24px;
            cursor: pointer;
            color: #888;
        }

        .close:hover {
            color: #fff;
        }

        .hidden {
            display: none !important;
        }

        @media (max-width: 768px) {
            .sections-grid {
                grid-template-columns: 1fr;
            }
            
            .filters-row {
                grid-template-columns: 1fr;
                gap: 8px;
            }
            
            .stats {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body class="content-overview">
    <div class="container">
        <div class="header">
            <h1>LeetCode Tracker</h1>
            <p>100-Day Coding Journey</p>
            
            <!-- Tab Navigation -->
            <div class="tab-nav">
                <button class="tab-btn active" onclick="showTab('overview')">📊 Overview</button>
                <button class="tab-btn" onclick="showTab('dsa')">🎯 DSA Only</button>
                <button class="tab-btn" onclick="showTab('system')">🧠 System Design Only</button>
            </div>
        </div>

        <!-- Overview Tab -->
        <div id="overview-tab" class="tab-content active">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="total-problems">0</div>
                    <div class="stat-label">DSA Problems</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="completed-problems">0</div>
                    <div class="stat-label">DSA Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="total-tasks">0</div>
                    <div class="stat-label">System Design</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="completed-tasks">0</div>
                    <div class="stat-label">SD Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="dsa-rate">0%</div>
                    <div class="stat-label">DSA Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="sd-rate">0%</div>
                    <div class="stat-label">SD Rate</div>
                </div>
            </div>

            <div class="progress-container">
                <div class="progress-label">DSA Progress</div>
                <div class="progress-bar" id="dsa-progress"></div>
            </div>
            
            <div class="progress-container">
                <div class="progress-label">System Design Progress</div>
                <div class="progress-bar" id="sd-progress"></div>
            </div>
        </div>

        <!-- DSA Only Tab -->
        <div id="dsa-tab" class="tab-content">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="dsa-total">0</div>
                    <div class="stat-label">Total Problems</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="dsa-completed">0</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="dsa-easy">0</div>
                    <div class="stat-label">Easy</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="dsa-medium">0</div>
                    <div class="stat-label">Medium</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="dsa-hard">0</div>
                    <div class="stat-label">Hard</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="dsa-completion-rate">0%</div>
                    <div class="stat-label">Completion Rate</div>
                </div>
            </div>

            <div class="progress-container">
                <div class="progress-label">DSA Progress</div>
                <div class="progress-bar" id="dsa-only-progress"></div>
            </div>
        </div>

        <!-- System Design Only Tab -->
        <div id="system-tab" class="tab-content">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="system-total">0</div>
                    <div class="stat-label">Total Tasks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="system-completed">0</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="system-watch">0</div>
                    <div class="stat-label">Watch Tasks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="system-design">0</div>
                    <div class="stat-label">Design Tasks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="system-bonus">0</div>
                    <div class="stat-label">Bonus Tasks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="system-completion-rate">0%</div>
                    <div class="stat-label">Completion Rate</div>
                </div>
            </div>

            <div class="progress-container">
                <div class="progress-label">System Design Progress</div>
                <div class="progress-bar" id="system-only-progress"></div>
            </div>
        </div>

        <div class="controls">
            <button class="btn btn-primary" onclick="syncProgress()" id="sync-btn">⚡ Auto Sync</button>
            <button class="btn" onclick="exportToCSV()">📊 Export</button>
            <button class="btn" onclick="expandAll()">📋 Expand All</button>
            <button class="btn" onclick="collapseAll()">📁 Collapse All</button>
            <div class="sync-status sync-disconnected" id="sync-status">
                <span>●</span> Offline
            </div>
        </div>

        <div class="filters">
            <div class="filters-row">
                <input type="text" class="search-input" id="search" placeholder="Search problems..." oninput="filterContent()">
                <select class="filter-select" id="difficulty-filter" onchange="filterContent()">
                    <option value="">All Difficulties</option>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                    <option value="task">Tasks</option>
                </select>
                <select class="filter-select" id="status-filter" onchange="filterContent()">
                    <option value="">All Status</option>
                    <option value="completed">Completed</option>
                    <option value="pending">Pending</option>
                </select>
                <select class="filter-select" id="week-filter" onchange="filterContent()">
                    <option value="">All Weeks</option>
                    <option value="1">Week 1</option>
                    <option value="2">Week 2</option>
                    <option value="3">Week 3</option>
                    <option value="4">Week 4</option>
                    <option value="5">Week 5</option>
                    <option value="6">Week 6</option>
                    <option value="7">Week 7</option>
                    <option value="8">Week 8</option>
                    <option value="9">Week 9</option>
                    <option value="10">Week 10</option>
                    <option value="11">Week 11</option>
                    <option value="12">Week 12</option>
                    <option value="13">Week 13</option>
                    <option value="14">Week 14</option>
                </select>
            </div>
        </div>

        {{WEEKS_CONTENT}}

        <!-- GitHub Sync Modal -->
        <div id="github-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <span class="close" onclick="closeModal()">&times;</span>
                <h2>🔗 GitHub Sync Setup</h2>
                <p>Enter your GitHub personal access token to enable automatic sync across devices.</p>
                
                <div id="setup-form">
                    <input type="password" id="github-token" placeholder="GitHub Personal Access Token">
                    <br><br>
                    <button class="btn btn-primary" onclick="setupSync()">Connect GitHub</button>
                    <button class="btn" onclick="closeModal()">Cancel</button>
                </div>
                
                <div id="connected-info" style="display: none;">
                    <p>✅ GitHub sync is active</p>
                    <button class="btn" onclick="disconnectSync()">Disconnect</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // GitHub Sync Configuration
        let githubToken = localStorage.getItem('github-token');
        let gistId = localStorage.getItem('gist-id');
        let autoSyncInterval;

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            updateStats();
            loadProgress();
            
            if (githubToken) {
                setupAutoSync();
            }
        });

        // Tab switching
        function showTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + '-tab').classList.add('active');
            
            // Update body class for content visibility
            document.body.className = 'content-' + tabName;
            
            // Update stats for the new tab
            setTimeout(() => updateStats(), 10); // Small delay to ensure content visibility is updated
        }

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
            
            if (!response.ok) throw new Error(`GitHub API error: ${response.status}`);
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
            
            if (!response.ok) throw new Error(`GitHub API error: ${response.status}`);
            return await response.json();
        }

        async function loadFromGist(gistId) {
            const response = await fetch(`https://api.github.com/gists/${gistId}`, {
                headers: { 'Authorization': `token ${githubToken}` }
            });
            
            if (!response.ok) throw new Error(`GitHub API error: ${response.status}`);
            
            const gist = await response.json();
            const content = gist.files['leetcode-progress.json'].content;
            return JSON.parse(content);
        }

        // Sync Functions
        function setupAutoSync() {
            const syncStatus = document.getElementById('sync-status');
            const syncBtn = document.getElementById('sync-btn');
            
            syncStatus.className = 'sync-status sync-connected';
            syncStatus.innerHTML = '<span>●</span> Synced';
            syncBtn.textContent = '☁️ Auto Sync';
            
            // Auto-sync every 30 seconds
            autoSyncInterval = setInterval(async () => {
                try {
                    await syncProgress();
                } catch (error) {
                    console.log('Auto-sync failed:', error);
                }
            }, 30000);
        }

        async function syncProgress() {
            if (!githubToken) {
                document.getElementById('github-modal').style.display = 'block';
                return;
            }

            try {
                const data = getCurrentProgress();
                data.lastSync = new Date().toISOString();
                
                if (gistId) {
                    await updateGist(gistId, data);
                } else {
                    const result = await createGist(data);
                    gistId = result.id;
                    localStorage.setItem('gist-id', gistId);
                }
                
                // Save locally too
                localStorage.setItem('leetcode-tracker-progress', JSON.stringify(data));
                
                // Update sync status briefly
                const syncStatus = document.getElementById('sync-status');
                const originalText = syncStatus.innerHTML;
                syncStatus.innerHTML = '<span>●</span> Synced';
                
            } catch (error) {
                console.error('Sync failed:', error);
                const syncStatus = document.getElementById('sync-status');
                syncStatus.className = 'sync-status sync-disconnected';
                syncStatus.innerHTML = '<span>●</span> Sync Failed';
            }
        }

        async function setupSync() {
            const token = document.getElementById('github-token').value.trim();
            
            if (!token) {
                alert('Please enter your GitHub token');
                return;
            }

            try {
                // Test the token
                const response = await fetch('https://api.github.com/user', {
                    headers: { 'Authorization': `token ${token}` }
                });
                
                if (!response.ok) throw new Error('Invalid token');
                
                githubToken = token;
                localStorage.setItem('github-token', token);
                
                closeModal();
                setupAutoSync();
                await syncProgress();
                
            } catch (error) {
                alert('Failed to connect to GitHub. Please check your token.');
            }
        }

        function disconnectSync() {
            githubToken = null;
            gistId = null;
            localStorage.removeItem('github-token');
            localStorage.removeItem('gist-id');
            
            if (autoSyncInterval) {
                clearInterval(autoSyncInterval);
            }
            
            const syncStatus = document.getElementById('sync-status');
            const syncBtn = document.getElementById('sync-btn');
            
            syncStatus.className = 'sync-status sync-disconnected';
            syncStatus.innerHTML = '<span>●</span> Offline';
            syncBtn.textContent = '⚡ Auto Sync';
            
            closeModal();
        }

        // UI Functions
        function toggleWeek(header) {
            const section = header.parentElement;
            const content = section.querySelector('.week-content');
            const toggle = header.querySelector('.week-toggle');
            
            section.classList.toggle('week-collapsed');
            toggle.textContent = section.classList.contains('week-collapsed') ? '▶' : '▼';
        }

        function toggleDay(header) {
            const section = header.parentElement;
            const content = section.querySelector('.day-content');
            
            section.classList.toggle('day-collapsed');
        }

        function expandAll() {
            document.querySelectorAll('.week-section').forEach(week => {
                week.classList.remove('week-collapsed');
                week.querySelector('.week-toggle').textContent = '▼';
            });
            
            document.querySelectorAll('.day-section').forEach(day => {
                day.classList.remove('day-collapsed');
            });
        }

        function collapseAll() {
            document.querySelectorAll('.week-section').forEach(week => {
                week.classList.add('week-collapsed');
                week.querySelector('.week-toggle').textContent = '▶';
            });
            
            document.querySelectorAll('.day-section').forEach(day => {
                day.classList.add('day-collapsed');
            });
        }

        function updateStats() {
            // Determine which content is currently visible
            const activeTab = document.querySelector('.tab-content.active').id;
            let contentSelector = '';
            
            if (activeTab === 'overview-tab') {
                contentSelector = '.overview-content';
            } else if (activeTab === 'dsa-tab') {
                contentSelector = '.dsa-content';
            } else if (activeTab === 'system-tab') {
                contentSelector = '.system-content';
            }
            
            // Only count checkboxes in the active content
            const dsaCheckboxes = document.querySelectorAll(contentSelector + ' .problem-checkbox');
            const dsaCompleted = document.querySelectorAll(contentSelector + ' .problem-checkbox:checked');
            const dsaTaskCheckboxes = document.querySelectorAll(contentSelector + ' .task-checkbox.dsa-task');
            const dsaTaskCompleted = document.querySelectorAll(contentSelector + ' .task-checkbox.dsa-task:checked');
            
            // System Design tracking  
            const sdCheckboxes = document.querySelectorAll(contentSelector + ' .task-checkbox.system-task');
            const sdCompleted = document.querySelectorAll(contentSelector + ' .task-checkbox.system-task:checked');
            
            // Overview tab stats
            const totalDSA = dsaCheckboxes.length + dsaTaskCheckboxes.length;
            const completedDSA = dsaCompleted.length + dsaTaskCompleted.length;
            
            document.getElementById('total-problems').textContent = totalDSA;
            document.getElementById('completed-problems').textContent = completedDSA;
            document.getElementById('total-tasks').textContent = sdCheckboxes.length;
            document.getElementById('completed-tasks').textContent = sdCompleted.length;
            
            const dsaRate = totalDSA > 0 ? Math.round((completedDSA / totalDSA) * 100) : 0;
            const sdRate = sdCheckboxes.length > 0 ? Math.round((sdCompleted.length / sdCheckboxes.length) * 100) : 0;
            
            document.getElementById('dsa-rate').textContent = dsaRate + '%';
            document.getElementById('sd-rate').textContent = sdRate + '%';
            document.getElementById('dsa-progress').style.width = dsaRate + '%';
            document.getElementById('sd-progress').style.width = sdRate + '%';
            
            // DSA Only tab stats
            const easyProblems = document.querySelectorAll(contentSelector + ' .difficulty.easy').length;
            const mediumProblems = document.querySelectorAll(contentSelector + ' .difficulty.medium').length;
            const hardProblems = document.querySelectorAll(contentSelector + ' .difficulty.hard').length;
            
            document.getElementById('dsa-total').textContent = totalDSA;
            document.getElementById('dsa-completed').textContent = completedDSA;
            document.getElementById('dsa-easy').textContent = easyProblems;
            document.getElementById('dsa-medium').textContent = mediumProblems;
            document.getElementById('dsa-hard').textContent = hardProblems;
            document.getElementById('dsa-completion-rate').textContent = dsaRate + '%';
            document.getElementById('dsa-only-progress').style.width = dsaRate + '%';
            
            // System Design Only tab stats
            const watchTasks = document.querySelectorAll(contentSelector + ' .system-task[data-type="watch"]').length;
            const designTasks = document.querySelectorAll(contentSelector + ' .system-task[data-type="design"]').length;
            const bonusTasks = document.querySelectorAll(contentSelector + ' .system-task[data-type="bonus"]').length;
            
            document.getElementById('system-total').textContent = sdCheckboxes.length;
            document.getElementById('system-completed').textContent = sdCompleted.length;
            document.getElementById('system-watch').textContent = watchTasks;
            document.getElementById('system-design').textContent = designTasks;
            document.getElementById('system-bonus').textContent = bonusTasks;
            document.getElementById('system-completion-rate').textContent = sdRate + '%';
            document.getElementById('system-only-progress').style.width = sdRate + '%';
        }

        function filterContent() {
            const search = document.getElementById('search').value.toLowerCase();
            const difficultyFilter = document.getElementById('difficulty-filter').value;
            const statusFilter = document.getElementById('status-filter').value;
            const weekFilter = document.getElementById('week-filter').value;

            document.querySelectorAll('.week-section').forEach(week => {
                const weekNumber = week.dataset.week;
                let weekVisible = false;
                
                if (weekFilter && weekNumber !== weekFilter) {
                    week.classList.add('hidden');
                    return;
                }

                // Filter LeetCode problems
                week.querySelectorAll('.problem-item').forEach(item => {
                    const text = item.querySelector('.problem-link').textContent.toLowerCase();
                    const difficulty = item.querySelector('.difficulty')?.textContent.toLowerCase() || '';
                    const isCompleted = item.querySelector('.problem-checkbox').checked;
                    
                    let visible = true;
                    
                    if (search && !text.includes(search)) visible = false;
                    if (difficultyFilter && difficulty !== difficultyFilter) visible = false;
                    if (statusFilter === 'completed' && !isCompleted) visible = false;
                    if (statusFilter === 'pending' && isCompleted) visible = false;
                    
                    item.style.display = visible ? 'flex' : 'none';
                    if (visible) weekVisible = true;
                });
                
                // Filter general tasks
                week.querySelectorAll('.task-item').forEach(item => {
                    const text = item.querySelector('.task-text').textContent.toLowerCase();
                    const isCompleted = item.querySelector('.task-checkbox').checked;
                    
                    let visible = true;
                    
                    if (search && !text.includes(search)) visible = false;
                    if (difficultyFilter && difficultyFilter !== 'task' && difficultyFilter !== '') visible = false;
                    if (statusFilter === 'completed' && !isCompleted) visible = false;
                    if (statusFilter === 'pending' && isCompleted) visible = false;
                    
                    item.style.display = visible ? 'flex' : 'none';
                    if (visible) weekVisible = true;
                });

                week.classList.toggle('hidden', !weekVisible);
            });
        }

        function getCurrentProgress() {
            const data = {
                checkboxes: {},
                timestamp: new Date().toISOString()
            };
            
            document.querySelectorAll('.problem-checkbox, .task-checkbox').forEach((checkbox, index) => {
                data.checkboxes[index] = checkbox.checked;
            });
            
            return data;
        }

        function loadProgress() {
            const saved = localStorage.getItem('leetcode-tracker-progress');
            if (saved) {
                const data = JSON.parse(saved);
                
                document.querySelectorAll('.problem-checkbox, .task-checkbox').forEach((checkbox, index) => {
                    if (data.checkboxes && data.checkboxes[index] !== undefined) {
                        checkbox.checked = data.checkboxes[index];
                    }
                });
                
                updateStats();
            }
        }

        function exportToCSV() {
            const rows = [['Week', 'Day', 'Type', 'Title', 'Difficulty', 'Completed', 'URL']];
            
            document.querySelectorAll('.week-section').forEach(week => {
                const weekTitle = week.querySelector('.week-header').textContent.trim();
                
                week.querySelectorAll('.day-section').forEach(day => {
                    const dayTitle = day.querySelector('.day-header').textContent.trim();
                    
                    // Export LeetCode problems
                    day.querySelectorAll('.problem-item').forEach(item => {
                        const checkbox = item.querySelector('.problem-checkbox');
                        const link = item.querySelector('.problem-link');
                        const difficulty = item.querySelector('.difficulty');
                        
                        rows.push([
                            weekTitle,
                            dayTitle,
                            'LeetCode Problem',
                            link.textContent,
                            difficulty ? difficulty.textContent : '',
                            checkbox.checked ? 'Yes' : 'No',
                            link.href
                        ]);
                    });
                    
                    // Export general tasks
                    day.querySelectorAll('.task-item').forEach(item => {
                        const checkbox = item.querySelector('.task-checkbox');
                        const text = item.querySelector('.task-text');
                        
                        rows.push([
                            weekTitle,
                            dayTitle,
                            'Task',
                            text.textContent,
                            'Task',
                            checkbox.checked ? 'Yes' : 'No',
                            ''
                        ]);
                    });
                });
            });
            
            const csv = rows.map(row => row.map(cell => `"${cell}"`).join(',')).join('\\n');
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'leetcode-progress.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        function closeModal() {
            document.getElementById('github-modal').style.display = 'none';
        }

        // Add event listeners for auto-save and sync
        document.addEventListener('change', function(e) {
            if (e.target.classList.contains('problem-checkbox') || e.target.classList.contains('task-checkbox')) {
                updateStats();
                
                // Auto-save locally
                const data = getCurrentProgress();
                localStorage.setItem('leetcode-tracker-progress', JSON.stringify(data));
            }
        });
    </script>
</body>
</html>'''

        return html_template.replace('{{WEEKS_CONTENT}}', weeks_html)
    
    def _generate_week_html(self, week: Week) -> str:
        """Generate HTML for a single week."""
        days_html = ""
        for day in week.days:
            days_html += self._generate_day_html(week.number, day)
        
        return f'''
        <div class="week-section" data-week="{week.number}">
            <div class="week-header" onclick="toggleWeek(this)">
                <span>Week {week.number}: {week.title}</span>
                <span class="week-toggle">▼</span>
            </div>
            <div class="week-content">
{days_html}
            </div>
        </div>'''
    
    def _generate_day_html(self, week_num: int, day: Day) -> str:
        """Generate HTML for a single day."""
        
        # DSA Problems HTML
        dsa_html = ""
        for problem in day.dsa_problems:
            if problem.number:  # LeetCode problem
                dsa_html += f'''
                    <div class="problem-item">
                        <input type="checkbox" class="problem-checkbox" onchange="updateStats()">
                        <a href="{problem.url}" target="_blank" class="problem-link">LC {problem.number}: {problem.title}</a>
                        <span class="difficulty {problem.difficulty}">{problem.difficulty}</span>
                    </div>'''
            else:  # General task
                dsa_html += f'''
                    <div class="task-item">
                        <input type="checkbox" class="task-checkbox dsa-task" onchange="updateStats()">
                        <span class="task-text">{problem.title}</span>
                    </div>'''
        
        # System Design Tasks HTML
        tasks_html = ""
        for task in day.system_design_tasks:
            task_type = "watch" if "Watch:" in task.description else ("bonus" if task.is_bonus else "design")
            tasks_html += f'''
                    <div class="task-item">
                        <input type="checkbox" class="task-checkbox system-task" data-type="{task_type}" onchange="updateStats()">
                        <span class="task-text">{task.description}</span>
                    </div>'''
        
        # Combined view (Overview tab)
        combined_html = f'''
                <div class="day-section day-collapsed overview-content">
                    <div class="day-header" onclick="toggleDay(this)">
                        <span>{day.title}</span>
                        <span>▶</span>
                    </div>
                    <div class="day-content">
                        <div class="sections-grid">
                            <div class="section dsa-section">
                                <div class="section-title">🎯 {day.dsa_title}</div>
                                {dsa_html}
                                {f'<div class="goal-text">📌 {day.dsa_goal}</div>' if day.dsa_goal else ''}
                            </div>
                            <div class="section system-section">
                                <div class="section-title">🧠 {day.system_design_title}</div>
                                {tasks_html}
                            </div>
                        </div>
                    </div>
                </div>'''
        
        # DSA Only view
        dsa_only_html = f'''
                <div class="day-section day-collapsed dsa-content">
                    <div class="day-header" onclick="toggleDay(this)">
                        <span>{day.title} - {day.dsa_title}</span>
                        <span>▶</span>
                    </div>
                    <div class="day-content">
                        <div class="section dsa-section full-width">
                            <div class="section-title">🎯 {day.dsa_title}</div>
                            {dsa_html}
                            {f'<div class="goal-text">📌 {day.dsa_goal}</div>' if day.dsa_goal else ''}
                        </div>
                    </div>
                </div>'''
        
        # System Design Only view
        system_only_html = f'''
                <div class="day-section day-collapsed system-content">
                    <div class="day-header" onclick="toggleDay(this)">
                        <span>{day.title} - {day.system_design_title}</span>
                        <span>▶</span>
                    </div>
                    <div class="day-content">
                        <div class="section system-section full-width">
                            <div class="section-title">🧠 {day.system_design_title}</div>
                            {tasks_html}
                        </div>
                    </div>
                </div>'''
        
        return combined_html + dsa_only_html + system_only_html

def main():
    """Main function to generate the elegant HTML tracker."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 elegant_tracker.py <markdown_file>")
        print("Example: python3 elegant_tracker.py dsa100.md")
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
    
    print(f"✨ Parsed {len(weeks)} weeks with {sum(len(week.days) for week in weeks)} days total.")
    
    generator = HTMLGenerator(weeks)
    html_content = generator.generate_html()
    
    output_file = "leetcode_tracker.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"🚀 Generated elegant tracker: {output_file}")
    print(f"📊 Total problems: {sum(len(day.dsa_problems) for week in weeks for day in week.days)}")
    print(f"🧠 Total system design tasks: {sum(len(day.system_design_tasks) for week in weeks for day in week.days)}")
    print(f"📅 Total weeks: {len(weeks)}")
    print(f"⚡ Total days: {sum(len(week.days) for week in weeks)}")
    print(f"\n✅ Success! Open '{output_file}' in your browser to start tracking.")
    print(f"🔗 Click 'Auto Sync' to set up GitHub sync for multi-device access.")

if __name__ == "__main__":
    main()