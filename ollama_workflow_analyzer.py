"""
Ollama Workflow Analyzer
Analyzes cleaned workflow files using local Ollama LLM to provide insights and automation suggestions.

Usage:
    python ollama_workflow_analyzer.py clean_workflows/cleaned_<session>.json
    
Requirements:
    - Ollama running locally on http://localhost:11434
    - mistral:latest model installed (run: ollama pull mistral:latest)
"""

import os
import sys
import json
import requests
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral:latest"  # Faster alternative: mistral is smaller and quicker than llama3:8b

SYSTEM_PROMPT = """
You are a workflow summarizer AI.

You are given a structured list of recorded user actions (keyboard presses, clicks, etc.), each with fields such as `action_type`, `description`, `target`, `window`, and optionally `transcripts`.

Your job is to:
1. Analyze the sequence of actions and the active window names.
2. Infer what the user was trying to do (task intent).
3. Detect distinct tasks based on app/window switches, new goals, or different activities.
4. Identify automation opportunities.


### Task Segmentation:
- Treat a **new window name** as a strong signal of a **new task or subtask**.
- A new task also begins when:
  - A new application opens or focus changes (based on `window`).
  - The user starts typing a URL, command, or distinct phrase.
  - The user’s goal clearly changes (e.g., launching Notepad → typing text → closing app).
- Merge related actions within the same window into one coherent task description.
- Avoid listing step numbers (e.g., “steps 2–12”); describe actions naturally instead.


### Reasoning Rules:
- Combine consecutive single-key typing events into meaningful phrases.
  Example: “Typed y, o, u, t, u, b, e” → “Typed ‘youtube.com’”.
- Use the `window` field to identify which app was active.
  Example: `"window": "Run"` → user used Windows Run dialog.
- If transcripts are missing, infer intent from patterns and context.
  Example: Typing “notepad” in the Run window → intent: open Notepad.
- Keep reasoning factual and concise — do not hallucinate or assume unseen actions.


### Automation Rules:
- Suggest automation at a **goal level** (what the user wants to achieve), not low-level inputs.
  Example: “Open Opera and visit YouTube,” not “Type each letter of youtube.com”.
- If similar actions repeat (e.g., opening multiple sites), group them into a single automation flow.


### Output Format:

1. **Summary (by Task):**
   - Describe each task clearly using natural language.
   - Mention which window or application the user was working in.
   - Explain inferred intent briefly.

2. **Transcript Insight:**
   - If transcripts exist, summarize what they reveal about user intent.
   - If not available, say: “Transcript: Not available.”

3. **Automation:**
   - Mention if the workflow can be automated and how.

4. **Steps (to Automate):**
   - Provide short, human-readable steps describing what the automation should do.

### Example Output:

**Summary (by Task):**
- **Task 1:** The user opened the Run dialog and typed “notepad”, then pressed Enter to launch Notepad.
- **Task 2:** In the Notepad window, they typed a short message (“hey how are you how are you today? yo yo”).
- **Task 3:** The user closed Notepad using `Alt+F4`.

**Transcript Insight:** Transcript: Not available.

**Automation:**
Opening Notepad and typing predefined text can be automated using a simple script or macro.

**Steps (to Automate):**
1. Open the Run dialog.
2. Type “notepad” and press Enter.
3. Wait for Notepad to open.
4. Type the desired message automatically.
5. Close the application.
"""

