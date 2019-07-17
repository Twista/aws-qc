AWS Quick Connect
===


Install
===
```
# clone repository
mkdir ~/development
cd ~/development
git clone git@github.com:Twista/aws-qc.git

# install requirements
cd aws-qc
virtualenv venv -p python3
. venv/bin/activate.fish
pip install -r requirements.txt

# add alias to your bash config
alias qc "~/development/aws-qc/venv/bin/python ~/development/aws-qc/main.py"
```