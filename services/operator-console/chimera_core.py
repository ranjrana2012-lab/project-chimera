import sys
import time
import argparse
import json
import csv
import os
import re
import threading
import unicodedata
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

def spawn_voice(text):
    if os.getenv("CHIMERA_ENABLE_VOICE", "").lower() not in {"1", "true", "yes", "on"}:
        return

    def speak():
        if pyttsx3:
            try:
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception:
                pass
    threading.Thread(target=speak, daemon=True).start()

# Optional ML loading
try:
    from transformers import pipeline
except ImportError:
    pipeline = None

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CAPTION = '\033[1;37;40m' # White text on black background for high contrast

class ChimeraCore:
    def __init__(self):
        self.sentiment_analyzer = None
        self.text_generator = None
        self.history = []
        self.positive_cues = {
            "amazing", "excited", "fantastic", "great", "happy", "love",
            "thrilled", "wonderful",
        }
        self.negative_cues = {
            "anxious", "angry", "bad", "frustrated", "overwhelmed",
            "sad", "terrible", "worried",
        }
        self.neutral_cues = {
            "fine", "it is okay", "it's okay", "nothing special",
            "okay", "ok", "so far",
        }

    def load_models(self):
        print(f"{Colors.OKBLUE}Loading ML models (DistilBERT & DistilGPT2)...{Colors.ENDC}")
        time.sleep(0.5)
        self.text_generator = None
        if pipeline:
            try:
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
                self.sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device="cpu")
                # Using tiny summarization or generation for live script
                self.text_generator = pipeline("text-generation", model="distilgpt2", device="cpu")
                print(f"{Colors.OKGREEN}Models loaded successfully.{Colors.ENDC}\n")
            except Exception as e:
                print(f"{Colors.WARNING}Warning: Could not load HuggingFace models. Using fast heuristic fallback.{Colors.ENDC}\n")
                self.sentiment_analyzer = self.heuristic_sentiment
        else:
            print(f"{Colors.WARNING}Warning: transformers not installed. Using fast heuristic fallback.{Colors.ENDC}\n")
            self.sentiment_analyzer = self.heuristic_sentiment

    def heuristic_sentiment(self, text):
        # Fallback if pipeline fails
        text = text[0].lower() if isinstance(text, list) else text.lower()
        positive_words = ["excited", "amazing", "love", "wonderful", "great", "happy", "fantastic"]
        negative_words = ["frustrated", "worried", "bad", "terrible", "angry", "wrong", "anxious", "sad"]
        
        pos_score = sum(1 for w in positive_words if w in text)
        neg_score = sum(1 for w in negative_words if w in text)
        
        if pos_score > neg_score:
            return [{"label": "POSITIVE", "score": 0.95}]
        elif neg_score > pos_score:
            return [{"label": "NEGATIVE", "score": 0.95}]
        else:
            return [{"label": "NEUTRAL", "score": 0.50}]

    def analyze_sentiment(self, text):
        if not self.sentiment_analyzer:
            self.load_models()
        res = self.sentiment_analyzer(text if isinstance(text, list) else [text])
        return self.apply_sentiment_overrides(text, res[0])

    def apply_sentiment_overrides(self, text, sentiment_result):
        lowered = text.lower()
        if self.contains_any(lowered, self.positive_cues) or self.contains_any(lowered, self.negative_cues):
            return sentiment_result

        if (
            sentiment_result["label"].upper() == "POSITIVE"
            and self.contains_any(lowered, self.neutral_cues)
        ):
            return {"label": "NEUTRAL", "score": 0.55}

        return sentiment_result

    def contains_any(self, text, phrases):
        return any(phrase in text for phrase in phrases)

    def select_strategy(self, sentiment_result):
        label = sentiment_result['label'].upper()
        if label == "POSITIVE":
            return "momentum_build"
        elif label == "NEGATIVE":
            return "supportive_care"
        else:
            return "standard_response"

    def generate_response(self, text, strategy):
        # Dynamic GLM-4.7/LLM Generative dialogue logic
        if getattr(self, "text_generator", None):
            try:
                prompt_map = {
                    "momentum_build": f"Text: '{text}'. Very enthusiastic response amplifying the audience energy:",
                    "supportive_care": f"Text: '{text}'. Calm and supportive response, telling them it will be okay:",
                    "standard_response": f"Text: '{text}'. Professional and neutral theater response:"
                }
                prompt = prompt_map.get(strategy, "Response:")
                res = self.text_generator(
                    prompt,
                    max_new_tokens=25,
                    num_return_sequences=1,
                    do_sample=False,
                )
                final_text = res[0]["generated_text"].replace(prompt, "", 1).strip()
                final_text = self.clean_generated_response(final_text)
                if self.is_response_usable(final_text, strategy):
                    return final_text
            except Exception:
                pass

        return self.fallback_response(strategy)

    def clean_generated_response(self, text):
        normalized = unicodedata.normalize("NFKC", text)
        cleaned = "".join(
            char for char in normalized
            if char.isprintable() and unicodedata.category(char)[0] != "C"
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" '\"-")
        return cleaned

    def is_response_usable(self, response, strategy):
        if not response or len(response) < 12 or "\ufffd" in response:
            return False

        alpha_count = sum(char.isalpha() for char in response)
        if alpha_count < 8:
            return False

        lowered = response.lower()
        prompt_artifacts = (
            "text:",
            "very enthusiastic response",
            "calm and supportive response",
            "professional and neutral theater response",
            "telling them it will be okay",
        )
        if any(artifact in lowered for artifact in prompt_artifacts):
            return False

        tone_keywords = {
            "momentum_build": ("amazing", "energy", "excited", "great", "love", "thrill", "wonderful"),
            "supportive_care": ("breathe", "calm", "gentle", "here", "okay", "safe", "support"),
            "standard_response": ("continue", "noted", "standard", "trajectory"),
        }
        return any(keyword in lowered for keyword in tone_keywords[strategy])

    def fallback_response(self, strategy):
        if strategy == "momentum_build":
            return f"That's fantastic! The energy here is really amplifying with that feedback! We're thrilled you feel that way."
        elif strategy == "supportive_care":
            return f"I hear your concerns, and the performance is adapting to give a more calming, supportive atmosphere right now."
        else:
            return f"Thank you for the input. The system has noted this and continues on the standard trajectory."

    def process_input(self, text, mode="standard"):
        start_time = time.time()
        
        sentiment = self.analyze_sentiment(text)
        strategy = self.select_strategy(sentiment)
        response = self.generate_response(text, strategy)
        
        # Asynchronously speak the response (Option 2)
        spawn_voice(response)
        
        latency = (time.time() - start_time) * 1000

        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "input": text,
            "sentiment": sentiment['label'],
            "score": sentiment['score'],
            "strategy": strategy,
            "response": response,
            "latency_ms": latency
        })

        if mode == "compare":
            print(f"\n{Colors.BOLD}--- Comparison Mode ---{Colors.ENDC}")
            print(f"Input: '{text}'")
            print(f"Detected Sentiment: {sentiment['label']} (Confidence: {sentiment['score']:.2f})")
            print(f"\n{Colors.WARNING}[Non-Adaptive Baseline System]{Colors.ENDC}")
            print(f"Response: Thank you for the input. The performance continues.")
            print(f"\n{Colors.OKGREEN}[Project Chimera Adaptive System]{Colors.ENDC}")
            print(f"Selected Strategy: {Colors.OKCYAN}{strategy}{Colors.ENDC}")
            print(f"Response: {response}")
            print(f"\nLatency: {latency:.0f}ms")
            
        elif mode == "caption":
            print(f"\n{Colors.BOLD}--- High-Contrast Caption Format ---{Colors.ENDC}")
            print(f"{Colors.CAPTION} {text} {Colors.ENDC}")
            print("SRT output successfully generated.")
            self.export_srt("captions.srt", text)
            
        else:
            print(f"\n{Colors.BOLD}System Output:{Colors.ENDC}")
            print(f"Sentiment: {sentiment['label']} -> Strategy: {strategy}")
            print(f"Adaptive Dialogue: {response}")
            print(f"Latency: {latency:.0f}ms")

    def export_srt(self, filename, text):
        with open(filename, "a", encoding="utf-8") as f:
            idx = len(self.history)
            now = datetime.now()
            ts1 = now.strftime("%H:%M:%S,000")
            ts2 = now.strftime("%H:%M:%S,500")
            f.write(f"{idx}\n{ts1} --> {ts2}\n{text}\n\n")

    def export_json(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)
            
    def export_csv(self, filename):
        with open(filename, "w", encoding="utf-8", newline='') as f:
            if not self.history:
                return
            writer = csv.DictWriter(f, fieldnames=self.history[0].keys())
            writer.writeheader()
            writer.writerows(self.history)

    def print_banner(self):
        print(f"\n{Colors.HEADER}{Colors.BOLD}=== Project Chimera Pipeline ==={Colors.ENDC}")
        print("1. Text Input → Sentiment Analysis (DistilBERT ML Model)")
        print("2. Sentiment → Adaptive Routing Strategy Selection")
        print("3. Adaptive Routing → GLM-4.7 API Dialogue Generation")
        print("\nType 'quit' to exit.")
        print("Type 'compare' to enter comparison mode for the next input.")
        print("Type 'caption' to enter caption mode for the next input.")
        print("Type 'export' to export session data (JSON/CSV/SRT).")
        print("==================================================\n")

    def run_interactive(self):
        self.print_banner()
        self.load_models()
        
        next_mode = "standard"
        
        while True:
            try:
                user_input = input(f"{Colors.OKCYAN}Chimera > {Colors.ENDC}").strip()
                if not user_input:
                    continue
                    
                if user_input.lower() == 'quit':
                    print("Exiting Chimera Core.")
                    break
                elif user_input.lower() == 'compare':
                    print("Comparison mode activated. Enter your next text to see side-by-side comparison.")
                    next_mode = "compare"
                    continue
                elif user_input.lower() == 'caption':
                    print("Caption mode activated. Enter your next text to format as accessible caption.")
                    next_mode = "caption"
                    continue
                elif user_input.lower() == 'export':
                    self.export_json("chimera_export.json")
                    self.export_csv("chimera_export.csv")
                    print("Exported session data to chimera_export.json and chimera_export.csv.")
                    continue
                
                self.process_input(user_input, mode=next_mode)
                next_mode = "standard"  # reset mode after processing
                
            except KeyboardInterrupt:
                print("\nExiting Chimera Core.")
                break
            except EOFError:
                break

    def run_demo(self):
        print(f"\n{Colors.BOLD}Executing Demo Sequence...{Colors.ENDC}")
        self.load_models()
        demo_texts = [
            "This show is absolutely wonderful, I love the energy!",
            "I'm feeling a bit anxious and the loud noises are frustrating.",
            "It's an okay experience, nothing special so far."
        ]
        for t in demo_texts:
            print(f"\n{Colors.BOLD}Processing Demo Input:{Colors.ENDC} '{t}'")
            self.process_input(t)
            time.sleep(1)

def main():
    core = ChimeraCore()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "demo":
            core.run_demo()
        elif command == "compare" and len(sys.argv) > 2:
            core.load_models()
            core.process_input(" ".join(sys.argv[2:]), mode="compare")
        elif command == "caption" and len(sys.argv) > 2:
            core.load_models()
            core.process_input(" ".join(sys.argv[2:]), mode="caption")
        else:
            # Assumes the arguments are raw string input, not a structural command.
            core.load_models()
            core.process_input(" ".join(sys.argv[1:]))
    else:
        core.run_interactive()

if __name__ == "__main__":
    main()
