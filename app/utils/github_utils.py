import requests
from datetime import datetime
import uuid
import os
import stat
import subprocess

TOKEN = ''
TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

def get_invites_from_user(username):
    url = 'https://api.github.com/user/repository_invitations'
    headers = {'Authorization': 'token ' + TOKEN}
    repository_invites = requests.get(
                url, headers=headers).json()
    invities = []
    for repository_invite in repository_invites:
        inviter = repository_invite.get('inviter').get('login')
        if inviter == username:
            invite = {
                'id': repository_invite.get('id'),
                'url': repository_invite.get('url'),
                'repository': repository_invite.get('repository').get('full_name'),
                'inviter': username,
            }
            invities.append(invite)
    return invities

def get_github_user(username):
    url = f'https://api.github.com/users/{username}'
    headers = {'Authorization': 'token ' + TOKEN}
    response = requests.get(
                url, headers=headers).json()
    return response    

def get_github_repos(username):
    url = f'https://api.github.com/users/{username}/repos?per_page=1000'
    headers = {'Authorization': 'token ' + TOKEN}
    repos = requests.get(
                url, headers=headers)


    user_repos = [
        {
            'name': repo.get('name'),
            'full_name': repo.get('full_name'),
            'description': repo.get('description'),
            'url': repo.get('html_url'),
            'language': repo.get('language'),
            'languages_url': repo.get('languages_url'),
            'contributors_url': repo.get('contributors_url'),
            'clone_url': repo.get('clone_url'),
            'created_at': datetime.strptime(repo.get('created_at'), TIME_FORMAT),
            'updated_at': datetime.strptime(repo.get('updated_at'), TIME_FORMAT),
            'pushed_at': datetime.strptime(repo.get('pushed_at'), TIME_FORMAT),
            'size': repo.get('size'),
        }
        for repo in repos.json() if repo]
    return user_repos      

def accept_invite(invite_id):
    url = f'https://api.github.com/user/repository_invitations/{invite_id}'
    headers = {'Authorization': 'token ' + TOKEN, 'Accept': 'application/vnd.github.v3+json'}
    response = requests.patch(
                url, headers=headers)
    return response.status_code



def get_file_from_repo(repo_name, file_path):
    url = f'https://api.github.com/repos/{repo_name}/contents/{file_path}'
    headers = {'Authorization': 'token ' + TOKEN}
    response = requests.get(
                url, headers=headers).json()
    return response

def get_repo_brances(github_user, repo):
    url = f'https://api.github.com/repos/{github_user}/{repo}/branches'
    headers = {'Authorization': 'token ' + TOKEN}
    return requests.get(
        url, headers=headers).json()


def get_commits_for_branch(github_user, repo, branch):
    url = f'https://api.github.com/repos/{github_user}/{repo}/commits?sha={branch}'
    headers = {'Authorization': 'token ' + TOKEN}
    return requests.get(
        url, headers=headers).json()
    

def get_selected_repos(github_user, repos):
    found_repos = []
    for repo in repos:
        repo = repo.replace(' ', '')
        url = f'https://api.github.com/repos/{github_user}/{repo}'
        headers = {
            'Authorization': 'token ' + TOKEN,
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        response = requests.get(
                    url).json()
        branches = get_repo_brances(github_user, repo)
        default_branch_commits = get_commits_for_branch(github_user, repo, response['default_branch'])
        if isinstance(default_branch_commits, dict):
            commit = []
        else:
            commit = default_branch_commits[0]

        if len(commit) > 0:
            latest_commit = {
                'committer_avatar': commit['committer']['avatar_url'],
                'committer_name': commit['commit']['committer']['name'],
                'committer_email': commit['commit']['committer']['email'],
                'message': commit['commit']['message'],
                'commit_date': datetime.strptime(commit['commit']['committer']['date'], TIME_FORMAT),
            }
        else:
            latest_commit = {
                'committer_avatar': 'static/img/unknown.png',
                'committer_name': 'N/A',
                'committer_email': 'N/A',
                'message': 'N/A',
                'commit_date': 'N/A',
            }
        repo_data = {
            'name': response['name'],
            'html_url': response['html_url'],
            'description': response['description'] if len(commit) > 0 else default_branch_commits['message'],
            'fork': response['fork'],
            'created_at': datetime.strptime(response['created_at'], TIME_FORMAT),
            'pushed_at': datetime.strptime(response['pushed_at'], TIME_FORMAT),
            'language': response['language'] if len(commit) > 0 else'N/A',
            'default_branch': response['default_branch'],
            'size': response['size'],
            'latest_commit': latest_commit,
            'branches': branches,
            'empty': len(commit) == 0

        }
        found_repos.append(repo_data)
    return found_repos


def clone_to(repo_url, destination_dir):
    directory = str(uuid.uuid4())
    path = os.path.join(destination_dir, directory)
    os.mkdir(path)
    subprocess.run(['git', 'clone', repo_url, path])
    return path


def get_latest_commit_hash(git_repo_path):
    # Change the working directory to your Git repository's path
    cmd = "git log -1 --format=%H"
    try:
        output = subprocess.check_output(cmd.split(), cwd=git_repo_path)
        commit_hash = output.strip().decode('utf-8')
        return commit_hash
    except subprocess.CalledProcessError:
        return None

def cleanup(path):
    import shutil
    shutil.rmtree(path, onerror=hard_cleaner)


def hard_cleaner(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


def get_latest_github_commit_hash(repo_owner, repo_name, branch):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/branches/{branch}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        commit_hash = response.json()["commit"]["sha"]
        return commit_hash
    else:
        return None

if __name__ == '__main__':
    print(get_latest_commit_hash('C:\\tmp\\3405faee-8eb5-4b82-9451-ab02e0ce20ba'))
    # path = clone_to('https://github.com/artheadsweden/an_ig_proj', '/tmp')
    # #print(path)
    # import time
    # time.sleep(5)
    # cleanup(path)
    # res = get_selected_repos('artheadsweden', ['an_ig_proj', 'a_g_proj', 'a_g_proj'])
    #
    # print(get_commits_for_branch('artheadsweden', 'an_ig_proj', 'master'))
    #
    # print()