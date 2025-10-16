import os, json, yaml
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain

# --- Setup ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
base_path = os.path.join(os.path.dirname(__file__), "prompts")

def load_prompt(name):
    with open(os.path.join(base_path, name)) as f:
        return f.read()

# --- Prompt templates ---
detect_prompt = PromptTemplate(input_variables=["yaml"], template=load_prompt("detect_prompt.txt"))
fix_prompt = PromptTemplate(input_variables=["yaml", "issues"], template=load_prompt("fix_prompt.txt"))
validate_prompt = PromptTemplate(input_variables=["yaml"], template=load_prompt("validate_prompt.txt"))

# --- Chains ---
detect_chain = LLMChain(llm=llm, prompt=detect_prompt, output_key="issues_json")
fix_chain = LLMChain(llm=llm, prompt=fix_prompt, output_key="fixed_yaml")
validate_chain = LLMChain(llm=llm, prompt=validate_prompt, output_key="validation")

# --- Combined pipeline ---
pipeline = SequentialChain(
    chains=[detect_chain, fix_chain, validate_chain],
    input_variables=["yaml"],
    output_variables=["issues_json", "fixed_yaml", "validation"],
    verbose=True,
)

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
    results = []
    for path, content in read_yaml_files("."):
        print(f"\n=== Analyzing {path} ===")
        output = pipeline({"yaml": content})
        try:
            issues = json.loads(output["issues_json"])
        except Exception:
            print("⚠️ Could not parse issues JSON.")
            issues = []

        print(json.dumps(issues, indent=2))
        print("\nSuggested fix:\n", output["fixed_yaml"])
        print("\nValidation result:", output["validation"])
        results.append({"file": path, "issues": issues, "fixed": output["fixed_yaml"], "validation": output["validation"]})

    # Fail pipeline on CRITICAL/HIGH
    if any(i["severity"] in ("CRITICAL", "HIGH") for r in results for i in r["issues"]):
        print("❌ Critical or High issues detected.")
        exit(1)
    print("✅ No blocking issues found.")

if __name__ == "__main__":
    run_pipeline()

