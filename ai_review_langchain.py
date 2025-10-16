import os, json, yaml
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

# --- Setup ---
base_path = os.path.join(os.path.dirname(__file__), "prompts")

def load_prompt(name):
    with open(os.path.join(base_path, name)) as f:
        return f.read()

def get_pipeline():
    """Initialize the pipeline with LLM - called when needed to avoid API key issues at import"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # --- Prompt templates ---
    detect_prompt = PromptTemplate(input_variables=["yaml"], template=load_prompt("detect_prompt.txt"))
    fix_prompt = PromptTemplate(input_variables=["yaml", "issues"], template=load_prompt("fix_prompt.txt"))
    validate_prompt = PromptTemplate(input_variables=["yaml"], template=load_prompt("validate_prompt.txt"))

    # --- Modern LangChain pipeline using RunnableSequence ---
    def detect_issues(inputs):
        """Detect issues in YAML"""
        response = detect_prompt | llm
        result = response.invoke(inputs)
        # Extract content from AIMessage if needed
        content = result.content if hasattr(result, 'content') else str(result)
        return {"issues_json": content}

    def fix_yaml(inputs):
        """Fix YAML based on detected issues"""
        response = fix_prompt | llm
        result = response.invoke(inputs)
        # Extract content from AIMessage if needed
        content = result.content if hasattr(result, 'content') else str(result)
        return {"fixed_yaml": content}

    def validate_yaml(inputs):
        """Validate the YAML"""
        response = validate_prompt | llm
        result = response.invoke(inputs)
        # Extract content from AIMessage if needed
        content = result.content if hasattr(result, 'content') else str(result)
        return {"validation": content}

    # --- Combined pipeline using modern syntax ---
    def run_analysis(inputs):
        """Run the complete analysis pipeline"""
        # Step 1: Detect issues
        issues_result = detect_issues(inputs)
        issues_json = issues_result["issues_json"]
        
        # Step 2: Fix YAML (pass both original yaml and issues)
        fix_inputs = {"yaml": inputs["yaml"], "issues": issues_json}
        fix_result = fix_yaml(fix_inputs)
        fixed_yaml = fix_result["fixed_yaml"]
        
        # Step 3: Validate the fixed YAML
        validate_inputs = {"yaml": fixed_yaml}
        validation_result = validate_yaml(validate_inputs)
        validation = validation_result["validation"]
        
        return {
            "issues_json": issues_json,
            "fixed_yaml": fixed_yaml,
            "validation": validation
        }
    
    return run_analysis

# --- Helpers ---
def read_yaml_files(path="."):
    yamls = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith((".yaml", ".yml")):
                with open(os.path.join(root, f)) as fp:
                    yamls.append((os.path.join(root, f), fp.read()))
    return yamls

def run_pipeline():
    pipeline = get_pipeline()  # Initialize pipeline when needed
    results = []
    for path, content in read_yaml_files("."):
        print(f"\n=== Analyzing {path} ===")
        try:
            output = pipeline({"yaml": content})
            
            # Debug: Print what the AI actually returned
            print(f"DEBUG - Raw issues_json: {repr(output['issues_json'])}")
            
            try:
                # Try to parse the JSON directly
                issues = json.loads(output["issues_json"])
            except json.JSONDecodeError as e:
                print(f"⚠️ Could not parse issues JSON: {e}")
                print(f"Raw response: {output['issues_json']}")
                
                # Try to extract JSON from the response if it's embedded in other text
                import re
                json_match = re.search(r'\[.*?\]', output["issues_json"], re.DOTALL)
                if json_match:
                    try:
                        issues = json.loads(json_match.group(0))
                        print("✅ Successfully extracted JSON from response")
                    except:
                        issues = []
                else:
                    issues = []
            except Exception as e:
                print(f"⚠️ Unexpected error parsing JSON: {e}")
                issues = []

            print("Issues found:")
            print(json.dumps(issues, indent=2))
            print("\nSuggested fix:")
            # Clean up the output by removing 'content=' prefix if present
            fixed_yaml = output["fixed_yaml"]
            if fixed_yaml.startswith("content='") and fixed_yaml.endswith("'"):
                fixed_yaml = fixed_yaml[9:-1]  # Remove 'content=' and trailing quote
            print(fixed_yaml)
            
            # Clean up validation result
            validation = output["validation"]
            if validation.startswith("content='") and validation.endswith("'"):
                validation = validation[9:-1]  # Remove 'content=' and trailing quote
            print(f"\nValidation result: {validation}")
            results.append({"file": path, "issues": issues, "fixed": output["fixed_yaml"], "validation": output["validation"]})
        except Exception as e:
            print(f"❌ Error processing {path}: {e}")
            continue

    # Fail pipeline on CRITICAL/HIGH
    if any(i["severity"] in ("CRITICAL", "HIGH") for r in results for i in r["issues"]):
        print("❌ Critical or High issues detected.")
        exit(1)
    print("✅ No blocking issues found.")

if __name__ == "__main__":
    run_pipeline()

