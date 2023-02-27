from radon.raw import analyze
from radon.visitors import ComplexityVisitor
from radon.metrics import h_visit, mi_visit
from radon.complexity import cc_rank
import os

def generate_radon_metrics(code_input):
    radon_metrics = {}

    # raw metrics
    raw_metrics = analyze(code_input)
    radon_metrics['loc'] = raw_metrics.loc
    radon_metrics['lloc'] = raw_metrics.lloc
    radon_metrics['sloc'] = raw_metrics.sloc
    radon_metrics['comments'] = raw_metrics.comments
    radon_metrics['multi'] = raw_metrics.multi
    radon_metrics['single_comments'] = raw_metrics.single_comments

    # cyclomatic complexity
    cc = ComplexityVisitor.from_code(code_input)
    radon_metrics['function_num'] = len(cc.functions)
    total_function_complexity = 0.0
    cc_funcs = []
    for fun in cc.functions:
        total_function_complexity += fun.complexity
        cc_funcs.append({
            'function_name': fun.name,
            'full_name': fun.fullname,
            'is_method': fun.is_method,
            'start_line': fun.lineno,
            'end_line': fun.endline,
            'letter': fun.letter,
            'complexity': fun.complexity
        })
    radon_metrics['total_function_complexity'] = total_function_complexity
    radon_metrics['radon_functions_complexity'] = cc.functions_complexity
    radon_metrics['function_breakdown'] = cc_funcs

    # calculate based on AST tree
    visit = h_visit(code_input)
    radon_metrics['functions'] = [
        {
            'name': func[0],
            'halstead_report':
            {
                 'h1': func[1].h1,
                 'h2': func[1].h2,
                 'N1': func[1].N1,
                 'N2': func[1].N2,
                 'bugs': func[1].bugs,
                 'calculated_length': func[1].calculated_length,
                 'difficulty': func[1].difficulty,
                 'effort': func[1].effort,
                 'length': func[1].length,
                 'time': func[1].time,
                 'vocabulary': func[1].vocabulary,
                 'volume': func[1].volume
             }
         }
        for func in visit.functions
    ]

    # Maintainability Index (MI) based on
    ## the Halstead Volume, the Cyclomatic Complexity, the SLOC number and the number of comment lines
    mi = mi_visit(code_input, multi=True)
    radon_metrics['Maintainability_Index'] = mi

    return radon_metrics

def get_radon_metrics(path):
    f = []
    for root, dirs, _files in os.walk(path):
        if '.git' in dirs:
            dirs.remove('.git')
        for file in _files:
            if file.endswith('.py'):
                f.append(os.path.join(root, file))
                
    radon_report = []
    for file in f:
        filename, file_extension = os.path.splitext(os.path.basename(file))
        file_data = {
            'file_name': filename + file_extension
        }
        path = os.path.join(os.getcwd(), file)

        # Radon complexity report
        visitor = ComplexityVisitor.from_code(open(path).read())
        radon_cc = cc_rank(visitor.complexity)

        # Radon halstead metrics
        radon_metrics = generate_radon_metrics(open(path).read())
        file_data['radon_complexity'] = radon_cc
        file_data['radon_metrics'] = radon_metrics
        radon_report.append(file_data)
    return radon_report

def get_complexity_text(cc_score):
    if cc_score <= 5:
        return "simple and easy to understand"
    if cc_score <= 10:
        return "well structured and easy to understand"
    if cc_score <= 20:
        return "slightly complex"
    if cc_score <= 30:
        return "rather complex"
    if cc_score <= 40:
        return "alarmingly complex"
    else:
        return "error-prone and difficult to maintain"

def generate_radon_text(metrics):
    message = "<p>When looking at your code we found some issues.</p>"
    issues_found = False
    
    for module_metrics in metrics:
        file_name = module_metrics['file_name']
        maintainability_index = module_metrics['radon_metrics']['Maintainability_Index']
        total_function_complexity = module_metrics['radon_metrics']['total_function_complexity']
        function_breakdown = module_metrics['radon_metrics']['function_breakdown']

        if maintainability_index < 50:
            issues_found = True
            message += f"<p>In the module named <b>'{file_name}'</b>, your code may be difficult to maintain due to a low maintainability index of {maintainability_index:.2f}. This means that it may be challenging for future developers to understand and modify this code. Please consider taking steps to improve its maintainability.</p>>"
        good_functions = []
        for function in function_breakdown:
            function_name = function['full_name']
            function_complexity = function['complexity']
            
            if function_complexity >= 10:
                issues_found = True
                message += f"<p>In function '{function_name}', the complexity is {function_complexity}. This indicates that this code is {get_complexity_text(function_complexity)}. Consider refactoring.</p>"
            else:
                good_functions.append(function_name)
        message += f"<p>In the module {file_name} the functions {','.join(good_functions)} is either {get_complexity_text(1)} or {get_complexity_text(11)}. That is very good.</p>"
        if total_function_complexity >= 50:
            issues_found = True
            message += f"<p>In module '{file_name}', the total complexity of all functions is {total_function_complexity}. Consider refactoring.</p>"

        if not issues_found:
            message += f"<p>No issues found in module '{file_name}'.</p>"
    
    if not issues_found:
        message += "<p>Your code looks great! No issues found.</p>"
    else:
        message += "<p>Please check these problems to make your code more readable and maintainable.</p>"
    
    return message
