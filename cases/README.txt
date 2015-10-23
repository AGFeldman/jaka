case*.json are the only files that actually specify the test cases

Run `generate.sh` to generate case*.json files from all the case*.py files in this directory.

Everything about this format should be intuitive, except maybe the following point: The type of a network entity is specified by the first letter of its id. 'R' means router. 'L' means link, 'F' means flow. BUT, hosts can be denoted by 'H', or by 'S', or by 'T'. This corresponds to the test case 2 description: http://courses.cms.caltech.edu/cs143/Project/NetworkSimTestCases-2015.pdf. This aspect of case 2 description is a bit confusing; agf asked Ritvik about it.

case*.py are used to generate the json files. For example, `python case0.py > case0.json`. You can also write straight json if you prefer. agf finds it easier to specify units in python, since you can say 10 * 10** 6 for '10 MB'.

verify.py checks that test cases specified in json meet a certain format. This is automatically called on all case*.json files as part of `generate.sh`.  Run `python verify.py < caseX.json` to check a particular json file.
