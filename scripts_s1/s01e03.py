import osimport loggingimport jsonfrom dotenv import load_dotenvfrom langfuse import Langfusefrom langfuse.decorators import observefrom src.poligon import sendfrom src.s_01.e_03 import DataRepairParserload_dotenv()key = os.environ.get("API_KEY")url_base = os.environ.get("CENTRALA_URL")json_url = f"{url_base}data/{key}/json.txt"verification_url = f"{url_base}report"langfuse = Langfuse(    secret_key=os.environ["LANGFUSE_SECRET_KEY"],    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],    host=os.environ["LANGFUSE_HOST"],)@observe()def main():    logging.basicConfig(level=logging.INFO)    if not os.path.exists("parsed_data.json"):        parser = DataRepairParser(json_url)        repaired = parser.repair()        parsed = parser.prepare_for_verification(repaired)        with open("parsed_data.json", "w") as f:            f.write(parsed)    else:        logging.info("Using cached data")        parsed = open("parsed_data.json").read()    res = send(verification_url, task="JSON", apikey=key, answer=json.loads(parsed))    print(res)if __name__ == "__main__":    main()