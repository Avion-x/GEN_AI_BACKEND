
from github import Github
from datetime import datetime


g = Github('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')

def push_to_github(branch='main', data = "", file_path = None, repo = 'Avion-x/AI_GEN_TEST_CASES', comment = None):
    if file_path is None:
        current_datetime = datetime.now()
        file_path = current_datetime.strftime("%Y-%m-%d %H:%M:%S") + ".md"
    if comment is None:
        comment = f"{file_path} uploaded to Github using GEN_AI project"
    repo = g.get_repo(repo)
    new_file = repo.create_file(file_path, comment, data, branch=branch)
    return new_file['content'].url
    return f"successfully uploaded file {file_path} to Github"