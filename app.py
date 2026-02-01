"""
English Literature Revision Quiz App
Flask application for Class 10 NCERT English Literature MCQ revision
Uses Gemini API for AI-generated questions
"""

from flask import Flask, render_template_string, request, jsonify, session
import google.generativeai as genai
import json
import os
import re
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Gemini API will be configured with user-provided key

# Base directory for content
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pre-extracted content JSON file (created by extract_content.py)
EXTRACTED_CONTENT_FILE = os.path.join(BASE_DIR, "extracted_content", "chapters_content.json")

# Load pre-extracted content if available
EXTRACTED_CONTENT = {}
if os.path.exists(EXTRACTED_CONTENT_FILE):
    try:
        with open(EXTRACTED_CONTENT_FILE, 'r', encoding='utf-8') as f:
            EXTRACTED_CONTENT = json.load(f)
        print(f"✅ Loaded pre-extracted content for {len(EXTRACTED_CONTENT)} chapters")
    except Exception as e:
        print(f"⚠️ Could not load extracted content: {e}")
else:
    print("⚠️ No pre-extracted content found. Run 'python extract_content.py' locally first.")


def get_chapter_context(chapter_id):
    """Get chapter context from pre-extracted JSON content"""
    if chapter_id in EXTRACTED_CONTENT:
        content = EXTRACTED_CONTENT[chapter_id]
        return content.get("book_content", ""), content.get("pyq_content", "")
    return "", ""

# Chapter data for First Flight
FIRST_FLIGHT_CHAPTERS = {
    "prose": [
        {"id": "ff_p1", "name": "A Letter to God", "type": "prose"},
        {"id": "ff_p2", "name": "Nelson Mandela: Long Walk to Freedom", "type": "prose"},
        {"id": "ff_p3", "name": "Two Stories about Flying", "type": "prose"},
        {"id": "ff_p4", "name": "From the Diary of Anne Frank", "type": "prose"},
        {"id": "ff_p5", "name": "Glimpses of India", "type": "prose"},
        {"id": "ff_p6", "name": "Mijbil the Otter", "type": "prose"},
        {"id": "ff_p7", "name": "Madam Rides the Bus", "type": "prose"},
        {"id": "ff_p8", "name": "The Sermon at Benares", "type": "prose"},
        {"id": "ff_p9", "name": "The Proposal", "type": "prose"},
    ],
    "poetry": [
        {"id": "ff_po1", "name": "Dust of Snow & Fire and Ice", "type": "poetry"},
        {"id": "ff_po2", "name": "A Tiger in the Zoo", "type": "poetry"},
        {"id": "ff_po3", "name": "How to Tell Wild Animals & The Ball Poem", "type": "poetry"},
        {"id": "ff_po4", "name": "Amanda!", "type": "poetry"},
        {"id": "ff_po5", "name": "Animals & The Trees", "type": "poetry"},
        {"id": "ff_po6", "name": "Fog & The Tale of Custard the Dragon", "type": "poetry"},
        {"id": "ff_po7", "name": "For Anne Gregory", "type": "poetry"},
    ]
}

# Chapter data for Footprints Without Feet
FOOTPRINTS_CHAPTERS = [
    {"id": "fp_1", "name": "A Triumph of Surgery", "type": "story"},
    {"id": "fp_2", "name": "The Thief's Story", "type": "story"},
    {"id": "fp_3", "name": "The Midnight Visitor", "type": "story"},
    {"id": "fp_4", "name": "A Question of Trust", "type": "story"},
    {"id": "fp_5", "name": "Footprints Without Feet", "type": "story"},
    {"id": "fp_6", "name": "The Making of a Scientist", "type": "story"},
    {"id": "fp_7", "name": "The Necklace", "type": "story"},
    {"id": "fp_8", "name": "The Hack Driver", "type": "story"},
    {"id": "fp_9", "name": "Bholi", "type": "story"},
    {"id": "fp_10", "name": "The Book That Saved the Earth", "type": "story"},
]

def get_all_chapters():
    """Get all chapters organized by book"""
    return {
        "first_flight": FIRST_FLIGHT_CHAPTERS,
        "footprints": FOOTPRINTS_CHAPTERS
    }

def get_chapter_info(chapter_id):
    """Get chapter details by ID"""
    for ch in FIRST_FLIGHT_CHAPTERS["prose"]:
        if ch["id"] == chapter_id:
            return {**ch, "book": "First Flight"}
    for ch in FIRST_FLIGHT_CHAPTERS["poetry"]:
        if ch["id"] == chapter_id:
            return {**ch, "book": "First Flight"}
    for ch in FOOTPRINTS_CHAPTERS:
        if ch["id"] == chapter_id:
            return {**ch, "book": "Footprints Without Feet"}
    return None

