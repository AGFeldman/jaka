echo "Running flake8"
flake8 .

echo "Running generate.sh"
cd cases
bash generate.sh > /dev/null

cd ..
echo "Running case0"
time python run.py cases/case0.json case0_test_output 
echo "Running case1"
time python run.py cases/case1.json case1_test_output 
echo "Running case2"
time python run.py cases/case2.json case2_test_output
