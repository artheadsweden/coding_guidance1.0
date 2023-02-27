import subprocess

def _run_pytest(path, flags):
    try:
        pytest_cmd = ['pytest', f'-{flags}', path]
        output = subprocess.check_output(pytest_cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            output = e.output.decode('utf-8')
        if e.returncode == 4:
            return {
                'test_run': 0,
                'test_passed': 0,
                'test_failed': 0,
                'passed_tests': [],
                'failed_tests': [],
                'percentage_passed': 0,
            }
        if e.returncode == 5:
            output = e.output.decode('utf-8')   
    else:
        output = output.decode('utf-8')
        
    if 'TOTAL' in output:
        return  output.split('TOTAL')[1].splitlines()[0].strip().split(' ')[-1]
    failures = []
    if 'FAILURES' in output:
        fails = output.split('FAILURES')[1].splitlines()
        for line in fails:
            if line.startswith('____'):
                l = [l.strip() for l in line.split('__') if l and len(l) > 1]
                failures.append(l[0])
        
    passes = []
    if 'PASSES' in output:
        _pass = output.split('PASSES')[1].splitlines()
        for line in _pass:
            if line.startswith('PASSED'):
                passes.append(line.split('::')[-1].strip())
        
    return {
        'test_run': len(failures) + len(passes),
        'test_passed': len(passes),
        'test_failed': len(failures),
        'passed_tests': passes,
        'failed_tests': failures,
        'percentage_passed': 0 if len(passes) + len(failures) == 0 else round(len(passes) / (len(failures) + len(passes)) * 100, 2),
    }
    
    
def run_pytest(path):
    run_result = _run_pytest(path, 'rA')
    print(run_result)
    total_cov = _run_pytest(path, '-cov=check2')
    print(total_cov)
    return {
        'test_run': run_result['test_run'],
        'test_passed': run_result['test_passed'],
        'test_failed': run_result['test_failed'],
        'passed_tests': run_result['passed_tests'],
        'failed_tests': run_result['failed_tests'],
        'percentage_passed': run_result['percentage_passed'],
        'total_coverage': total_cov
    }