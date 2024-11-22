import os
from dotenv import load_dotenv
from src.s_03.e_01 import process_text_files, use_llm, combine_matching_files
from src.send_task import send
from src.prompt.s01e03 import NAMES_PROMPT, KEYWORD_PROMPT


if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("API_KEY")
    endpoint = f"{os.environ['CENTRALA_URL']}report"

    try:
        report = process_text_files("/Users/Chabi/Desktop/ai_devs/pliki_z_fabryki")
        facts = process_text_files("/Users/Chabi/Desktop/ai_devs/pliki_z_fabryki/facts")
        print(report)
        print(facts)

        names_report = use_llm(report, os.getenv("ANTHROPIC_API_KEY"), NAMES_PROMPT)
        names_facts = use_llm(facts, os.getenv("ANTHROPIC_API_KEY"), NAMES_PROMPT)

        final_data = combine_matching_files(names_facts, names_report, facts, report)

        results = use_llm(final_data, os.getenv("ANTHROPIC_API_KEY"), KEYWORD_PROMPT)

        for filename in results:
            results[filename] = ", ".join(results[filename])

        res = send(endpoint, task="dokumenty", apikey=api_key, answer=results)
        print(res)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
