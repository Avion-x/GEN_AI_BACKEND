
from github import Github
from datetime import datetime
import requests


g = Github('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')

def push_to_github(branch='main', data = "", file_path = None, repo = 'Avion-x/AI_GEN_TEST_CASES', comment = None,):
    if file_path is None:
        current_datetime = datetime.now()
        file_path = current_datetime.strftime("%Y-%m-%d %H:%M:%S") + ".md"
    if comment is None:
        comment = f"{file_path} uploaded to Github using GEN_AI project"
    repo = g.get_repo(repo)
    try:
        file = repo.get_contents(file_path, ref=branch)
        # Update the file content
        file = repo.update_file(
            path=file_path,
            message=comment,
            content=data,
            branch=branch,
            sha=file.sha
        )
    except:
        # File does not exist, create the file
        file = repo.create_file(
            path=file_path,
            message=comment,
            content=data,
            branch=branch
        )
    return file['content'].url
    return f"successfully uploaded file {file_path} to Github"

def get_commits_for_file(file_path = None, repo = 'Avion-x/AI_GEN_TEST_CASES'):
    repo = g.get_repo(repo)
    commits = repo.get_commits(path=file_path)
    commit_list = []
    for commit in commits:
        commit_info = {
            'sha': commit.sha,
            'author': commit.author.login if commit.author else "Unknown",
            'date': commit.commit.author.date.strftime('%Y-%m-%d %H:%M:%S'),
            'message': commit.commit.message,
            "url": commit.html_url,
        }
        commit_list.append(commit_info)
    return commit_list

def get_changes_in_file(file_path = None, repo = 'Avion-x/AI_GEN_TEST_CASES',  commit_sha = ''):
    repo = g.get_repo(repo)
    file_content = repo.get_contents(file_path, ref=commit_sha)
    raw_url = file_content._download_url.value
    response = requests.get(raw_url)
    return response.text

def get_files_in_commit(repo = 'Avion-x/AI_GEN_TEST_CASES', branch_name = 'main'):
    repo = g.get_repo(repo)
    branch = repo.get_branch(branch_name)
    commits = repo.get_commits(sha=branch.commit.sha)
    commit_list = []
    for commit in commits:
            # Get the files associated with each commit
            files = []
            commit_files = commit.files

            for file in commit_files:
                files.append(file.filename)

            commit_list.append({
                'sha': commit.sha,
                'author': commit.author.login if commit.author else "Unknown",
                'date': commit.commit.author.date.strftime('%Y-%m-%d %H:%M:%S'),
                'message': commit.commit.message,
                'url': commit.html_url,
                'files': files,
            })
    return commit_list
