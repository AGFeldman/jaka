# Generates case*.json files from case*.py files
# Runs verify.py on the case*.json files

for c in case*.py
do
    json_filename=$(echo "$c" | sed s/\.py/\.json/)
    dot_filename=$(echo "$c" | sed s/\.py/\.pdf/)
    echo "Generating $json_filename"
    python $c > $json_filename
    echo "Generating $dot_filename"
    python ../generate_dot.py $json_filename | dot -T pdf > $dot_filename
done

for json_filename in case*.json
do
    echo "Checking $json_filename for obvious errors"
    python ../check_json.py < $json_filename
done
