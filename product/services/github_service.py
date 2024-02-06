
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
    return {
        "git_url" : file['content'].git_url,
        "download_url" : file['content'].download_url,
        "sha" : file['content'].sha,
        "url" : file['content'].url
    }
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

def get_changes_in_file(file_name, commit_sha):
    repo = 'Avion-x/AI_GEN_TEST_CASES'
    repo = g.get_repo(repo)
    file_content = repo.get_contents(file_name, ref=commit_sha)
    raw_url = file_content._download_url.value
    response = requests.get(raw_url)
    return response.text

def get_files_in_commit(commit_sha):
    repo = 'Avion-x/AI_GEN_TEST_CASES'
    repo = g.get_repo(repo)
    # Get the commit by SHA
    commit = repo.get_commit(sha=commit_sha)

    # Get the list of files in the commit
    files = commit.files

    # Prepare a list of file names
    file_names = [file.filename for file in files]
    return file_names
