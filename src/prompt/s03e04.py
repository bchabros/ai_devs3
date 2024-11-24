INITIAL_PROMPT = """Your task is to locate Barbara Zawadzka by analyzing information from multiple sources:1. A text note about Barbara2. An API endpoint (/people) that returns cities where a person has been seen3. An API endpoint (/places) that returns people seen in a given city<rules>Important notes:- Names and cities should be queried without Polish characters (e.g., SLASK instead of ŚLĄSK)- Names should be in nominative case- You give only names (do not add surnames) example if in data is Aleksander Nowak you should give target ALEKSANDER- The data from APIs might be incomplete- You need to combine information from all sources- In final answer you have give the city Name - Do not set BARBARA as Target you won't get any information- Remember you have limited number of iteration you can check in prompt "Remember, you have {remaining} queries remaining".</rules><target>Your goal is to find the city where Barbara is most likely located.</targetWhat would be your first step to gather the necessary information? Do not try directly solve the problem try to find connections and this will help you find solution.Remember to format your response with:ACTION: (people/places - which API to query)REASONING: (why you're making this query)TARGET: (name or city to query)IS_FINAL: (true/false - have you found Barbara's location?)"""SYSTEM_PROMPT = """<objective>Your task is to determine the likely location of a person (BARBARA).</objective><tools>Available resources:1. A note containing information about various people and cities/2. Access to a database query tool (query_db) for information about people and places.3. Task instructions with guidelines/</tools><instruction>Task requirements:- Analyze the note to identify mentioned people and city names- Query the API about discovered clues- Be aware that API responses may contain additional names of people or cities- Continue querying systematically until you locate BARBARA's city- Once you identify the city where BARBARA is located, send the city name to headquarters (/report) for the 'loop' task- IMPORTANT: The city name must be in the exact format returned by the API (e.g., 'LODZ' not 'Łódź'). Submissions with diacritical marks will not be accepted.Key tips:- This task cannot be solved with a single prompt - it requires iterative querying- Avoid infinite loops in your questioning pattern- When querying the API, use nominative case without Polish diacritical marks  Examples:   - Use 'SLASK' not 'ŚLĄSKIEGO'  - Use 'GRZESIEK' not 'GRZEŚKOWI'</instruction><Note>{note}</Note>Using the above information, query the database about people and places to locate BARBARA's whereabouts.Pay careful attention to API responses as they may contain additional crucial information that will help you find the target.The history of previous queries and responses will be provided in system messages.Return the message "DONE" when you believe you have found BARBARA's location."""