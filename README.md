# ProofDoctor

## Installation

`pip install -r requirements.txt` should take care of all dependencies.


## Usage

To repair the toy example in ./test:
```bash
cd test; python ../main.py make
```
Invocation works the same for any Coq project using the appropriate build command.

```bash
conda create -n proof-repair python=3.11
conda activate proof-repair
pip install coq-pearls @ git+https://github.com/tom-p-reichel/prism.git
pip install git+https://github.com/tom-p-reichel/prism.git#egg=coq-pearls
pip install git+https://github.com/tom-p-reichel/goodinference.git#egg=goodinference
pip install git+https://github.com/tom-p-reichel/python-coqtop.git#egg=coqtop
```

In the forked version of prism, replace deprecated np.infty with np.inf. 
