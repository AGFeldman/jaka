status=0

# flake8 test
echo "Running flake8"
flake8 .
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

# generate.sh test
echo "Running generate_without_dot.sh"
cd cases
bash generate_without_dot.sh > /dev/null
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

cd ..

# case0 RENO test
echo "Running case0 RENO"
time python run.py cases/case0_RENO.json case0_RENO_test_output 
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

# case0 FAST test
echo "Running case0 FAST"
time python run.py cases/case0_FAST.json case0_FAST_test_output 
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

# case1 RENO test
echo "Running case1 RENO"
time python run.py cases/case1_RENO.json case1_RENO_test_output 
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

# case1 FAST test
echo "Running case1 FAST"
time python run.py cases/case1_FAST.json case1_FAST_test_output 
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

# case2 RENO test
echo "Running case2 RENO"
time python run.py cases/case2_RENO.json case2_RENO_test_output
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

# case2 FAST test
echo "Running case2 FAST"
time python run.py cases/case2_FAST.json case2_FAST_test_output
last_status=$?
if [ "$status" == "0" ] && [ "$last_status" != "0" ]; then
    status=$last_status
fi

exit $status
