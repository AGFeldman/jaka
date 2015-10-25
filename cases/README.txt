case*.json are the only files that actually specify the test cases

Run `generate.sh` to generate case*.json files from all the case*.py files in this directory.

case*.py are used to generate the json files. For example, `python case0.py > case0.json`. You can also write straight json if you prefer. agf finds it easier to specify units in python, since you can say 10 * 10** 6 for '10 MB'.

../check_json.py checks that test cases specified in json meet a certain format. This is automatically called on all case*.json files as part of `generate.sh`.  Run `python ../check_json.py < caseX.json` to check a particular json file.

IDs of network entities are not strictly related to their type. There is a separate 'type' field.
