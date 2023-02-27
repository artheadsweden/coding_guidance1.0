import subprocess
import os
import json


def run_prospector(path):
    try:
        # Construct the Prospector command
        prospector_cmd = ['prospector', '--output-format', 'json', path]

        # Run Prospector and capture its output
        output = subprocess.check_output(prospector_cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            output = e.output.decode('utf-8')
        else:
            print(f"Error running prospector: {e.output}")
            return None

    # Parse the output
    output_dict = json.loads(output)

    # Extract the summary and message list
    summary = output_dict['summary']
    messages = output_dict['messages']

    # Create a list of module dicts
    modules = []
    for message in messages:
        if message['location']['path']:
            module_path = os.path.relpath(message['location']['path'], os.path.dirname(path)).replace('\\', '/')
            module_name = os.path.splitext(os.path.basename(message['location']['path']))[0]
            module_issues = 1
            for m in modules:
                if m['module_path'] == module_path:
                    m['number_of_issues'] += 1
                    m['issues'].append({
                        'row': message['location']['line'],
                        'col': message['location']['character'],
                        'function': message['location']['function'],
                        'message': message['message'],
                        'code': message.get('code'),
                        'tool': message['source']
                    })
                    module_issues = 0
                    break
            if module_issues == 1:
                modules.append({
                    'module_name': module_name,
                    'module_path': module_path,
                    'number_of_issues': 1,
                    'issues': [{
                        'row': message['location']['line'],
                        'col': message['location']['character'],
                        'function': message['location']['function'],
                        'message': message['message'],
                        'code': message.get('code'),
                        'tool': message['source']
                    }]
                })

    return {
        'summary': {
            'started': summary['started'],
            'completed': summary['completed'],
            'time_taken': summary['time_taken'],
            'module_count': len(modules),
            'issue_count': len(messages)
        },
        'issues': modules
    }
    
def explain_prospector2(prospector_result):
    summary = prospector_result['summary']
    issues = prospector_result['issues']
    
    # Check if any issues were found
    if summary['issue_count'] == 0:
        return "No issues found in your code!"
    
    # Create a string with the analysis summary
    summary_text = f"{summary['issue_count']} issue(s) found in {summary['module_count']} module(s)."
    summary_text += f" Analysis took {summary['time_taken']} seconds.\n\n"
    
    # Create a string with the details of each issue found
    issues_text = ""
    for issue in issues:
        issues_text += f"File: {issue['module_name']} ({issue['module_path']})\n"
        issues_text += f"Number of issues: {issue['number_of_issues']}\n"
        for detail in issue['issues']:
            row, col, func, message, code, tool = detail.values()
            if func:
                issues_text += f"\n\tFunction: {func}()\n"
            else:
                issues_text += "\n"
            issues_text += f"\tMessage: {message}\n"
            issues_text += f"\tCode: {code}\n"
            issues_text += f"\tLocation: line {row}, column {col}\n"
            issues_text += f"\tTool: {tool}\n"
    
    # Return the combined summary and issues strings
    return summary_text + issues_text

def explain_prospector(prospector_result):
    if not prospector_result['issues']:
        return "We looked at your code and found no issues. Good job!"

    issues = []
    for module_data in prospector_result['issues']:
        module_name = module_data["module_name"]
        issues_found = module_data["issues"]
        for issue in issues_found:
            issue_message = issue["message"].lower()
            tool = issue["tool"]
            code = issue["code"]
            line_number = issue["row"]
            column_number = issue["col"]
            issue_text = f"In the module named '{module_name}' we found {issue_message}. This is on line {line_number}, column {column_number}."
            issues.append(issue_text)
    issues_text = "\n".join(issues)
    return f"When looking at your code we found some issues. {issues_text}\nPlease check these problems to make your code more readable and maintainable."

