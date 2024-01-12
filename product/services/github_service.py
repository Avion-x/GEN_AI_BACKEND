
from github import Github
from datetime import datetime


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