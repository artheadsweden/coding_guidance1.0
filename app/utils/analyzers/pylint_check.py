import subprocess
import re
import os

PYLINT_CODES = {
    "C0111": 3, # Missing docstring
    "C0112": 3, # Empty docstring
    "C0103": 5, # Invalid variable name
    "C0116": 3, # Missing function or method docstring
    "E0602": 5, # Undefined variable
    "E1120": 5, # No value for argument
    "E1111": 5, # Assigning to function call which doesn't return
    "E1101": 5, # Module 'module_name' has no 'member_name' member
    "R0201": 2, # Method could be a function
    "R1710": 2, # Consider using a list comprehension
    "W0621": 3, # Redefining name from outer scope
    "W1202": 4, # Using string format on an unmatched argument index
    "W1203": 4, # Using string format on a none value
    "W0622": 4, # Redefining built-in
    "W0613": 2, # Unused argument
    "W0311": 4, # Bad indentation
}

import re

def parse_pylint_report(report_lines):
    result = {"summary": {}, "issues": []}
    issue_lines = []
    for line in report_lines:
        if line.startswith("*" * 10):
            section_title = line.strip("* ")
            if section_title == "Global evaluation":
                break
        elif line.startswith("=" * 23):
            issue_lines.append(line)
        elif issue_lines and line.startswith(" " * 4):
            issue_lines.append(line)
        elif issue_lines:
            issue = {"file_path": "", "line_number": "", "pylint_code": "", "description": ""}
            match = re.match(r"^([^:]+):(\d+):\s+\[(\w+)\]\s+(.*)$", issue_lines[0])
            if match:
                issue["file_path"] = match.group(1)
                issue["line_number"] = int(match.group(2))
                issue["pylint_code"] = match.group(3)
                issue["description"] = match.group(4).strip()
            result["issues"].append(issue)
            issue_lines = []
        else:
            match = re.match(r"^([\w ]+):\s+(.*)$", line)
            if match:
                result["summary"][match.group(1)] = match.group(2)
    return result

def run_pylint(path):
    process = subprocess.Popen(['pylint', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    output = stdout.decode('utf-8').strip().split('\n')
    rep = parse_pylint_report(output)
    result = []
    module_data = {}
    for line in output:
        if line.startswith('-------------'):
            pylint_summary = line[-1]
            pylint_score = line.split('/')[0].split(' ')[-1]
            module_data['pylint_score'] = pylint_score
            module_data['pylint_summary'] = pylint_summary
            result.append(module_data)
            module_data = {}    
            break
        elif line.startswith('*************'):
            if len(module_data) > 0:
                result.append(module_data)
            module_data = {}
            module_data['name'] = line.split(' ')[-1].strip()
            module_data['issues'] = []
        elif line.startswith('=='):
            continue
        elif line.startswith(path):
            module = line.split(':')[0].replace('\\', '/')
            line_no = re.findall(r':[0-9]+', line)[0].replace(':', '')
            col_no = re.findall(r':[0-9]+', line)[-1].replace(':', '')
            pylint_code = re.search(r': [A-Z][0-9]{4}[:]', line).group().split(': ')[1].strip(':')
            pylint_message = line.split(':')[-1].strip()
            module_data['issues'].append({
                'module': module,
                'line_no': line_no,
                'col_no': col_no,
                'lint_code': pylint_code,
                'lint_msg': pylint_message
            })
        else:
            continue
    
    return result

def check_pylint(path):
    linted = []
    for root, dirs, _files in os.walk(path):
        for name in _files:
            if name.endswith('.py'):
                module_name = os.path.join(root, name)
                result = run_pylint(module_name)
                linted.append(result)
    return linted
            