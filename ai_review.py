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
            # Try to extract JSON from the response if it's embedded in other text
            import re
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                all_findings.extend(parsed)
            else:
                parsed = json.loads(result)
                all_findings.extend(parsed)
        except json.JSONDecodeError as e:
            print(f"⚠️ Could not parse structured response: {e}")
            print(f"Raw response: {result}")
        except Exception as e:
            print(f"⚠️ Unexpected error parsing response: {e}")
            print(f"Raw response: {result}")

    criticals = [f for f in all_findings if f["severity"] in ("CRITICAL", "HIGH")]
    if criticals:
        print("❌ Found critical issues!")
        print(json.dumps(criticals, indent=2))
        exit(1)
    else:
        print("✅ No major issues found.")

if __name__ == "__main__":
    main()

