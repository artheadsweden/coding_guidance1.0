from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, logout_user, current_user
from app.utils.github_utils import get_github_repos, get_selected_repos, clone_to, cleanup, get_latest_commit_hash, get_latest_github_commit_hash
from app import User
from app.utils.analyzers.check_driver import gather_data, summerize_report_html
from datetime import datetime


user_bp = Blueprint('user', __name__, template_folder='templates')


@user_bp.get('/main')
@login_required
def user_main():
    repos_count = len(current_user.repos)
    repos_analyzed = len(current_user.reports)
    if repos_analyzed > 0:
        date, time = sorted([(r['analyze_date'], r['analyze_time']) for r in current_user.reports])[0]
        last_check = f'{date} {time}'
    else:
        last_check = 'N/A'
    return render_template('user_main.html', repos_count=repos_count, repos_analyzed=repos_analyzed, last_check=last_check)


@user_bp.get('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('open.index'))


@user_bp.get('/repos')
def repos():
    user_repos = get_github_repos(current_user.github_username)
    user = User.find(github_username=current_user.github_username).first_or_none()
    repos_selected = [repo['name'] for repo in user.repos]
    return render_template('select_repos.html', repos=user_repos, selected_repos=repos_selected)


@user_bp.post('/pick_repos')
def pick_repos():
    picked_repos = request.form.getlist('repo')
    current_user.repos = get_selected_repos(current_user.github_username, picked_repos)
    current_user.save()
    return redirect(url_for('user.user_main'))


@user_bp.get('/selected_repos')
def selected_repos():
    user = User.find(github_username=current_user.github_username).first_or_none()
    return render_template('selected_repos.html', repos=user.repos)


@user_bp.post('/analyze')
def post_analyze():
    user = User.find(github_username=current_user.github_username).first_or_none()
    repo_name = request.form.get('repo_name')
    db_repo = [r for r in user.repos if r['name'] == repo_name][0]
    default_branch = db_repo['default_branch']
    db_reports = [r for r in user.reports if r['repo_name'] == repo_name]
    if len(db_reports) > 0:
        latest_hash = get_latest_github_commit_hash(user.github_username, repo_name, default_branch)
        report = [rep for rep in db_reports if rep['latest_commit_hash'] == latest_hash]
        if len(report) > 0:
            return render_template('report.html', html_summary=report[0]['html_summary'], report=report[0]['report'])
    repo_url = request.form.get('repo_url')
    path = clone_to(repo_url, '/tmp')
    report = gather_data(path)
    html_summary = summerize_report_html(report)
    commit_hash = get_latest_commit_hash(path)
    user.reports.append(
        {
            'analyze_date': datetime.today().strftime('%Y-%m-%d'),
            'analyze_time': datetime.today().strftime('%H:%M:%S'),
            'latest_commit_hash': commit_hash,
            'repo_name': repo_name,
            'repo_url': repo_url,
            'report': report,
            'html_summary': html_summary
        }
    )
    user.save()
    return render_template('report.html', html_summary=html_summary, report=report)