def generate_quiz(chapter_id, api_key, num_questions=15):
    """Generate MCQ quiz using Gemini API with actual PDF content"""
    # Configure Gemini API with user-provided key
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    chapter = get_chapter_info(chapter_id)
    if not chapter:
        return None
    
    chapter_type = chapter["type"]
    chapter_name = chapter["name"]
    book_name = chapter["book"]
    
    # Extract PDF content for context
    print(f"Extracting content for: {chapter_name}")
    book_content, pyq_content = get_chapter_context(chapter_id)
    
    # Build context section
    context_section = ""
    if book_content:
        print(f"Book content extracted: {len(book_content)} characters")
        context_section += f"""
=== CHAPTER CONTENT FROM NCERT BOOK ===
{book_content}
=== END OF CHAPTER CONTENT ===
"""
    else:
        print("No book content extracted (PyMuPDF may not be installed)")
    
    if pyq_content:
        print(f"PYQ content extracted: {len(pyq_content)} characters")
        context_section += f"""
=== PREVIOUS YEAR QUESTIONS (LITERATURE SECTION) ===
{pyq_content}
=== END OF PYQ CONTENT ===
"""
    else:
        print("No PYQ content extracted")
    
    # Build comprehensive prompt based on chapter type
    if chapter_type == "poetry":
        prompt = f"""You are an expert CBSE Class 10 English teacher. Generate exactly {num_questions} MCQ questions for the poem(s): "{chapter_name}" from the book "{book_name}".

{context_section}

IMPORTANT: Use the above chapter content and PYQ questions as PRIMARY REFERENCE to create accurate MCQs.
Cover ALL of these aspects thoroughly:
1. POETIC DEVICES: Identify metaphors, similes, personification, alliteration, anaphora, imagery, symbolism, rhyme scheme from the actual poem text
2. DEEP MEANINGS: Central theme, poet's message based on the actual content
3. LINE-BY-LINE ANALYSIS: Important lines from the poem and their meanings
4. KEYWORDS: Important vocabulary from the chapter and their significance
5. POET'S INTENT: What the poet wants to convey
6. TONE & MOOD: The overall feeling of the poem
7. SYMBOLISM: What different elements represent
8. EXTRACT-BASED: Questions on specific stanzas/lines from the poem
9. PYQ PATTERNS: If PYQ content is provided, create similar style questions

For each question, create 4 options where:
- One is clearly correct
- Others are plausible but incorrect distractors

Return ONLY valid JSON in this exact format:
{{
    "questions": [
        {{
            "id": 1,
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": 0,
            "explanation": "Brief explanation of why this is correct and key takeaway",
            "keyword": "Important keyword to remember from this question"
        }}
    ]
}}"""
    else:
        prompt = f"""You are an expert CBSE Class 10 English teacher. Generate exactly {num_questions} MCQ questions for the chapter: "{chapter_name}" from the book "{book_name}".

{context_section}

IMPORTANT: Use the above chapter content and PYQ questions as PRIMARY REFERENCE to create accurate MCQs.
Cover ALL of these aspects thoroughly:
1. CHARACTER SKETCHES: Traits, nature, role of each character AS DESCRIBED in the chapter
2. PLOT EVENTS: Important incidents from the actual chapter content
3. THEMES & MORALS: Central message and life lessons from the story
4. KEYWORDS: Important vocabulary, phrases from the chapter
5. AUTHOR'S PURPOSE: What the author wants to convey
6. IMPORTANT QUOTES: Significant lines from the chapter and who said them
7. SETTINGS: Where and when the story takes place
8. CONFLICTS: Main problems and their resolutions
9. FACTUAL DETAILS: Names, places, specific events from the chapter
10. LONG ANSWER KEYWORDS: Convert key points of long answers into keyword-based MCQs
11. PYQ PATTERNS: If PYQ content is provided, create similar style questions

For each question, create 4 options where:
- One is clearly correct
- Others are plausible but incorrect distractors

Return ONLY valid JSON in this exact format:
{{
    "questions": [
        {{
            "id": 1,
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": 0,
            "explanation": "Brief explanation of why this is correct and key takeaway",
            "keyword": "Important keyword to remember from this question"
        }}
    ]
}}"""

    try:
        # Try different models in order of preference
        models_to_try = ['gemini-2.5-flash-lite','gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
        
        response = None
        last_error = None
        
        for model_name in models_to_try:
            try:
                print(f"Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    break
            except Exception as model_error:
                last_error = model_error
                error_str = str(model_error)
                if "429" in error_str or "quota" in error_str.lower():
                    print(f"Quota exceeded for {model_name}, trying next model...")
                    continue
                elif "not found" in error_str.lower() or "does not exist" in error_str.lower():
                    print(f"Model {model_name} not available, trying next...")
                    continue
                else:
                    raise model_error
        
        if not response or not response.text:
            if last_error:
                raise last_error
            return None
        
        # Extract JSON from response
        response_text = response.text
        print(f"Response received, length: {len(response_text)}")
        
        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*"questions"[\s\S]*\}', response_text)
        if json_match:
            try:
                quiz_data = json.loads(json_match.group())
                # Validate the quiz data
                if 'questions' in quiz_data and len(quiz_data['questions']) > 0:
                    # Ensure correct index is valid
                    for q in quiz_data['questions']:
                        if 'correct' not in q:
                            q['correct'] = 0
                        if 'options' not in q or len(q['options']) < 4:
                            q['options'] = ["Option A", "Option B", "Option C", "Option D"]
                        if q['correct'] >= len(q['options']):
                            q['correct'] = 0
                        if 'explanation' not in q:
                            q['explanation'] = "Review this concept carefully."
                        if 'keyword' not in q:
                            q['keyword'] = "Important concept"
                    return quiz_data
            except json.JSONDecodeError as je:
                print(f"JSON decode error: {je}")
        
        # Fallback: try to parse entire response as JSON
        try:
            quiz_data = json.loads(response_text.strip())
            if 'questions' in quiz_data:
                return quiz_data
        except:
            pass
            
        print("Could not parse quiz data from response")
        return None
        
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return None

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>English Literature Quiz - Class 10</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: rgba(255, 255, 255, 0.03);
            --bg-card-hover: rgba(255, 255, 255, 0.06);
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --accent-primary: #6366f1;
            --accent-secondary: #8b5cf6;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
            --success: #10b981;
            --success-bg: rgba(16, 185, 129, 0.15);
            --error: #ef4444;
            --error-bg: rgba(239, 68, 68, 0.15);
            --warning: #f59e0b;
            --warning-bg: rgba(245, 158, 11, 0.15);
            --border: rgba(255, 255, 255, 0.08);
            --glass: rgba(255, 255, 255, 0.02);
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Animated background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            overflow: hidden;
        }
        
        .bg-animation::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 30%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
                        radial-gradient(circle at 70% 70%, rgba(139, 92, 246, 0.08) 0%, transparent 50%);
            animation: bgMove 20s ease-in-out infinite;
        }
        
        @keyframes bgMove {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            50% { transform: translate(-5%, -5%) rotate(5deg); }
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        header {
            text-align: center;
            padding: 40px 20px;
            margin-bottom: 40px;
        }
        
        .logo {
            font-size: 3rem;
            font-weight: 800;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }
        
        .tagline {
            color: var(--text-secondary);
            font-size: 1.1rem;
            font-weight: 500;
        }
        
        /* API Key Input */
        .api-key-section {
            margin-top: 24px;
            padding: 20px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .api-key-label {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .api-key-input-wrapper {
            display: flex;
            gap: 10px;
        }
        
        .api-key-input {
            flex: 1;
            padding: 12px 16px;
            background: var(--glass);
            border: 2px solid var(--border);
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 0.95rem;
            font-family: inherit;
            transition: all 0.3s ease;
        }
        
        .api-key-input:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
        }
        
        .api-key-input::placeholder {
            color: var(--text-secondary);
            opacity: 0.6;
        }
        
        .api-key-status {
            margin-top: 10px;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .api-key-status.valid {
            color: var(--success);
        }
        
        .api-key-status.invalid {
            color: var(--error);
        }
        
        .api-key-status.pending {
            color: var(--warning);
        }
        
        .api-key-link {
            color: var(--accent-primary);
            text-decoration: none;
            font-size: 0.85rem;
            margin-top: 8px;
            display: inline-block;
        }
        
        .api-key-link:hover {
            text-decoration: underline;
        }
        
        /* Section titles */
        .section-title {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            font-size: 1.4rem;
            font-weight: 700;
        }
        
        .section-title .icon {
            width: 40px;
            height: 40px;
            background: var(--accent-gradient);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }
        
        /* Book sections */
        .book-section {
            margin-bottom: 50px;
        }
        
        .subsection-title {
            color: var(--text-secondary);
            font-size: 0.9rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin: 20px 0 16px;
            padding-left: 5px;
        }
        
        /* Chapter grid */
        .chapters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 16px;
        }
        
        .chapter-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .chapter-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--accent-gradient);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .chapter-card:hover {
            transform: translateY(-4px);
            border-color: var(--accent-primary);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
        }
        
        .chapter-card:hover::before {
            opacity: 0.05;
        }
        
        .chapter-card .content {
            position: relative;
            z-index: 1;
        }
        
        .chapter-number {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--accent-primary);
            background: rgba(99, 102, 241, 0.1);
            padding: 4px 10px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 12px;
        }
        
        .chapter-name {
            font-size: 1.1rem;
            font-weight: 600;
            line-height: 1.4;
        }
        
        .chapter-type {
            margin-top: 12px;
            font-size: 0.8rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .type-icon {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: var(--accent-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.7rem;
        }
        
        /* Quiz screen */
        .quiz-screen {
            display: none;
        }
        
        .quiz-header {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 30px;
        }
        
        .quiz-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .quiz-chapter-name {
            font-size: 1.3rem;
            font-weight: 700;
        }
        
        .quiz-stats {
            display: flex;
            gap: 20px;
        }
        
        .stat {
            text-align: center;
            padding: 10px 20px;
            background: var(--glass);
            border-radius: 12px;
        }
        
        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-primary);
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }
        
        .progress-container {
            margin-top: 20px;
        }
        
        .progress-bar {
            height: 6px;
            background: var(--border);
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--accent-gradient);
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        
        .progress-text {
            margin-top: 8px;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        
        /* Question card */
        .question-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 32px;
            margin-bottom: 24px;
        }
        
        .question-number {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--accent-primary);
            margin-bottom: 16px;
        }
        
        .question-text {
            font-size: 1.25rem;
            font-weight: 600;
            line-height: 1.6;
            margin-bottom: 28px;
        }
        
        .options-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .option {
            padding: 18px 24px;
            background: var(--glass);
            border: 2px solid var(--border);
            border-radius: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .option:hover:not(.disabled) {
            background: var(--bg-card-hover);
            border-color: var(--accent-primary);
            transform: translateX(8px);
        }
        
        .option.disabled {
            cursor: default;
        }
        
        .option.correct {
            background: var(--success-bg);
            border-color: var(--success);
        }
        
        .option.incorrect {
            background: var(--error-bg);
            border-color: var(--error);
        }
        
        .option-letter {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            background: var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
            flex-shrink: 0;
        }
        
        .option.correct .option-letter {
            background: var(--success);
        }
        
        .option.incorrect .option-letter {
            background: var(--error);
        }
        
        .option-text {
            font-size: 1rem;
            line-height: 1.5;
        }
        
        /* Feedback box */
        .feedback-box {
            margin-top: 20px;
            padding: 20px;
            border-radius: 14px;
            display: none;
        }
        
        .feedback-box.show {
            display: block;
            animation: fadeIn 0.3s ease;
        }
        
        .feedback-box.correct {
            background: var(--success-bg);
            border: 1px solid var(--success);
        }
        
        .feedback-box.incorrect {
            background: var(--error-bg);
            border: 1px solid var(--error);
        }
        
        .feedback-title {
            font-weight: 700;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .feedback-box.correct .feedback-title {
            color: var(--success);
        }
        
        .feedback-box.incorrect .feedback-title {
            color: var(--error);
        }
        
        .feedback-text {
            color: var(--text-secondary);
            line-height: 1.6;
        }
        
        .keyword-badge {
            display: inline-block;
            margin-top: 12px;
            padding: 6px 14px;
            background: var(--accent-gradient);
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        /* Buttons */
        .btn-group {
            display: flex;
            gap: 16px;
            margin-top: 24px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 14px 28px;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: var(--accent-gradient);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);
        }
        
        .btn-secondary {
            background: var(--glass);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        
        .btn-secondary:hover {
            background: var(--bg-card-hover);
            border-color: var(--accent-primary);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }
        
        /* Results screen */
        .results-screen {
            display: none;
        }
        
        .results-header {
            text-align: center;
            padding: 40px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 24px;
            margin-bottom: 30px;
        }
        
        .score-circle {
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: var(--accent-gradient);
            margin: 0 auto 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 20px 60px rgba(99, 102, 241, 0.3);
        }
        
        .score-value {
            font-size: 3.5rem;
            font-weight: 800;
        }
        
        .score-label {
            font-size: 1rem;
            opacity: 0.9;
        }
        
        .results-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        
        .results-subtitle {
            color: var(--text-secondary);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 30px;
        }
        
        .stat-card {
            padding: 20px;
            background: var(--glass);
            border-radius: 16px;
            text-align: center;
        }
        
        .stat-card.correct { border-left: 4px solid var(--success); }
        .stat-card.incorrect { border-left: 4px solid var(--error); }
        .stat-card.skipped { border-left: 4px solid var(--warning); }
        
        .stat-card .value {
            font-size: 2rem;
            font-weight: 700;
        }
        
        .stat-card.correct .value { color: var(--success); }
        .stat-card.incorrect .value { color: var(--error); }
        .stat-card.skipped .value { color: var(--warning); }
        
        .stat-card .label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 5px;
        }
        
        /* Analysis sections */
        .analysis-section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 28px;
            margin-bottom: 24px;
        }
        
        .analysis-title {
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .keyword-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .keyword-item {
            padding: 8px 16px;
            background: var(--accent-gradient);
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .mistake-item {
            padding: 20px;
            background: var(--glass);
            border-radius: 14px;
            margin-bottom: 16px;
            border-left: 4px solid var(--error);
        }
        
        .mistake-question {
            font-weight: 600;
            margin-bottom: 12px;
        }
        
        .mistake-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 12px;
        }
        
        .mistake-answer {
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        
        .mistake-answer.wrong {
            background: var(--error-bg);
            color: var(--error);
        }
        
        .mistake-answer.right {
            background: var(--success-bg);
            color: var(--success);
        }
        
        .mistake-explanation {
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.5;
        }
        
        .takeaway-item {
            padding: 16px 20px;
            background: var(--glass);
            border-radius: 12px;
            margin-bottom: 12px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }
        
        .takeaway-icon {
            width: 28px;
            height: 28px;
            background: var(--accent-gradient);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        
        /* Loading overlay */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(10, 10, 15, 0.95);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            flex-direction: column;
            gap: 24px;
        }
        
        .loading-overlay.show {
            display: flex;
        }
        
        .loader {
            width: 60px;
            height: 60px;
            border: 4px solid var(--border);
            border-top-color: var(--accent-primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .loading-text {
            font-size: 1.2rem;
            color: var(--text-secondary);
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .logo { font-size: 2rem; }
            .chapters-grid { grid-template-columns: 1fr; }
            .quiz-info { flex-direction: column; text-align: center; }
            .quiz-stats { justify-content: center; }
            .stats-grid { grid-template-columns: 1fr; }
            .mistake-details { grid-template-columns: 1fr; }
            .question-text { font-size: 1.1rem; }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loader"></div>
        <div class="loading-text">Generating your personalized quiz...</div>
    </div>
    
    <div class="container">
        <!-- Header -->
        <header>
            <h1 class="logo">📚 Literature Quiz</h1>
            <p class="tagline">Class 10 NCERT English Revision • AI-Powered MCQs</p>
            
            <!-- API Key Input Section -->
            <div class="api-key-section">
                <div class="api-key-label">
                    🔑 Enter your Gemini API Key
                </div>
                <div class="api-key-input-wrapper">
                    <input type="password" 
                           id="apiKeyInput" 
                           class="api-key-input" 
                           placeholder="AIza... (your Gemini API key)"
                           autocomplete="off">
                </div>
                <div class="api-key-status pending" id="apiKeyStatus">
                    ⚠️ API key required to generate quizzes
                </div>
                <a href="https://aistudio.google.com/app/apikey" 
                   target="_blank" 
                   class="api-key-link">
                    📋 Get your free API key from Google AI Studio →
                </a>
            </div>
        </header>
        
        <!-- Home Screen -->
        <div id="homeScreen">
            <!-- First Flight Section -->
            <div class="book-section">
                <h2 class="section-title">
                    <span class="icon">✈️</span>
                    First Flight
                </h2>
                
                <h3 class="subsection-title">📖 Prose</h3>
                <div class="chapters-grid" id="firstFlightProse"></div>
                
                <h3 class="subsection-title">🎭 Poetry</h3>
                <div class="chapters-grid" id="firstFlightPoetry"></div>
            </div>
            
            <!-- Footprints Section -->
            <div class="book-section">
                <h2 class="section-title">
                    <span class="icon">👣</span>
                    Footprints Without Feet
                </h2>
                <div class="chapters-grid" id="footprintsChapters"></div>
            </div>
        </div>
        
        <!-- Quiz Screen -->
        <div class="quiz-screen" id="quizScreen">
            <div class="quiz-header">
                <div class="quiz-info">
                    <div>
                        <div class="quiz-chapter-name" id="quizChapterName"></div>
                    </div>
                    <div class="quiz-stats">
                        <div class="stat">
                            <div class="stat-value" id="correctCount">0</div>
                            <div class="stat-label">Correct</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="incorrectCount">0</div>
                            <div class="stat-label">Wrong</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="skippedCount">0</div>
                            <div class="stat-label">Skipped</div>
                        </div>
                    </div>
                </div>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill" style="width: 0%"></div>
                    </div>
                    <div class="progress-text" id="progressText">Question 1 of 15</div>
                </div>
            </div>
            
            <div class="question-card" id="questionCard">
                <div class="question-number" id="questionNumber"></div>
                <div class="question-text" id="questionText"></div>
                <div class="options-list" id="optionsList"></div>
                <div class="feedback-box" id="feedbackBox">
                    <div class="feedback-title" id="feedbackTitle"></div>
                    <div class="feedback-text" id="feedbackText"></div>
                    <div class="keyword-badge" id="keywordBadge"></div>
                </div>
            </div>
            
            <div class="btn-group">
                <button class="btn btn-secondary" id="skipBtn" onclick="skipQuestion()">
                    ⏭️ Skip Question
                </button>
                <button class="btn btn-primary" id="nextBtn" onclick="nextQuestion()" style="display: none;">
                    Next Question →
                </button>
                <button class="btn btn-secondary" onclick="goHome()">
                    🏠 Exit Quiz
                </button>
            </div>
        </div>
        
        <!-- Results Screen -->
        <div class="results-screen" id="resultsScreen">
            <div class="results-header">
                <div class="score-circle">
                    <div class="score-value" id="scorePercent">0%</div>
                    <div class="score-label">Score</div>
                </div>
                <h2 class="results-title" id="resultsTitle">Quiz Completed!</h2>
                <p class="results-subtitle" id="resultsSubtitle"></p>
                
                <div class="stats-grid">
                    <div class="stat-card correct">
                        <div class="value" id="finalCorrect">0</div>
                        <div class="label">Correct Answers</div>
                    </div>
                    <div class="stat-card incorrect">
                        <div class="value" id="finalIncorrect">0</div>
                        <div class="label">Wrong Answers</div>
                    </div>
                    <div class="stat-card skipped">
                        <div class="value" id="finalSkipped">0</div>
                        <div class="label">Skipped</div>
                    </div>
                </div>
            </div>
            
            <!-- Keywords Section -->
            <div class="analysis-section" id="keywordsSection">
                <h3 class="analysis-title">🔑 Keywords to Remember</h3>
                <div class="keyword-list" id="keywordsList"></div>
            </div>
            
            <!-- Mistakes Analysis -->
            <div class="analysis-section" id="mistakesSection">
                <h3 class="analysis-title">❌ Mistakes Review</h3>
                <div id="mistakesList"></div>
            </div>
            
            <!-- Key Takeaways -->
            <div class="analysis-section" id="takeawaysSection">
                <h3 class="analysis-title">💡 Key Takeaways</h3>
                <div id="takeawaysList"></div>
            </div>
            
            <div class="btn-group" style="justify-content: center; margin-top: 30px;">
                <button class="btn btn-primary" onclick="goHome()">
                    🏠 Back to Chapters
                </button>
                <button class="btn btn-secondary" onclick="retryQuiz()">
                    🔄 Retry This Chapter
                </button>
            </div>
        </div>
    </div>
    
    <script>
        // State management
        let currentQuiz = null;
        let currentQuestionIndex = 0;
        let answers = [];
        let currentChapterId = null;
        let currentChapterName = null;
        
        // Chapter data
        const chapters = {{ chapters | tojson }};
        
        // Initialize the app
        document.addEventListener('DOMContentLoaded', function() {
            renderChapters();
        });
        
        function renderChapters() {
            // First Flight Prose
            const proseContainer = document.getElementById('firstFlightProse');
            chapters.first_flight.prose.forEach((ch, idx) => {
                proseContainer.innerHTML += createChapterCard(ch, idx + 1);
            });
            
            // First Flight Poetry
            const poetryContainer = document.getElementById('firstFlightPoetry');
            chapters.first_flight.poetry.forEach((ch, idx) => {
                poetryContainer.innerHTML += createChapterCard(ch, idx + 1);
            });
            
            // Footprints
            const footprintsContainer = document.getElementById('footprintsChapters');
            chapters.footprints.forEach((ch, idx) => {
                footprintsContainer.innerHTML += createChapterCard(ch, idx + 1);
            });
        }
        
        function createChapterCard(chapter, number) {
            const typeIcon = chapter.type === 'poetry' ? '📝' : chapter.type === 'story' ? '📖' : '📚';
            const typeLabel = chapter.type.charAt(0).toUpperCase() + chapter.type.slice(1);
            
            return `
                <div class="chapter-card" onclick="startQuiz('${chapter.id}', '${chapter.name.replace(/'/g, "\\'")}')">
                    <div class="content">
                        <span class="chapter-number">Chapter ${number}</span>
                        <h3 class="chapter-name">${chapter.name}</h3>
                        <div class="chapter-type">
                            <span class="type-icon">${typeIcon}</span>
                            ${typeLabel}
                        </div>
                    </div>
                </div>
            `;
        }
        
        async function startQuiz(chapterId, chapterName) {
            // Get and validate API key
            const apiKeyInput = document.getElementById('apiKeyInput');
            const apiKey = apiKeyInput.value.trim();
            const apiKeyStatus = document.getElementById('apiKeyStatus');
            
            if (!apiKey) {
                apiKeyStatus.className = 'api-key-status invalid';
                apiKeyStatus.innerHTML = '❌ Please enter your Gemini API key first';
                apiKeyInput.focus();
                apiKeyInput.style.borderColor = 'var(--error)';
                setTimeout(() => {
                    apiKeyInput.style.borderColor = '';
                }, 2000);
                return;
            }
            
            if (!apiKey.startsWith('AIza')) {
                apiKeyStatus.className = 'api-key-status invalid';
                apiKeyStatus.innerHTML = '❌ Invalid API key format (should start with "AIza")';
                apiKeyInput.focus();
                return;
            }
            
            currentChapterId = chapterId;
            currentChapterName = chapterName;
            
            // Show loading
            document.getElementById('loadingOverlay').classList.add('show');
            apiKeyStatus.className = 'api-key-status pending';
            apiKeyStatus.innerHTML = '⏳ Validating API key and generating quiz...';
            
            try {
                const response = await fetch('/generate-quiz', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chapter_id: chapterId, api_key: apiKey })
                });
                
                const data = await response.json();
                
                if (data.success && data.quiz) {
                    currentQuiz = data.quiz.questions;
                    currentQuestionIndex = 0;
                    answers = new Array(currentQuiz.length).fill(null);
                    
                    // Setup quiz screen
                    document.getElementById('quizChapterName').textContent = chapterName;
                    document.getElementById('correctCount').textContent = '0';
                    document.getElementById('incorrectCount').textContent = '0';
                    document.getElementById('skippedCount').textContent = '0';
                    
                    // Show quiz screen
                    document.getElementById('homeScreen').style.display = 'none';
                    document.getElementById('quizScreen').style.display = 'block';
                    document.getElementById('resultsScreen').style.display = 'none';
                    
                    renderQuestion();
                } else {
                    alert('Failed to generate quiz. Please try again.');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            } finally {
                document.getElementById('loadingOverlay').classList.remove('show');
            }
        }
        
        function renderQuestion() {
            const question = currentQuiz[currentQuestionIndex];
            const totalQuestions = currentQuiz.length;
            
            // Update progress
            const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100;
            document.getElementById('progressFill').style.width = progress + '%';
            document.getElementById('progressText').textContent = `Question ${currentQuestionIndex + 1} of ${totalQuestions}`;
            document.getElementById('questionNumber').textContent = `Question ${currentQuestionIndex + 1}`;
            document.getElementById('questionText').textContent = question.question;
            
            // Render options
            const optionsList = document.getElementById('optionsList');
            const letters = ['A', 'B', 'C', 'D'];
            optionsList.innerHTML = question.options.map((opt, idx) => `
                <div class="option" data-index="${idx}" onclick="selectOption(${idx})">
                    <span class="option-letter">${letters[idx]}</span>
                    <span class="option-text">${opt}</span>
                </div>
            `).join('');
            
            // Reset UI
            document.getElementById('feedbackBox').classList.remove('show', 'correct', 'incorrect');
            document.getElementById('skipBtn').style.display = 'flex';
            document.getElementById('nextBtn').style.display = 'none';
        }
        
        function selectOption(selectedIndex) {
            const question = currentQuiz[currentQuestionIndex];
            const options = document.querySelectorAll('.option');
            const feedbackBox = document.getElementById('feedbackBox');
            
            // Disable all options
            options.forEach(opt => opt.classList.add('disabled'));
            
            // Mark correct and selected
            const correctIndex = question.correct;
            options[correctIndex].classList.add('correct');
            
            if (selectedIndex !== correctIndex) {
                options[selectedIndex].classList.add('incorrect');
                feedbackBox.classList.add('incorrect');
                document.getElementById('feedbackTitle').innerHTML = '❌ Incorrect';
            } else {
                feedbackBox.classList.add('correct');
                document.getElementById('feedbackTitle').innerHTML = '✅ Correct!';
            }
            
            // Store answer
            answers[currentQuestionIndex] = {
                selected: selectedIndex,
                correct: correctIndex,
                isCorrect: selectedIndex === correctIndex,
                question: question.question,
                options: question.options,
                explanation: question.explanation,
                keyword: question.keyword
            };
            
            // Show feedback
            document.getElementById('feedbackText').textContent = question.explanation;
            document.getElementById('keywordBadge').textContent = '🔑 ' + question.keyword;
            feedbackBox.classList.add('show');
            
            // Update stats
            updateStats();
            
            // Show next button
            document.getElementById('skipBtn').style.display = 'none';
            document.getElementById('nextBtn').style.display = 'flex';
        }
        
        function skipQuestion() {
            answers[currentQuestionIndex] = { skipped: true, keyword: currentQuiz[currentQuestionIndex].keyword };
            updateStats();
            nextQuestion();
        }
        
        function updateStats() {
            const correct = answers.filter(a => a && a.isCorrect).length;
            const incorrect = answers.filter(a => a && a.isCorrect === false).length;
            const skipped = answers.filter(a => a && a.skipped).length;
            
            document.getElementById('correctCount').textContent = correct;
            document.getElementById('incorrectCount').textContent = incorrect;
            document.getElementById('skippedCount').textContent = skipped;
        }
        
        function nextQuestion() {
            if (currentQuestionIndex < currentQuiz.length - 1) {
                currentQuestionIndex++;
                renderQuestion();
            } else {
                showResults();
            }
        }
        
        function showResults() {
            const correct = answers.filter(a => a && a.isCorrect).length;
            const incorrect = answers.filter(a => a && a.isCorrect === false).length;
            const skipped = answers.filter(a => a && a.skipped).length;
            const total = currentQuiz.length;
            const percent = Math.round((correct / total) * 100);
            
            // Update score
            document.getElementById('scorePercent').textContent = percent + '%';
            document.getElementById('finalCorrect').textContent = correct;
            document.getElementById('finalIncorrect').textContent = incorrect;
            document.getElementById('finalSkipped').textContent = skipped;
            
            // Set title based on score
            let title, subtitle;
            if (percent >= 80) {
                title = '🎉 Excellent Performance!';
                subtitle = 'You have a strong grasp of this chapter.';
            } else if (percent >= 60) {
                title = '👍 Good Job!';
                subtitle = 'Review the mistakes to improve further.';
            } else if (percent >= 40) {
                title = '📚 Keep Practicing!';
                subtitle = 'Focus on the keywords and explanations below.';
            } else {
                title = '💪 Don\\'t Give Up!';
                subtitle = 'Review this chapter and try again.';
            }
            document.getElementById('resultsTitle').textContent = title;
            document.getElementById('resultsSubtitle').textContent = subtitle;
            
            // Keywords
            const keywords = answers.filter(a => a && a.keyword).map(a => a.keyword);
            const keywordsList = document.getElementById('keywordsList');
            keywordsList.innerHTML = [...new Set(keywords)].map(kw => 
                `<span class="keyword-item">${kw}</span>`
            ).join('');
            
            // Mistakes
            const mistakes = answers.filter(a => a && a.isCorrect === false);
            const mistakesList = document.getElementById('mistakesList');
            
            if (mistakes.length > 0) {
                document.getElementById('mistakesSection').style.display = 'block';
                mistakesList.innerHTML = mistakes.map(m => `
                    <div class="mistake-item">
                        <div class="mistake-question">${m.question}</div>
                        <div class="mistake-details">
                            <div class="mistake-answer wrong">Your answer: ${m.options[m.selected]}</div>
                            <div class="mistake-answer right">Correct: ${m.options[m.correct]}</div>
                        </div>
                        <div class="mistake-explanation">${m.explanation}</div>
                    </div>
                `).join('');
            } else {
                document.getElementById('mistakesSection').style.display = 'none';
            }
            
            // Key takeaways
            const takeawaysList = document.getElementById('takeawaysList');
            const takeaways = mistakes.length > 0 ? 
                mistakes.slice(0, 5).map(m => m.explanation) :
                ['Great job! You\\'ve mastered this chapter. Consider moving to the next one.'];
            
            takeawaysList.innerHTML = takeaways.map(t => `
                <div class="takeaway-item">
                    <div class="takeaway-icon">💡</div>
                    <div>${t}</div>
                </div>
            `).join('');
            
            // Show results screen
            document.getElementById('quizScreen').style.display = 'none';
            document.getElementById('resultsScreen').style.display = 'block';
        }
        
        function goHome() {
            document.getElementById('homeScreen').style.display = 'block';
            document.getElementById('quizScreen').style.display = 'none';
            document.getElementById('resultsScreen').style.display = 'none';
            currentQuiz = null;
            currentQuestionIndex = 0;
            answers = [];
        }
        
        function retryQuiz() {
            if (currentChapterId && currentChapterName) {
                startQuiz(currentChapterId, currentChapterName);
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    """Render the main page"""
    chapters = get_all_chapters()
    return render_template_string(HTML_TEMPLATE, chapters=chapters)

@app.route('/generate-quiz', methods=['POST'])
def generate_quiz_api():
    """API endpoint to generate quiz for a chapter"""
    data = request.json
    chapter_id = data.get('chapter_id')
    api_key = data.get('api_key')
    
    if not chapter_id:
        return jsonify({'success': False, 'error': 'No chapter ID provided'})
    
    if not api_key:
        return jsonify({'success': False, 'error': 'No API key provided'})
    
    quiz = generate_quiz(chapter_id, api_key)
    
    if quiz:
        return jsonify({'success': True, 'quiz': quiz})
    else:
        return jsonify({'success': False, 'error': 'Failed to generate quiz. Check your API key or quota.'})

if __name__ == '__main__':
    print("🚀 Starting English Literature Quiz App...")
    print("📚 Open http://localhost:5000 in your browser")
    app.run(host="0.0.0.0", debug=True, port=5000)
