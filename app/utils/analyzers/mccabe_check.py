import mccabe
from mccabe import PathGraphingAstVisitor
import ast
import os

THRESHOLD_LIMIT = 7

def maccabe_complexity(module, threshold):
    code = open(module, 'r').read()
    tree = compile(code, module, "exec", ast.PyCF_ONLY_AST)
    visitor = PathGraphingAstVisitor()
    visitor.preorder(tree, visitor)

    return [(graph.name, graph.complexity()) for graph in visitor.graphs.values() if graph.complexity() >= threshold]

def check_mccabe(path):
    report = []
    for root, dirs, _files in os.walk(path):
        for name in _files:
            if name.endswith('.py'):
                file_data = {
                    'name': name
                }
                path = os.path.join(root, name)
                code = open(path).read()
                file_data['mccabe_cc_score'] = mccabe.get_code_complexity(code, THRESHOLD_LIMIT)
                file_data['mccabe_threshold'] = []
                for t in maccabe_complexity(path, THRESHOLD_LIMIT):
                    threshold = 0 if len(t) < 2 else t[1]
                    threshold_data = t[0].split(':')
                    if len(threshold_data) >= 3:
                        file_data['mccabe_threshold'].append({
                            'line': threshold_data[0],
                            'col': threshold_data[1],
                            'method/function': threshold_data[2].strip().strip("'"),
                            'threshold': threshold,
                            'threshold_limit': THRESHOLD_LIMIT
                        })
            report.append(file_data)
    return report

def analyze_mccabe_metrics(metrics):
    message = "When looking at your code we found some issues.\n"
    issues_found = False
    
    for module_metrics in metrics:
        module_name = module_metrics['name']
        mccabe_cc_score = module_metrics['mccabe_cc_score']
        mccabe_threshold = module_metrics['mccabe_threshold']
        
        if mccabe_cc_score > 5:
            issues_found = True
            message += f"In the module named '{module_name}', your code has a McCabe complexity score of {mccabe_cc_score}, which is above the recommended threshold. This indicates that your code may be too complex and difficult to understand.\n"
            if mccabe_threshold:
                message += f"The following methods/functions in '{module_name}' have complexity scores above the recommended threshold:\n"
                for item in mccabe_threshold:
                    message += f"- '{item['method/function']}' on line {item['line']}, with a score of {item['threshold']}\n"
        else:
            message += f"No issues found in module '{module_name}'.\n"
    
    if not issues_found:
        message += "Your code looks great! No issues found."
    else:
        message += "Please check these problems to make your code more readable and maintainable."
    
    return message