import os

from src.s_03.e_02 import DocumentRAG
from src.send_task import send

if __name__ == "__main__":
    # Initialize the QA system
    qa_system = DocumentRAG(
        documents_path="/Users/Chabi/Desktop/ai_devs/pliki_z_fabryki/do-not-share",
        index_name="ai-devs-s02e03",
        refresh=False,  # if True then refresh all vector database
    )

    # Example query
    query = (
        "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
    )
    result = qa_system.query(query)

    answer = str(
        os.path.basename(result["source_documents"][0].metadata["source"])
        .replace(".txt", "")
        .replace("_", "-")
    )

    res = send(
        f"{os.environ.get('CENTRALA_URL')}report",
        task="wektory",
        apikey=os.environ["API_KEY"],
        answer=answer,
    )
    print(res)
