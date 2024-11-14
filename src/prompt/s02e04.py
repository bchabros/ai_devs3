prompt_text = """
<objective>
Analyze daily report and classify as "people", "hardware", or "neither".
</objective>

<criteria>
PEOPLE only if:
- Direct reports of caught/captured individuals
- Physical evidence of unauthorized presence (footprints, belongings)
- Security breaches with confirmed human intrusion

HARDWARE if:
- Physical equipment repairs
- Hardware malfunction reports
- Hardware maintenance logs
DO NOT include software-related issues

NEITHER for:
- Failed searches for people
- General mentions of humans/staff/workers
- Administrative reports
- Software issues
- All other content not matching above criteria exactly

IMPORTANT: Mentions of people/humans alone do NOT qualify as "people" category.
Must have direct evidence or captures.
</criteria>

<rules>
- Respond with single word: "people", "hardware", or "neither"
- When uncertain, classify as "neither"
- Ignore software-related content
</rules>

<output_format>
CRITICAL: Return ONLY ONE of these exact words:
- "people"
- "hardware" 
- "neither"

NO additional text, explanation or punctuation allowed.
</output_format>

text:
{text}
"""

prompt_image = """
<objective>
Read and classify image text as "people", "hardware", or "neither".
</objective>

<criteria>
PEOPLE if:
- Reports of caught individuals
- Evidence of human presence
- Signs of intrusion

HARDWARE if:
- Physical equipment repairs
- Hardware malfunction reports
- Hardware maintenance logs
DO NOT include software-related issues

NEITHER if:
- Software-related content
- Administrative reports
- Other unrelated content
- If report is to Boss do not treat him as people
</criteria>

<ocr_guidance>
- Extract all visible text
- Account for image quality issues
- Process tables and structured text
</ocr_guidance>

<rules>
- Respond with single word: "people", "hardware", or "neither"
- When uncertain, classify as "neither"
- Ignore software-related content
</rules>

<output_format>
CRITICAL: Return ONLY ONE of these exact words:
- "people"
- "hardware" 
- "neither"

NO additional text, explanation or punctuation allowed.
</output_format>
"""
