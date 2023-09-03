from textbase import bot, Message
from textbase.models import OpenAI
from typing import List
from dotenv import load_dotenv
import os
import openai
import requests
import json
import re
from collections import Counter
load_dotenv()

# Load your OpenAI API key

openai.api_key = os.getenv('OPENAI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')


def fetch_user_repositories(user_url):
    username = user_url.split('/')[-1]  # Extract the username from the URL
    response = requests.get(f'https://api.github.com/users/{username}/repos',
                            headers={'Authorization': f'token {GITHUB_TOKEN}'})
    if response.status_code == 200:
        return response.json()
    else:
        print("Error response from GitHub API:", response.text)
        return []


def analyze_complexity_with_gpt(repo_detail):
    repo_detail_str = json.dumps(repo_detail)
    message = [
        {"role": "system", "content": "you are an ai assistant your job is to find the complexity of  Github repositories of user."},
        {"role": "system", "content": "you are provided with information like repo_id , description ,language, size ,stargazers_count ,watchers_count ,forks_count ,open_issues_count,line of code, contribution count, library used,commits count  "},
        {"role": "system", "content": "analyze all the provided information and give a complexity score , the higher the score the more complex the repository is, the score should be between 1-100"},
        {"role": "system", "content": "only return a number between 1 to 100 no texts"},       
        {"role": "user", "content": "repo_id , description ,language, size ,stargazers_count ,watchers_count ,forks_count ,open_issues_count,line of code, contribution count, library used,commits count  "},
        {"role": "assistant", "content": "make observations check the complxity of language used see discription size and all other values provided and return complexity score, the higher the number the higher the complexity"},
        {"role": "user", "content": repo_detail_str}
    ]


    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0.2,
        max_tokens=2,
        messages=message
    )
    return response['choices'][0]['message']['content']

def generate_repo_report(repository_data):
    repo_report = {}

    for repo in repository_data:
        repo_id = repo['id']
        owner_login = repo['owner']['login']
        repo_name = repo['name']
        repo_link = f"https://github.com/{owner_login}/{repo_name}"  # Constructing the repository link
        description = repo['description']
        language = repo['language']
        size = repo['size']
        stargazers_count = repo['stargazers_count']
        watchers_count = repo['watchers_count']
        forks_count = repo['forks_count']
        open_issues_count = repo['open_issues_count']

        # Additional attributes that might indicate complexity
        commits_count = get_commits_count(repo_name, owner_login)
        contributors_count = get_contributors_count(repo_name, owner_login)
        libraries_used = get_libraries_used(repo_name, owner_login)
        lines_of_code = get_lines_of_code(repo_name, owner_login)
        # Create a dictionary with relevant information for the repository
        repo_info = {
            "name": repo_name,
            "description": description,
            "language": language,
            "size": size,
            "stargazers_count": stargazers_count,
            "watchers_count": watchers_count,
            "forks_count": forks_count,
            "open_issues_count": open_issues_count,
            "commits_count": commits_count,
            "contributors_count": contributors_count,
            "libraries_used": libraries_used,
            "lines_of_code": lines_of_code,
        }

        # Store the repository information in the report dictionary
        repo_report[repo_link] = repo_info

    return repo_report


def get_commits_count(repo_name, owner):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/commits"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        commits = response.json()
        return len(commits)
    else:
        return 0


def get_contributors_count(repo_name, owner):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/contributors"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        contributors = response.json()
        return len(contributors)
    else:
        return 0


def get_lines_of_code(repo_name, owner):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/stats/code_frequency"
    response = requests.get(url)

    if response.status_code == 200:
        code_frequency = response.json()
        total_lines_added = sum(entry[1] for entry in code_frequency)
        total_lines_deleted = sum(entry[2] for entry in code_frequency)
        total_lines_of_code = total_lines_added - total_lines_deleted
        return total_lines_of_code
    else:
        return None  # Failed to fetch lines of code


def get_libraries_used(repo_name, owner):
    url = f"https://api.github.com/repos/{owner}/{repo_name}/contents"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

    libraries_used = Counter()  # Using Counter to count library occurrences

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        contents = response.json()
        for item in contents:
            if item["type"] == "file" and item["name"].endswith(".py"):
                file_url = item["download_url"]
                file_contents = requests.get(file_url).text
                imports = re.findall(r'^\s*import\s+([\w\d_]+)', file_contents, re.MULTILINE)
                for library in imports:
                    libraries_used[library] += 1
    else:
        print("Error:", response.text)

    return libraries_used


repo_scores = {}


def starter(user_url):
    print("url se extract kr rhe h")
    repositories = fetch_user_repositories(user_url)

    # Save the repositories data as a JSON file
    with open("repositories_data.json", "w") as json_file:
        json.dump(repositories, json_file, indent=4)

    print("repo extracted")

    # Convert repo to repo description dictionary to be given to prompt
    repo_desc = generate_repo_report(repositories)

    print("repo desc extracted")

    if not repositories:
        return "No repositories found for the provided user URL.", 0

   
    else:
        print("to calc repo score")

        # Initialize an empty dictionary for storing repository scores
        repo_scores = {}
        p_Score = 0
        top_repos = {}  # List to store the top repositories
        l=0
        for repo_link, repo_info in repo_desc.items():
            # Analyze complexity with GPT and store it in the dictionary
            score = int(analyze_complexity_with_gpt(repo_info))
            repo_scores[repo_link] = score
        
            print(repo_link, repo_scores[repo_link])
            
            if score >= 30:
                p_Score += score  # Only add scores >= 30 to profile score
                l=l+1
            # Add to top_repos list if it's one of the top repositories
            if not top_repos or score > min(top_repos.values()):
                top_repos[repo_link] = score

        # Filter out repositories with a score less than 30
        top_repos = {link: score for link, score in top_repos.items() if score >= 30}

        # Sort the top repositories by score in descending order
        top_repos = dict(sorted(top_repos.items(), key=lambda x: x[1], reverse=True))

        # Calculate profile score by summing all repository scores >= 30 and dividing by the count
        profile_score = p_Score / l

        # Get the most complex repository
        most_complex_repo = max(repo_scores, key=repo_scores.get)

        return f"The most complex repository is: {most_complex_repo} with a score of  {repo_scores[most_complex_repo]}\n\nProfile Score : {profile_score:.2f}\n\n", top_repos



@bot()
def on_message(message_history: List[Message], state: dict = None):

   
    user_message = message_history[-1]['content'][0]['value']
    if "github.com" in user_message:
        a, b = starter(user_message)
        bot_response = f"{a}\n"
        bot_response += f"\nTop Repositories : \n"
        count = 0

        for repo, score in b.items():
            bot_response += f"{repo} - Score: {score:.2f}\n"
            count += 1
            if count >= 3:
                break

    else:    
        #bot_response = "please give the url to your github profile"
        message = [
        {"role": "system", "content": "your only purpose is to greet the user and ask the user to provide the github profile url or respond to relative queires "},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Welcome to the git analyser bot. I am here to help you find out more about your github profile. Please provide the github profile url"},
        {"role": "user", "content": user_message}
        ]

        response = openai.ChatCompletion.create(
                model="gpt-4",
                temperature=0.8,
                max_tokens=50,
                messages=message)
        bot_response = response['choices'][0]['message']['content']
    response = {
        "data": {
            "messages": [
                {
                    "data_type": "STRING",
                    "value": bot_response
                }
            ],
            "state": state
        },
        "errors": [
            {
                "message": ""
            }
        ]
    }

    return {
        "status_code": 200,
        "response": response
    }