from setuptools import setup, find_packages

setup(
    name="my-backend",       # Change this to whatever you want to call the package
    version="1.0.0",         # Since it's completed, start at 1.0.0!
    description="My completed backend API and core logic",
    python_requires=">=3.12", # Based on your __pycache__ folders
    
    # This automatically finds 'api', 'config', and 'src' (and their subfolders)
    packages=find_packages(exclude=[
        "venv*",             # NEVER install your virtual environment
        "data*",             # Usually generated at runtime, skip it
        "logs*",             # Generated at runtime, skip it
        "*__pycache__*",     # Skip compiled python files
    ]),
    
    # Your dependencies
    install_requires=[
        "requests",
        "mysql-connector-python",
        "python-dotenv",
        "openai",
        "sqlglot",
        "langchain_openai",
        "langchain_core",
        "langchain_chroma",
        "langchain_ollama",
        "fastapi",
    ],
    
    # This is crucial: It tells pip to grab your hidden .env files 
    # and put them inside the installed 'config' folder
    package_data={
        "config": [".azure.env", ".mysql.env", ".openwebui.env"]
    },
)