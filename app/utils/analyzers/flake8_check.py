import subprocess


def flake8_exec(path, flag):
    try:
        flake8_cmd = ['flake8', f'--select={flag.upper()}', path]
        output = subprocess.check_output(flake8_cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            output = e.output.decode('utf-8')
    else:
        output = output.decode('utf-8')

    r = []
    for line in output.splitlines():
        line_items = line.split()
        code = line_items[1]
        message = line.split(code + ' ')[-1]
        col = line.split(code + ' ')[0].split(':')[-2]
        row = line.split(code + ' ')[0].split(':')[-3]
        file = line.split(code + ' ')[0].split(':')[-4]
        file = file.replace('\\', '/')
        file = file.split('/')[-1]
        item = {
            'module': file,
            'line': row,
            'col': col,
            'code': code,
            'message': message.capitalize(),
        }
        r.append(item)
    return r

def run_flake8(path):
    result = [
        {
            'flag': 'B',
            'name': 'Bugs',
            'description': 'Possible code smells',
            'issues': []
        },
        {
            'flag': 'E',
            'name': 'StyleErrors',
            'description': 'Style errors',
            'issues': []
        },
        {
            'flag': 'W',
            'name': 'StyleWarnings',
            'description': 'Style warnings',
            'issues': []
        },
        {
            'flag': 'F',
            'name': 'CodeErrors',
            'description': 'Code errors',
            'issues': []
        },
            {
            'flag': 'N',
            'name': 'NamingErrors',
            'description': 'Naming errors',
            'issues': []
        },
        
        
    ]
    for item in result:
        check_result = flake8_exec(path, item['flag'])
        if len(check_result) > 0:
            item['issues'] = check_result
    return result
