import loggingimport jsonfrom src.send_task import sendfrom src.s_05.e_02 import GPSAgent, API_KEY, ENDPOINTdef main():    agent = GPSAgent()    try:        # Get and analyze the task        question = agent.get_question()        # Let the agent solve it        result = agent.solve_task(question)        # Log and output results        agent.log_interaction("Final Results", None, result)        print(json.dumps(result, indent=4))        res = send(ENDPOINT, task="gps", apikey=API_KEY, answer=result)        print(res)    except Exception as e:        logging.error(f"Error in main execution: {e}")        if hasattr(agent, 'results_file'):            agent.log_interaction("Error", None, str(e))        raise    finally:        if hasattr(agent, 'results_file'):            agent.results_file.close()if __name__ == "__main__":    main()