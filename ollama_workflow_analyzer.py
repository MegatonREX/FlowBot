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
MODEL_NAME = "llama3:7b"

SYSTEM_PROMPT = """
You are a workflow summarizer AI.

You are given a structured list of recorded user actions, each with details such as `action_type`, `description`, and `target`.
Your task is to analyze these actions and produce a complete yet concise explanation of what actually happened — including what the user likely did in context — and identify which parts could be automated.

Output format:
1. Summary: Write a clear, human-readable explanation of what the user did, describing the major actions in sequence. Include inferred meaning from context (e.g., "User pressed Cmd+R to open the Run dialog, typed 'opera', pressed Enter to open the Opera browser, then navigated to Gmail.").
2. Steps: List the important actions in short, factual order like a command trace (e.g., "Cmd+R → Typed 'opera' → Enter → Typed 'gmail' → Enter → Clicked inside browser").
3. Automation: Determine if any steps are repetitive or pattern-based. If yes, explain which actions can be automated (e.g., "Opening the Run dialog and typing a command can be automated using a script."). Otherwise, say "No automation needed."

Rules:
- Use both `action_type` and `target` fields to understand what was done.
- Infer context only when it is strongly implied (e.g., Cmd+R likely means Run dialog on Windows).
- Merge similar or repeated patterns into one meaningful sequence.
- Keep the response factual, structured, and formatted exactly with the three labeled sections:
  Summary:
  Steps:
  Automation:
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
        
        prompt += f"\nStep {step_num}: {desc}"
    
    prompt += """

Please provide your analysis in exactly this format:
- Summary: [one sentence describing what the user did]
- Automation: [either "Can be automated." or "No automation needed."]
"""
    
    return prompt

def query_ollama(prompt, system_prompt=SYSTEM_PROMPT, stream=True):
    """
    Send prompt to Ollama API and get response.
    
    Args:
        prompt: The user prompt to send
        system_prompt: System instructions for the model
        stream: Whether to stream the response (default: True)
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": stream,
        "options": {
            "temperature": 0.3,
            "top_p": 0.85,
            "top_k": 30,
            "repeat_penalty": 1.1,
        }

    }
    
    try:
        print(f"🤖 Querying Ollama ({MODEL_NAME})...\n")
        print("=" * 70)
        
        response = requests.post(OLLAMA_URL, json=payload, stream=stream, timeout=120)
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

def check_ollama_status():
    """Check if Ollama is running and the model is available."""
    try:
        # Check if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        
        if MODEL_NAME not in model_names:
            print(f"⚠️  Warning: Model '{MODEL_NAME}' not found locally.")
            print(f"   Available models: {', '.join(model_names) if model_names else 'None'}")
            print(f"\n   To install the model, run:")
            print(f"   ollama pull {MODEL_NAME}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Ollama is not running.")
        print("   Start it with: ollama serve")
        return False
    except Exception as e:
        print(f"⚠️  Warning: Could not verify Ollama status: {e}")
        return True  # Continue anyway

def main():
    if len(sys.argv) < 2:
        print("Usage: python ollama_workflow_analyzer.py clean_workflows/cleaned_<session>.[json|txt]")
        print("\nExamples:")
        print("  python ollama_workflow_analyzer.py clean_workflows/cleaned_20251027_082338.json")
        print("  python ollama_workflow_analyzer.py clean_workflows/cleaned_20251027_082338.txt")
        sys.exit(1)
    
    workflow_file = sys.argv[1]
    
    # Check file format
    if not (workflow_file.endswith('.json') or workflow_file.endswith('.txt')):
        print("❌ Error: File must be .json or .txt format")
        sys.exit(1)
    
    # Check Ollama status
    print("🔍 Checking Ollama status...")
    if not check_ollama_status():
        sys.exit(1)
    
    print("✓ Ollama is ready\n")
    
    # Load workflow
    print(f"📂 Loading workflow: {workflow_file}")
    workflow = load_workflow(workflow_file)
    
    # Format prompt
    prompt = format_workflow_for_llm(workflow)
    
    # Get analysis from Ollama
    analysis = query_ollama(prompt)
    
    # Save analysis
    if analysis:
        save_analysis(workflow_file, analysis)
        print("\n✨ Analysis complete!")
    else:
        print("\n⚠️  No analysis generated")

if __name__ == "__main__":
    main()