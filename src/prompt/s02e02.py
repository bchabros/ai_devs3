IMAGE_PROMPT = """
    <objective>
    Identify the Polish city based on historical aerial/map view fragments from pre-1945 period.
    </objective>

    <context>
    - Images show German-style street layouts and naming conventions from pre-1945 period
    - Focus areas include granary districts and commercial zones
    - Street patterns and intersections are key identifying features
    - Historical Polish cities often had distinctive warehouse/granary districts
    </context>

    <analysis_requirements>
    1. Examine street names and their language/etymology
    2. Analyze street layout patterns and angles
    3. Note any distinctive landmarks or buildings
    4. Consider proximity to waterways/ports if visible
    5. Identify architectural features typical of specific Polish regions
    6. Look for evidence of medieval urban planning
    7. It is not any big city like Warsaw, Gdańsk or Cracow
    </analysis_requirements>

    <output_rules>
    - Return only the modern Polish city name
    - No explanatory text or reasoning
    - Single word response only
    - Use current official Polish spelling
    </output_rules>
    """

# PROMPT = """
# <objective>
# Your task is to answer on question which part of city in Poland represents this aerial view.
# Answer only city names.
# </objective>
#
# <rules>
# - This is an aerial view of city in Poland of course it is a small part of this City.
# - Please analyze this image and tell me what city do you think this is (as an answer just give me name of a City).
# - Take your time analysis the street names and relation between them.
# - The city had granaries in its history.
# - The given fragments of the map will be encoded text in base64.
# - DO NOT ADD ANY ADDITIONAL TEXT JUST GIVE ONLY CITY NAME NOTHING ELSE.
# </rules>
# """
