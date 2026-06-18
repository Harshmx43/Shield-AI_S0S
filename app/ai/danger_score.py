from app.ai.transcribe import transcribe_from_base64
from app.ai.distress_nlp import analyze_transcript

# ─── Danger Level Thresholds ─────────────────────────────────────────────────
DANGER_LEVELS = {
    'CRITICAL': 80,
    'HIGH': 60,
    'MEDIUM': 40,
    'LOW': 0
}

def get_danger_level(score):
    if score >= DANGER_LEVELS['CRITICAL']:
        return 'CRITICAL'
    elif score >= DANGER_LEVELS['HIGH']:
        return 'HIGH'
    elif score >= DANGER_LEVELS['MEDIUM']:
        return 'MEDIUM'
    else:
        return 'LOW'

def analyze_biometrics(heart_rate, fall_detected, struggle_detected):
    """Analyze wearable biometric data"""
    score = 0
    reasons = []

    if heart_rate > 150:
        score += 25
        reasons.append(f'Extreme heart rate: {heart_rate} BPM')
    elif heart_rate > 120:
        score += 15
        reasons.append(f'Elevated heart rate: {heart_rate} BPM')

    if fall_detected:
        score += 20
        reasons.append('Sudden fall detected by wearable')

    if struggle_detected:
        score += 20
        reasons.append('Struggle/resistance pattern detected')

    return score, reasons

def analyze_case(data):
    """
    Main danger scoring function.
    Combines: audio NLP + biometrics + trigger type

    Scoring breakdown:
    - Panic button trigger:     +30 pts (base)
    - Wearable trigger:         +20 pts (base)
    - Witness trigger:          +15 pts (base)
    - Keywords found:           up to +45 pts
    - Panic speech patterns:    +20 pts
    - High heart rate:          up to +25 pts
    - Fall detected:            +20 pts
    - Struggle detected:        +20 pts
    Max possible:               ~175 pts (capped at 100)
    """

    total_score = 0
    all_reasons = []
    transcript = data.get('transcript', '')

    # ── Base score from trigger type ──────────────────────────────────────────
    trigger_type = data.get('trigger_type', 'panic')
    if trigger_type == 'panic':
        total_score += 30
        all_reasons.append('Manual panic button activated')
    elif trigger_type == 'wearable':
        total_score += 20
        all_reasons.append('Wearable auto-triggered')
    elif trigger_type == 'witness':
        total_score += 15
        all_reasons.append('Witness reported danger')

    # ── Audio / NLP Analysis ──────────────────────────────────────────────────
    if data.get('audio_url') and not transcript:
        try:
            transcript = transcribe_from_url(data['audio_url'])
        except Exception as e:
            print(f"Transcription failed: {e}")

    if transcript:
        nlp_result = analyze_transcript(transcript)
        total_score += nlp_result['keyword_score']
        total_score += nlp_result['panic_score']

        if nlp_result['keywords_found']:
            all_reasons.append(f"Distress keywords: {', '.join(nlp_result['keywords_found'][:3])}")
        if nlp_result['has_panic_patterns']:
            all_reasons.append('Panic speech patterns detected in audio')
    else:
        nlp_result = {'keywords_found': []}

    # ── Biometrics Analysis ───────────────────────────────────────────────────
    bio_score, bio_reasons = analyze_biometrics(
        heart_rate=data.get('heart_rate', 0),
        fall_detected=data.get('fall_detected', False),
        struggle_detected=data.get('struggle_detected', False)
    )
    total_score += bio_score
    all_reasons.extend(bio_reasons)

    # ── Cap score at 100 ──────────────────────────────────────────────────────
    final_score = min(total_score, 100)
    danger_level = get_danger_level(final_score)

    return {
        'score': final_score,
        'level': danger_level,
        'reasons': all_reasons,
        'keywords': nlp_result.get('keywords_found', []),
        'transcript': transcript
    }
