import os
import json
import shutil
import subprocess
from pathlib import Path
import re
import argparse
from prism.util.opam import OpamSwitch

# https://huggingface.co/datasets/a-gardner1/PRISM/tree/main/Coq-Flow-Equivalence
# Iterates through the dataset to find commits with broken proofs. Checks out a copy of Coq-Flow-Equivalence on the broken proof commit. 
# Clone the Coq-Flow-Equivalence repository. https://github.com/GaloisInc/Coq-Flow-Equivalence
# Ex - python prepare_broken_proofs_coq_flow_equivalence.py --example-limit 5
# To repair - then cd to the directory of the broken version of the repo that was created, and run the python main.py make.

class PRISMProject:
    def __init__(self, project_name, work_dir, dataset_path):
        self.project_name = project_name
        self.work_dir = Path(work_dir)
        self.dataset_path = Path(dataset_path) / project_name
        self.original_repo = self.work_dir / project_name
        self.opam_switch = OpamSwitch()

    def setup_test_directory(self, example_name):
        test_dir_name = f"test_{Path(example_name).stem}"
        test_dir = self.work_dir / test_dir_name

        if test_dir.exists():
            shutil.rmtree(test_dir)

        print(f"Copying repository to {test_dir}")
        shutil.copytree(self.original_repo, test_dir, dirs_exist_ok=True)

        return test_dir
    
    def replace_omega_with_lia(self, repo_path):
        print("Replacing Omega with Lia in Coq files...")

        for file_path in repo_path.glob("**/*.v"):
            print(f"Checking {file_path.name}...")
            with open(file_path, 'r') as f:
                content = f.read()

            old_content = content
            content = re.sub(r'Require Import Omega\.', 'Require Import Lia.', content)
            content = re.sub(r'\bomega\b', 'lia', content)

            if content != old_content:
                print(f"Made replacements in {file_path.name}")
                with open(file_path, 'w') as f:
                    f.write(content)

    def fix_monad_file(self, repo_path):
        """Fix issues in Monad.v."""
        monad_file = repo_path / "Monad.v"
        if monad_file.exists():
            print(f"Processing {monad_file}...")

            # Read the content of Monad.v
            with open(monad_file, 'r') as f:
                content = f.read()
            print("Original content:\n", content)

            # Add scope declaration if missing
            if "Declare Scope monad_scope" not in content:
                content = "Declare Scope monad_scope.\n" + content
                print("Added 'Declare Scope monad_scope'.")

            # Replace all trailing implicit arguments in square brackets with curly braces
            updated_content = re.sub(r'\[(\w+)\]', r'{\1}', content)

            # Check if changes were made
            if updated_content != content:
                print("Updated content:\n", updated_content)

                # Write the changes back to the file
                with open(monad_file, 'w') as f:
                    f.write(updated_content)
                print(f"Successfully updated {monad_file}.")
            else:
                print(f"No changes made to {monad_file}.")
        else:
            print(f"{monad_file} does not exist!")

    def process_example(self, json_file):
        with open(json_file) as f:
            example = json.load(f)

        # Create test directory and check out the initial commit
        test_dir = self.setup_test_directory(json_file.name)
        initial_commit = example["error"]["initial_state"]["project_state"]

        if initial_commit:
            print(f"Checking out commit {initial_commit}")
            subprocess.run(["git", "reset", "--hard"], cwd=test_dir)
            subprocess.run(["git", "clean", "-fdx"], cwd=test_dir)
            subprocess.run(["git", "checkout", initial_commit], cwd=test_dir)
        
        print("Running preprocessing steps on Coq files...")
        self.replace_omega_with_lia(test_dir)
        self.fix_monad_file(test_dir)

        return True

def main():
    parser = argparse.ArgumentParser(description='Process PRISM dataset examples for Coq-Flow-Equivalence')
    parser.add_argument('--work-dir', type=Path, default='/path/to/work/dir',
                        help='Working directory containing the repositories')
    parser.add_argument('--dataset-path', type=Path, default='/path/to/prism/dataset',
                        help='Path to the PRISM dataset')
    parser.add_argument('--example-limit', type=int, default=1,
                        help='Number of examples to process (default: 1, use 0 for all)')

    args = parser.parse_args()
    project = PRISMProject("Coq-Flow-Equivalence", args.work_dir, args.dataset_path)

    if not project.original_repo.exists():
        print(f"Original repository not found at {project.original_repo}")
        return

    if not project.dataset_path.exists():
        print(f"Dataset not found at {project.dataset_path}")
        return

    json_files = list(project.dataset_path.glob("*.json"))
    print(f"Found {len(json_files)} JSON files in {project.dataset_path}")

    if args.example_limit > 0:
        json_files = json_files[:args.example_limit]

    for json_file in json_files:
        project.process_example(json_file)

        if len(json_files) > 1:
            input("\nPress Enter to continue to next example...")

if __name__ == "__main__":
    main()