def parse_txt_workflow(content: str):
    """
    Basic parser for .txt workflow logs.
    Extracts metadata, summary, and actions so the model can analyze them.
    """
    workflow = {
        "metadata": {
            "session_id": "unknown",
            "recorded_at": "unknown",
            "total_steps": 0
        },
        "workflow_summary": "",
        "actions": []
    }

    lines = content.splitlines()
    current_section = None

    for line in lines:
        line_stripped = line.strip()

        # Detect headers or sections
        if line_stripped.upper().startswith("SESSION"):
            workflow["metadata"]["session_id"] = line_stripped.split(":", 1)[-1].strip()
        elif line_stripped.upper().startswith("RECORDED"):
            workflow["metadata"]["recorded_at"] = line_stripped.split(":", 1)[-1].strip()
        elif "WORKFLOW SUMMARY" in line_stripped.upper():
            current_section = "summary"
        elif "DETAILED ACTIONS" in line_stripped.upper():
            current_section = "actions"
        elif current_section == "summary":
            workflow["workflow_summary"] += " " + line_stripped
        elif current_section == "actions" and line_stripped:
            # Try to detect "Step 1: something"
            if line_stripped.lower().startswith("step "):
                parts = line_stripped.split(":", 1)
                if len(parts) == 2:
                    step_label, desc = parts
                    try:
                        step_num = int(''.join(filter(str.isdigit, step_label)))
                    except ValueError:
                        step_num = len(workflow["actions"]) + 1
                    workflow["actions"].append({
                        "step": step_num,
                        "description": desc.strip()
                    })
            else:
                # Treat as continuation of previous action description
                if workflow["actions"]:
                    workflow["actions"][-1]["description"] += " " + line_stripped
                else:
                    workflow["actions"].append({
                        "step": 1,
                        "description": line_stripped
                    })

    workflow["metadata"]["total_steps"] = len(workflow["actions"])
    workflow["workflow_summary"] = workflow["workflow_summary"].strip()
    return workflow


def load_workflow(filepath):
    """Load cleaned workflow JSON or TXT file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Check if it's a JSON or TXT file
            if filepath.endswith('.json'):
                return json.load(f)
            elif filepath.endswith('.txt'):
                # Parse the TXT format
                content = f.read()
                return parse_txt_workflow(content)
            else:
                print(f"❌ Error: Unsupported file format. Use .json or .txt files.")
                sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON file: {e}")
        sys.exit(1)

def format_workflow_for_llm(workflow):
    """Format workflow data into a clear prompt for the LLM."""
    metadata = workflow.get("metadata", {})
    summary = workflow.get("workflow_summary", "")
    actions = workflow.get("actions", [])
    
    prompt = f"""Analyze this user workflow:

SESSION ID: {metadata.get('session_id', 'unknown')}
RECORDED: {metadata.get('recorded_at', 'unknown')}
TOTAL STEPS: {metadata.get('total_steps', 0)}

WORKFLOW SUMMARY:
{summary}

DETAILED ACTIONS:
"""
    
    for action in actions:
        step_num = action.get('step', '')
        desc = action.get('description', '')
        action_type = action.get('action_type', '')
        target = action.get('target', '')
        transcripts = action.get('transcripts', [])
        
        prompt += f"\nStep {step_num}: {desc}"
        if action_type:
            prompt += f"\n  Action Type: {action_type}"
        if target:
            prompt += f"\n  Target: {target}"
        if transcripts:
            # Join all transcripts for this step
            transcript_text = " | ".join(transcripts)
            prompt += f"\n  Transcript: {transcript_text}"
    
    prompt += """

