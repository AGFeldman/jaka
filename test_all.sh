status=0

# flake8 test
echo "Running flake8"
flake8 .
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

# generate.sh test
echo "Running generate.sh"
cd cases
bash generate.sh > /dev/null
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

cd ..

# case0 test
echo "Running case0"
time python run.py cases/case0.json case0_test_output 
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

# case1 test
echo "Running case1"
time python run.py cases/case1.json case1_test_output 
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

# case2 test
echo "Running case2"
time python run.py cases/case2.json case2_test_output
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

exit $status
