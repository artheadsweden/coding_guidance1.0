from app.utils.analyzers.cohesion_check import check_cohesion, explain_cohesion
from app.utils.analyzers.prospector_check import run_prospector, explain_prospector
from app.utils.analyzers.radon_check import get_radon_metrics, generate_radon_text
from app.utils.analyzers.flake8_check import run_flake8
from app.utils.analyzers.pytest_check import run_pytest

def gather_data(path):
    report = {}
    
    cohesion_result = check_cohesion(path)
    cohesion_text = explain_cohesion(cohesion_result)
    #print(cohesion_text[0])
    report['cohesion_result'] = cohesion_result
    report['cohesion_text'] = cohesion_text
    
    prospector_result = run_prospector(path)
    prospector_text = explain_prospector(prospector_result)
    
    report['prospector_result'] = prospector_result
    report['prospector_text'] = prospector_text
    
    radon_result = get_radon_metrics(path)
    radon_text = generate_radon_text(radon_result)
    report['radon_result'] = radon_result
    report['radon_text'] = radon_text
        
    flake8_result = run_flake8(path)
    report['flake8_result'] = flake8_result
    
    pytest_result = run_pytest(path)
    report['pytest_result'] = pytest_result

    return report

def summerize_report_html(report, include_grade=True):
    grade_points = 0
    msg = '<h3>Summary of our analysis</h3>'
    msg += '<p>We looked at your code and here is a summary of what we found</p>'
    msg += '<h5>Code quality</h5>'
    msg += '<p>We looked at your code quality.</p>'
    prospector = report['prospector_result']
    prospector_total_issues = prospector['summary']['issue_count']
    
    if prospector_total_issues == 0:
        msg += '<p>Great job! Your code is very clean and well written</p>'
        grade_points += 10
    elif prospector_total_issues < 10:
        msg += '<p>Your code is mostly clean and well written, but there are a few issues that you should look into.</p>'
    else:
        msg += '<p>Your code is not very clean and well written. You should look into that.</p>'
        grade_points -= 10
    
    msg += '<h5>Code cohesion</h5>'
    msg += '<p>Code cohesion is how well your classes is structured.</p>'
    cohesion_classes = [cls['classes'] for cls in report['cohesion_result'] if len(cls['classes']) >= 1]
    cohesion_perstages = [float(c['total'].split('%')[0]) for cls in cohesion_classes for c in cls]
    if len(cohesion_classes) == 0:
        msg += '<p>We could not find any classes in your code. Not all programs need classes, but you could consider adding some to make your code cleaner.</p>'
        grade_points += 2
    elif len(cohesion_classes) == 1:
        if cohesion_perstages[0] > 75:
            msg += '<p>We found one class in your code. The quality of the code in this class looks good</p>'
            grade_points += 5
        else:
            msg += '<p>We found one class in your code. The quality of the code in this class is not very good. Check if you can break apart complext methods so that they only do one thing. A long complex method is hard to read. It is better to use several smaller methods that have a sinlge task each.</p>'
            grade_points -= 5
    else:
        avg_cohesion = sum(cohesion_perstages) / len(cohesion_perstages)
        if avg_cohesion > 75:
            msg += '<p>We found several classes in your code. The quality of the code in these classes looks good</p>'
            grade_points += 7
        else:
            msg += '<p>We found several classes in your code. The quality of the code in these classes is not very good. Check if you can break apart complext methods so that they only do one thing. A long complex method is hard to read. It is better to use several smaller methods that have a sinlge task each.</p>'
            grade_points -= 7
    
    msg += '<h5>Code Readabillity and Maintainabillity</h5>'
    msg += '<p>We have also looked at how easy your code is to read and maintain. High quality code should be both easy to read and maintain.</p>'
    
    cds = 0
    for item in report['radon_result']:
        if item['radon_complexity'] not in 'AB':
            cds += 1
    if cds == 0:
        msg += '<p>Your code is very easy to read and maintain. Great job!</p>'
        grade_points += 5
    else:
        msg += '<p>Your code is not very easy to read and maintain. Many if-statements and for-loops, especialy nested, makes the code complex and it can be hard to follow the logic. Look over your code and rewrite it.</p>'
        grade_points -= 7
    
    
    
    msg += '<h5>Potentiel bugs</h5>'
    msg += '<p>We looked for potential bugs in your code. Here is what we found</p>'
    
    bugs = None
    for item in report['flake8_result']:
        if item['flag'] == 'B':
            bugs = item['issues']
    if len(bugs) > 0:
        msg += '<p>We found some potential bugs in your code. This does not mean that you acctually have bugs in your code, but you have used the language in a way that might lead to bugs, wrong results, or even crashes. You should check this out and rewrite the parts of your code that might be error prone.</p>'
        grade_points -= 15
    else:
        msg += '<p>We did not find any potential bugs in your code. Great job!</p>'
        
    msg += '<h5>Code Tests</h5>'
    msg += '<p>We looked for tests in your code. Here is what we found</p>'
    
    if report['pytest_result']['test_run'] == 0:
        msg += '<p>We could not find any tests for your code. Maybe it would be a good idea to write some tests.</p>'
        grade_points += 5
    else:
        if report['pytest_result']['percentage_passed'] == 100:
            msg += '<p>All your tests passed. Great job!</p>'
            grade_points += 10
        else:
            msg += '<p>Some of your tests failed. Maybe you should look into that?</p>'
            grade_points -= 10

    if include_grade:
        grade = 'IG' if grade_points < 0 else 'G' if grade_points < 10 else 'VG'
        msg += f'<h3>Your grade is: <span class="{"text-danger" if grade_points < 0 else "text-secondary" if grade_points < 10 else "text-success"}">{grade}</span></h3>'
        msg += f'<p>The grade is calculated from a grade score generated from positive and negative metrics in your code</p><p>Your code got a score of <span class="{"text-danger" if grade_points < 0 else "text-secondary" if grade_points < 10 else "text-success"}">{grade_points}</span>.</p>'
        msg += '<p>Here are the limits used in grading:</p>'
        msg += '<ul><li>IG - A negative score</li><li>G - A score between 0 and 9</li><li>VG - A score of 10 or above</li></ul>'
    return msg




