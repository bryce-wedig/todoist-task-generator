# todoist-task-generator

Bryce's tool for creating Todoist tasks with relative due dates

# Setup

1. Create a file `secrets.json` at the root:
```
{
    "todoist_api_token": "{your Todoist API token}"
}
```
2. Duplicate `task_loaders/example.csv` in the `task_loaders` directory and customize it
3. Install dependencies from `requirements.txt`
4. Run the script