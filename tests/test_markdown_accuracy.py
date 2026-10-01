#!/usr/bin/env python3
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_FILE = os.path.join(REPO_ROOT, "tests", "test_all_labs_prompts.py")

def load_test_file():
    with open(TEST_FILE, "r") as f:
        return f.read()

def test_markdown_accuracy():
    test_content = load_test_file()
    all_passed = True
    
    for lab_num in range(2, 8):
        guide_path = os.path.join(REPO_ROOT, f"lab{lab_num}", "guide.md")
        if not os.path.exists(guide_path):
            continue
            
        with open(guide_path, "r") as f:
            guide_content = f.read()
            
        guide_prompts = set(re.findall(r'> \*"([^"]+)"\*', guide_content))
        
        # Find p1, p2, p3 in test_content for this lab
        block_match = re.search(f'def run_lab{lab_num}_tests.*?(def run_lab|$)', test_content, re.DOTALL)
        if block_match:
            block = block_match.group(0)
            p_matches = re.findall(r'\bp[123]\s*=\s*"([^"]+)"', block)
            for p in p_matches:
                if p not in guide_prompts:
                    print(f"❌ [Lab {lab_num}] Test suite prompt NOT FOUND in guide.md: {p}")
                    all_passed = False
                
    if all_passed:
        print("✅ Phase 0: Automated Markdown Verification Passed.")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    test_markdown_accuracy()
