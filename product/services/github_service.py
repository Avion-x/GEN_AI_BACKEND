
from github import Github
from datetime import datetime
import requests
from github import Github, BadCredentialsException, UnknownObjectException
from product.services.generic_services import validate_mandatory_checks
from user.models import Customer


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
    files = file['commit'].files or [file]
    return {
        "url" : file['commit'].url,
        "html_url" : file['commit'].html_url,
        "sha" : file['commit'].sha,
        "file": [{
            "git_url" : _file['content'].git_url,
            "download_url" : _file['content'].download_url,
            "sha" : _file['content'].sha,
            "url" : _file['content'].url
            } for _file in files]
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


class CustomGithub(Github):
    validation_checks = {
        "access_key": {
            "is_mandatory": True,
            "type": str,
            "convert_type": False,
        },
        "branch": {
            "is_mandatory": True,
            "type": str,
            "convert_type": False,
        },
        "repository": {
            "is_mandatory": True,
            "type": str,
            "convert_type": False,
        },
    }

    def __init__(self, *args, **kwargs):
        try:
            input_params = validate_mandatory_checks(input_data=kwargs, checks=self.validation_checks)
            access_token = input_params.get('access_key')
            super().__init__(access_token)
            self.access_key = input_params.get('access_key')
            self.branch = input_params.get('branch')
            self.repository = input_params.get('repository')          
            self.repo = self.get_repo(self.repository)
        except Exception as e:
            print(f"Error in initializing Github object: {e}")
            raise e
        
    def set_defaults(self, customer):
        try:
            if isinstance(customer, Customer):
                data = customer.data
        except Exception as e:
            print(f"Error in setting defaults: {e}")
            raise e
        
    def validate_inputs(self):
        try:
            # Check if the branch exists
            if self.branch not in [b.name for b in self.repo.get_branches()]:
                return {'error': f"Branch '{self.branch}' does not exist in the repository '{self.repository}'", "status": 400}
            return {"status":True, "access_key": self.access_key, "branch": self.branch, "repository": self.repository}
        except Exception as e:
            return {"error": e, "status": 400}
        
    def push_to_github(self, data = "", file_path = None, comment = None,):
        try:
            if file_path is None:
                current_datetime = datetime.now()
                file_path = current_datetime.strftime("%Y-%m-%d %H:%M:%S") + ".md"
            if comment is None:
                comment = f"{file_path} uploaded to Github using GEN_AI project"

            try:
                file = self.repo.get_contents(file_path, ref=self.branch)
                # Update the file content
                file = self.repo.update_file(
                    path=file_path,
                    message=comment,
                    content=data,
                    branch=self.branch,
                    sha=file.sha
                )
            except:
                # File does not exist, create the file
                file = self.repo.create_file(
                    path=file_path,
                    message=comment,
                    content=data,
                    branch=self.branch
                )
            files = file['commit'].files or [file]
            return {
                "url" : file['commit'].url,
                "html_url" : file['commit'].html_url,
                "sha" : file['commit'].sha,
                "file": [{
                    "git_url" : _file['content'].git_url,
                    "download_url" : _file['content'].download_url,
                    "sha" : _file['content'].sha,
                    "url" : _file['content'].url
                    } for _file in files]
            }
        except Exception as e:
            print(f"Error in pushing file to Github: {e}")
            return {"error": e, "status": 400}
