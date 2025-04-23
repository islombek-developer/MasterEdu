# quiz_app/ai_utils.py
import os
import json
import random
# pip install openai
from openai import OpenAI
# pip install python-dotenv # Agar .env ishlatsangiz
# from dotenv import load_dotenv
# load_dotenv()

client = None
api_key = "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"

if api_key:
    client = OpenAI(api_key=api_key)
else:
    print("\n\n*** DIQQAT: OPENAI_API_KEY topilmadi! AI generatsiyasi ishlamaydi. ***\n\n")

def generate_questions_via_ai(topic, difficulty, count, question_type='vocabulary'):
    """AI yordamida ingliz tili uchun mavzuga oid savollar generatsiya qiladi."""
    if not client:
        print("AI mijozi (client) sozlanmagan. Generatsiya o'tkazib yuborildi.")
        # Placeholder qaytarish (test uchun)
        questions_data = []
        for i in range(count):
            q_text = f"Placeholder: AI {difficulty} '{question_type}' savol #{i+1} ({topic} haqida)"
            opts = [
                {"text": "Placeholder Correct Answer", "is_correct": True},
                {"text": "Placeholder Option 2", "is_correct": False},
                {"text": "Placeholder Option 3", "is_correct": False},
                {"text": "Placeholder Option 4", "is_correct": False},
            ]
            random.shuffle(opts)
            questions_data.append({"text": q_text, "difficulty": difficulty, "answers": opts})
        return questions_data

    prompt = f"""
    Generate {count} multiple-choice English language questions suitable for a student with '{difficulty}' level proficiency.
    The main topic must be: "{topic}".
    Focus the questions on '{question_type}'.

    For each question:
    1. Provide concise question text.
    2. Provide EXACTLY 4 answer options (A, B, C, D).
    3. Clearly indicate EXACTLY ONE correct answer.
    4. Options should be plausible but distinct.
    5. Language must match the '{difficulty}' level.

    Return ONLY a valid JSON list of objects. Each object MUST have this structure:
    {{
        "question_text": "The question...",
        "options": [
            {{"text": "Option A text", "is_correct": false}},
            {{"text": "Option B text", "is_correct": true}},
            {{"text": "Option C text", "is_correct": false}},
            {{"text": "Option D text", "is_correct": false}}
        ]
    }}
    No other text, explanations, or formatting outside the JSON list. Ensure exactly one 'is_correct' is true per question. Vary correct answer position.
    """

    print(f"--- Sending Prompt to AI ---\nTopic: {topic}, Difficulty: {difficulty}, Count: {count}, Type: {question_type}\n---")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Yoki "gpt-4o", "gpt-4"
            messages=[
                {"role": "system", "content": "You are an expert English language teacher assistant creating quiz questions in JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
             response_format={ "type": "json_object" } # JSON formatni talab qilish (agar model qo'llasa)
        )

        ai_response_content = response.choices[0].message.content
        print(f"--- AI Raw Response ---\n{ai_response_content}\n---")

        try:
            # API response_format=json_object ni qo'llasa, to'g'ridan-to'g'ri json.loads qilish mumkin
             questions_data = json.loads(ai_response_content)
             # Javob list ekanligini tekshirish
             if not isinstance(questions_data, list):
                  # Ba'zan AI listni object ichiga o'rashi mumkin (masalan, {"questions": [...]})
                  # Agar shunday bo'lsa, listni topishga harakat qilish
                  if isinstance(questions_data, dict) and len(questions_data.keys()) == 1:
                      key = list(questions_data.keys())[0]
                      if isinstance(questions_data[key], list):
                           questions_data = questions_data[key]
                      else:
                           raise ValueError("AI response is a dict, but does not contain a list.")
                  else:
                    raise ValueError("AI response is not a JSON list.")

        except (json.JSONDecodeError, ValueError) as e:
             # Agar JSON to'g'ri kelmasa, qo'lda topishga urinish (oxirgi chora)
             print(f"Warning: Direct JSON parsing failed ({e}). Trying manual extraction.")
             json_start = ai_response_content.find('[')
             json_end = ai_response_content.rfind(']') + 1
             if json_start != -1 and json_end != 0:
                 json_str = ai_response_content[json_start:json_end]
                 try:
                     questions_data = json.loads(json_str)
                 except json.JSONDecodeError as e2:
                     print(f"Xatolik: AI javobini JSON sifatida o'qib bo'lmadi (manual): {e2}")
                     print(f"Olingan javob: {ai_response_content}")
                     return []
             else:
                 print(f"Xatolik: AI javobida JSON list topilmadi.")
                 print(f"Olingan javob: {ai_response_content}")
                 return []

        # Validatsiya
        validated_data = []
        for i, q_data in enumerate(questions_data):
            if isinstance(q_data, dict) and 'question_text' in q_data and 'options' in q_data and isinstance(q_data['options'], list) and len(q_data['options']) == 4:
                valid_options = []
                correct_count = 0
                for opt in q_data['options']:
                    if isinstance(opt, dict) and 'text' in opt and 'is_correct' in opt:
                        is_correct_bool = bool(opt['is_correct'])
                        valid_options.append({"text": str(opt['text']), "is_correct": is_correct_bool})
                        if is_correct_bool:
                            correct_count += 1
                    else:
                        print(f"Warning: Invalid option format skipped in question {i+1}: {opt}")
                        valid_options = []
                        break # Bu savolning qolgan variantlarini tekshirishni to'xtatish

                if valid_options and correct_count == 1:
                    validated_data.append({
                        "text": str(q_data['question_text']),
                        "difficulty": difficulty,
                        "answers": valid_options
                    })
                elif valid_options and correct_count != 1:
                     print(f"Warning: Question {i+1} ('{q_data.get('question_text')[:30]}...') skipped due to {correct_count} correct answers (expected 1).")
                # else: (agar valid_options bo'sh bo'lsa, xabar yuqorida chiqdi)
            else:
                print(f"Warning: Invalid question structure skipped (item {i+1}): {q_data}")

        print(f"--- Parsed and Validated AI Data ({len(validated_data)} questions) ---")
        return validated_data

    except Exception as e:
        print(f"Xatolik: AI bilan bog'lanishda yoki generatsiyada muammo: {e}")
        return []