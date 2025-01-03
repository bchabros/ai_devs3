import os
import logging
from typing import Dict
from anthropic import Anthropic


def process_text_files(folder_path: str) -> Dict[str, str]:
    """
    Process all .txt files in the given folder and create a dictionary with filenames and their content.

    Args:
        folder_path: Path to the folder containing text files

    Returns:
        Dictionary with filename as key and file content as value
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    result_dict = {}

    try:
        # Check if folder exists
        if not os.path.exists(folder_path):
            logging.error(f"Folder {folder_path} does not exist")
            raise FileNotFoundError(f"Folder {folder_path} not found")

        logging.info(f"Starting to process files in {folder_path}")

        # List all files in the folder
        files = os.listdir(folder_path)
        logging.info(f"Found {len(files)} files in total")

        # Process each .txt file
        txt_files = [f for f in files if f.endswith(".txt")]
        logging.info(f"Found {len(txt_files)} .txt files")

        for filename in txt_files:
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    result_dict[filename] = content
                    logging.info(f"Successfully processed {filename}")
            except Exception as e:
                logging.error(f"Error processing {filename}: {str(e)}")

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise

    logging.info(
        f"Processing completed. Processed {len(result_dict)} files successfully"
    )
    return result_dict


def use_llm(
    text_dict: Dict[str, str], anthropic_api_key: str, prompt: str
) -> Dict[str, list]:
    """
    Extract keywords from text using Anthropic API.

    Args:
        text_dict: Dictionary with filename as key and content as value
        anthropic_api_key: Anthropic API key
        prompt: prompt for llm

    Returns:
        Dictionary with filename as key and list of keywords as value
    """
    client = Anthropic(api_key=anthropic_api_key)
    keywords_dict = {}

    for filename, content in text_dict.items():
        try:
            message = client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=300,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt.format(content=content, filename=filename),
                    }
                ],
            )

            # Access the content correctly from the response
            names = [k.strip() for k in message.content[0].text.split(",")]
            keywords_dict[filename] = names
            logging.info(f"Successfully extracted keywords from {filename}")

        except Exception as e:
            logging.error(f"Failed to extract keywords from {filename}: {str(e)}")
            keywords_dict[filename] = []

    return keywords_dict


def match_keywords(keyword_report: dict, keyword_facts: dict) -> dict:
    """
    Match reports with facts based on shared keywords and combine their keywords into string.
    """
    matches = {}

    for report_file, report_keywords in keyword_report.items():
        for facts_file, facts_keywords in keyword_facts.items():
            if set(report_keywords) & set(facts_keywords):
                # Combine unique keywords and join into string
                combined_keywords = list(set(report_keywords + facts_keywords))
                matches[report_file] = ", ".join(combined_keywords)

    return matches


def combine_matching_files(names_facts, names_report, facts_content, report_content):
    """
    Combines content from matching files where names are the same and not "Brak"
    Preserves non-matching files in the output.
    Logs which files were combined.
    """
    combined = {}
    names_to_fact_files = {}
    names_to_report_files = {}

    print("\nMatching files process started...")

    # First, copy all report content to the output
    combined.update(report_content)

    # Build name to file mappings
    for file, names in names_facts.items():
        if names[0] != "Brak":
            names_to_fact_files[names[0]] = file

    for file, names in names_report.items():
        if names[0] != "Brak":
            names_to_report_files[names[0]] = file

    # Process matches
    matches = 0
    for name in set(names_to_fact_files.keys()) & set(names_to_report_files.keys()):
        fact_file = names_to_fact_files[name]
        report_file = names_to_report_files[name]

        print(f"\nFound match for {name}:")
        print(f"- Fact file: {fact_file}")
        print(f"- Report file: {report_file}")

        combined[report_file] = report_content[report_file] + facts_content[fact_file]
        print("Files combined successfully")
        matches += 1

    print(f"\nTotal matches found: {matches}")
    print(f"Total files in output: {len(combined)}")
    return combined
