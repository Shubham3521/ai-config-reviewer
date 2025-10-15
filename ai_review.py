import os, yaml, json, openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def read_yaml_files(path="."):
    yamls = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.endswith((".yaml", ".yml")):
                with open(os.path.join(root, f)) as fp:
                    yamls.append(fp.read())
    return yamls

def review_with_ai(content):
    prompt = open("prompts/k8s_review_prompt.txt").read() + "\n\nYAML:\n" + content
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()

def main():
    yamls = read_yaml_files("examples")
    all_findings = []
    for y in yamls:
        result = review_with_ai(y)
        print(f"Review result:\n{result}\n")
        try:
            parsed = json.loads(result)
            all_findings.extend(parsed)
        except Exception:
            print("⚠️ Could not parse structured response")

    criticals = [f for f in all_findings if f["severity"] in ("CRITICAL", "HIGH")]
    if criticals:
        print("❌ Found critical issues!")
        print(json.dumps(criticals, indent=2))
        exit(1)
    else:
        print("✅ No major issues found.")

if __name__ == "__main__":
    main()

