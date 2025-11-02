import datetime
import json
import os
import requests
import pandas as pd
from tqdm import tqdm


TODOIST_API_VERSION = "v2"


def get_todoist_header(todoist_api_token):
    return {
        "Authorization": "Bearer " + todoist_api_token,
        "Content-Type": "application/json"
    }


def main():
    # load secrets.json
    secrets_path = os.path.join(os.path.dirname(__file__), "secrets.json")
    try:
        with open(secrets_path, "r") as f:
            secrets = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to read secrets.json at {secrets_path}: {e}")

    # create auth header for Todoist
    todoist_api_token = secrets.get("todoist_api_token")
    if not todoist_api_token:
        raise ValueError("todoist_api_token not found in secrets.json")
    auth_todoist = get_todoist_header(todoist_api_token)

    # query for Todoist projects
    projects_response = requests.get(
        "https://api.todoist.com/rest/" + TODOIST_API_VERSION + "/projects",
        headers=auth_todoist
    )
    if projects_response.status_code == 200:
        print("Projects retrieved successfully.")
    else:
        print("Failed to retrieve projects.")
        return

    # prompt user for project
    projects = projects_response.json()
    for i, project in enumerate(projects):
        print(f"{i + 1}: {project['name']}")
    project_choice = input("Select a project by number: ")
    try:
        selected_project = projects[int(project_choice) - 1]
    except (IndexError, ValueError):
        print("Invalid project selection.")
        return
    print(f'Selected project: {selected_project["name"]}')
    project_id = selected_project['id']

    # prompt user for section name
    section_name = input("What do you want to call the section? ").strip()
    
    # create the section in the selected project
    section_id = None
    if section_name:
        print("Creating Section: " + section_name)
        create_section = requests.post(
            "https://api.todoist.com/rest/" + TODOIST_API_VERSION + "/sections",
            headers=auth_todoist,
            data=json.dumps({
                "name": section_name,
                "project_id": project_id
            }))
        if create_section.status_code == 200:
            print("Section created.")
        create_section_response = create_section.json()
        section_id = create_section_response['id']

    # prompt user for start and end dates
    start_date_string = input("Start date: ").strip()
    end_date_string = input("End date: ").strip()
    try:
        start_date = datetime.datetime.strptime(start_date_string, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid start date. Expected format YYYY-MM-DD.")
        return
    end_date = None
    if end_date_string:
        try:
            end_date = datetime.datetime.strptime(end_date_string, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid end date. Expected format YYYY-MM-DD.")
            return
        if end_date < start_date:
            print("End date must be the same or after start date.")
            return

    # list available task loader files and prompt user to pick one
    task_loaders_dir = os.path.join(os.path.dirname(__file__), "task_loaders")
    if not os.path.isdir(task_loaders_dir):
        print(f"No task_loaders directory found at {task_loaders_dir}")
        return
    loader_files = sorted([f for f in os.listdir(task_loaders_dir) if f.endswith(".csv")])
    if not loader_files:
        print("No task loader files found in task_loaders directory.")
        return
    for i, fname in enumerate(loader_files):
        print(f"{i + 1}: {fname}")
    choice = input("Select a task loader by number: ").strip()
    try:
        selected_fname = loader_files[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return
    selected_loader_path = os.path.join(task_loaders_dir, selected_fname)
    selected_loader_name = os.path.splitext(selected_fname)[0]
    print(f"Selected loader: {selected_loader_name}")

    # read csv
    df = pd.read_csv(selected_loader_path)

    # create list of tasks from csv
    tasks = []
    for i, row in df.iterrows():
        if pd.notna(row['rel_start']):
            rel_start_days = int(row['rel_start'])
            due_date = start_date + datetime.timedelta(days=rel_start_days)
        elif pd.notna(row['rel_end']):
            rel_end_days = int(row['rel_end'])
            due_date = end_date + datetime.timedelta(days=rel_end_days)
        else:
            raise ValueError("Either rel_start or rel_end must be provided in the CSV.")
        tasks.append((row['task_name'], due_date.strftime("%Y-%m-%d")))

    # create tasks in Todoist
    for task, due_string in tqdm(tasks):
        task_data = {
            "content": task,
            "due_string": due_string,
            "project_id": project_id
        }
        if section_id is not None:
            task_data["section_id"] = section_id
        create_task = requests.post(
            "https://api.todoist.com/rest/" + TODOIST_API_VERSION + "/tasks",
            data=json.dumps(task_data),
            headers=auth_todoist
        )
        if create_task.status_code != 200:
            print("ERROR creating task: " + str(task))
            print(create_task.text)
            break


if __name__ == "__main__":
    main()
