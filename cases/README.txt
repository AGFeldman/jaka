*.json are the only files that actually specify the test cases

case*.py are used to generate the json files. For example, 'python case0.py > case0.json'. You can also write straight json if you prefer. agf finds it easier to specify units in python, since you can say 10 * 10** 6 for '10 MB'.

verify.py checks that test cases specified in json meet a certain format. Run 'bash verify.sh' to check all json files in this directory.
