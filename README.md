# C-RAG

## Introduction

Th e codebase of C-RAG structures it contains 3 RAG Pipelines:
- Classic C-RAG 
- Self C-RAG
- Adaptive RAG

### General information

- This project uses conda as an environment manager. The user must have Anaconda or Miniconda installed.
- This project uses git-hooks to check code quality when creating commits.

### Repository

- https://github.com/bchabros/C_RAG.git

### Local env setup

#### 1. Conda

- Install conda (miniconda version): https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html
- Install conda (anaconda navigator version): https://anaconda.org/anaconda/conda
- Make sure conda directory (`C:\Users\<USER>\AppData\Local\miniconda3`) or (`C:\Users\<USER>\AppData\Local\conda`) is added to PATH environment variable in Windows
- Create conda environment from `env.yaml`: `conda env create -f env.yaml`
- Activate environment: `conda activate CRAG`

#### 2. .env file

- Create `.env` file in the project's root directory (based on .env-sample file). The content of `.env` is not stored in Git repository, because it contains secrets.

#### 3. PyCharm settings

- Edit Run/Debug configurations in PyCharm and make sure to select the correct `.env` file and conda environment
- In PyCharm choose `File -> Settings -> Python interpreter` and select `CRAG` environment

#### 4. Upload chroma vectorstore

Before started using [main.py](main.py) you have to use [ingestion.py](ingestion.py) which create vector store based on three links. Of course, you can use your own links as well.

#### 5. Main File:

[main.py](main.py) - It's based on basic streamlit library so to run app you have to run command `streamlit run main.py`

#### 5. RAG Algorithm
- **C-RAG** - the rag which grade documents if they relevant them use them, or it is not then use websearch (tavily to find additional information).         
![graph_1.png](png/graph_1.png)
- **Self C-RAG** - similar to previous one but self check if info from websearch was useful and model does hallucinate if yes then repeat until he won't get accept that it use relevant info and did not hallucinate.   
![graph_2.png](png/graph_2.png)
- **Adaptive Self C-RAG** - devlop on first check so If question is about something about LLM then check document otherwise it will pass this process and use only websearch.   
![graph_3.png](png/graph_3.png)

#### 6. LangGraph Studio
In repo is [langgraph.json](langgraph.json) which is compatible with LangGraph Studio: https://blog.langchain.dev/langgraph-studio-the-first-agent-ide/


