# Generates case*.json files from case*.py files
# Runs verify.py on the case*.json files
# Does not generate DOT files. This is only intended to be useful for
# continuous integration.v

for c in case*.py
do
    json_filename=$(echo "$c" | sed s/\.py/\.json/)
    dot_filename=$(echo "$c" | sed s/\.py/\.pdf/)
    echo "Generating $json_filename"
    python $c > $json_filename
done

for json_filename in case*.json
do
    echo "Checking $json_filename for obvious errors"
    python ../check_json.py < $json_filename
done