Please provide your analysis following the format specified in the system prompt.
"""
    
    return prompt

def query_ollama(prompt, system_prompt=SYSTEM_PROMPT, stream=True, model_name=None):
    """
    Send prompt to Ollama API and get response.
    
    Args:
        prompt: The user prompt to send
        system_prompt: System instructions for the model
        stream: Whether to stream the response (default: True)
        model_name: Optional model name to use
    """
    # Use provided model or default
    selected_model = model_name if model_name else MODEL_NAME
    
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": stream,
        "options": {
            "temperature": 0.4,
            "top_p": 0.85,
            "top_k": 30,
            "repeat_penalty": 1.1,
        }

    }
    
    try:
        print(f"🤖 Querying Ollama ({selected_model})...\n")
        print("=" * 70)
        
        response = requests.post(OLLAMA_URL, json=payload, stream=stream, timeout=250)
        response.raise_for_status()
        
        full_response = ""
        
        if stream:
            # Stream response in real-time
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        print(token, end="", flush=True)
                        full_response += token
                        
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
        else:
            # Get complete response
            data = response.json()
            full_response = data.get("response", "")
            print(full_response)
        
        print("\n" + "=" * 70)
        return full_response
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Ollama. Make sure it's running:")
        print("   Start Ollama: ollama serve")
        print(f"   Or check if it's accessible at: {OLLAMA_URL}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out. The model might be taking too long to respond.")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Error communicating with Ollama: {e}")
        sys.exit(1)

def save_analysis(workflow_file, analysis_text):
    """Save the LLM analysis to a file."""
    base_name = os.path.basename(workflow_file).replace(".json", "")
    output_dir = "clean_workflows/analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"analysis_{base_name}.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"WORKFLOW ANALYSIS\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: {workflow_file}\n")
        f.write(f"Model: {MODEL_NAME}\n")
        f.write("=" * 70 + "\n\n")
        f.write(analysis_text)
    
    print(f"\n💾 Analysis saved to: {output_file}")
    return output_file

def check_ollama_status(model_name=None):
    """Check if Ollama is running and the model is available."""
    # Use provided model or default
    check_model = model_name if model_name else MODEL_NAME
    
    try:
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        
        if check_model not in model_names:
            print(f"⚠️  Warning: Model '{check_model}' not found locally.")
            print(f"   Available models: {', '.join(model_names) if model_names else 'None'}")
            print(f"\n   To install the model, run:")
            print(f"   ollama pull {check_model}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Ollama is not running.")
        print("   Start it with: ollama serve")
        return False
    except Exception as e:
        print(f"⚠️  Warning: Could not verify Ollama status: {e}")
        return True  # Continue anyway

def analyze_workflow_with_ollama(workflow_file, model_name=None):
    """
    Analyze a cleaned workflow file using Ollama LLM.
    Can be called from other modules.
    
    Args:
        workflow_file: Path to the cleaned workflow JSON or TXT file
        model_name: Optional model name to use (default: MODEL_NAME from config)
        
    Returns:
        bool: True if analysis was successful, False otherwise
    """
    # Use provided model or default
    selected_model = model_name if model_name else MODEL_NAME
    
    # Check file format
    if not (workflow_file.endswith('.json') or workflow_file.endswith('.txt')):
        print(f"[Ollama Analyzer] ❌ Error: File must be .json or .txt format")
        return False
    
    if not os.path.exists(workflow_file):
        print(f"[Ollama Analyzer] ❌ Error: File not found: {workflow_file}")
        return False
    
    # Check Ollama status with the selected model
    print("[Ollama Analyzer] 🔍 Checking Ollama status...")
    if not check_ollama_status(selected_model):
        print("[Ollama Analyzer] ⚠️ Ollama not available, skipping LLM analysis")
        return False
    
    print(f"[Ollama Analyzer] ✓ Ollama is ready (using model: {selected_model})\n")
    
    try:
        # Load workflow
        print(f"[Ollama Analyzer] 📂 Loading workflow: {workflow_file}")
        workflow = load_workflow(workflow_file)
        
        # Format prompt
        prompt = format_workflow_for_llm(workflow)
        
        # Get analysis from Ollama with selected model
        analysis = query_ollama(prompt, model_name=selected_model)
        
        # Save analysis
        if analysis:
            save_analysis(workflow_file, analysis)
            print("\n[Ollama Analyzer] ✨ Analysis complete!")
            return True
        else:
            print("\n[Ollama Analyzer] ⚠️ No analysis generated")
            return False
            
    except Exception as e:
        print(f"[Ollama Analyzer] ❌ Error during analysis: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python ollama_workflow_analyzer.py clean_workflows/cleaned_<session>.[json|txt]")
        print("\nExamples:")
        print("  python ollama_workflow_analyzer.py clean_workflows/cleaned_20251027_082338.json")
        print("  python ollama_workflow_analyzer.py clean_workflows/cleaned_20251027_082338.txt")
        sys.exit(1)
    
    workflow_file = sys.argv[1]
    success = analyze_workflow_with_ollama(workflow_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()