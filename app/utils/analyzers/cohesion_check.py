import subprocess


def check_cohesion(path):
    try:
        cohesion_cmd = ['cohesion', '-v', '-d', path]
        output = subprocess.check_output(cohesion_cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = e.output.decode('utf-8')
        print(e)
    output = output.decode('utf-8')
    lines = output.splitlines()
    output = []
    current_file = {}
    current_class = {}
    current_function = {}
    for line in lines:
        if line.startswith('File: '):
            # If we encounter a new file, add the current file to the output and reset current_file and current_class
            if current_file:
                if current_class:
                    current_file['classes'].append(current_class)
                output.append(current_file)
            current_file = {
                'filename': line.split(' ')[1],
                'classes': []
            }
            current_class = {}
            current_function = {}
        elif line.startswith('  Class: '):
            # If we encounter a new class, add the current class to the current file and reset current_class
            if current_class:
                if current_function:
                    current_class['methods'].append(current_function)
                current_file['classes'].append(current_class)
            current_class = {
                'name': line.split(' ')[3],
                'line': line.split(' ')[4].split(':')[0][1:],
                'col': line.split(' ')[4].split(':')[1][:-1],
                'methods': []
            }
            current_function = {}
        elif line.startswith('    Function: '):
            # If we encounter a new function, add the current function to the current class and reset current_function
            if current_function:
                current_class['methods'].append(current_function)
            function_info = line.split(' ')
            function_name = function_info[5]
            method_type = function_info[6] if '/' not in function_info[6] else None
            cohesion = function_info[6] if '/' in function_info[6] else None
            cohesion_percentage = function_info[-1] if '%' in function_info[-1] else '0%'
            current_function = {
                'name': function_name,
                'method_type': method_type,
                'cohesion': cohesion,
                'cohesion_percentage': cohesion_percentage,
                'cohesion_as_float': float(cohesion_percentage[:-2]),
                'variables': []
            }
        elif line.startswith('      Variable: '):
            # If we encounter a new variable, add it to the current function's variables list
            variable_info = line.split(' ')
            variable_name = variable_info[7]
            cohensive_use = variable_info[8]
            current_function['variables'].append({
                'name': variable_name,
                'cohesive_use': True if cohensive_use == 'True' else False
            })
        elif line.startswith('    Total:'):
            current_class['total'] = line.split(':')[-1].strip()
    # Add the final file, class, function and variable to the output
    if current_function:
        current_class['methods'].append(current_function)
    if current_class:
        current_file['classes'].append(current_class)
    if current_file:
        output.append(current_file)
    return output


def explain_cohesion(file_structure):
    issues = []
    messages = []
    for file in file_structure:
        for class_ in file['classes']:
            for method in class_['methods']:
                if method['cohesion_percentage'] and float(method['cohesion_percentage'].strip('%')) > 50:
                    issues.append({
                        'filename': file['filename'],
                        'class': class_['name'],
                        'method': method['name'],
                        'message': f"In the '{method['name']}' method of the '{class_['name']}' class in the file '{file['filename']}', it seems like the code could be improved for better readability and maintainability. You might consider breaking the method into smaller, more focused methods that handle specific tasks, or moving some of the code to other methods. This will make the code easier to understand, modify, and extend."
                    })


    if issues:
        message = "After checking your code, we found the following potential issues:\n"
        #print("After checking your code, we found the following potential issues:")
        for issue in issues:
            message += f"- {issue['message']}\n"
            #print(f"- {issue['message']}")
    else:
        message =  "No issues found in your code!"
    messages.append(message)
    return messages[0]
