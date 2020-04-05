compiler:
	pip install .

depend: requirements.txt
	apt-get install -y llvm-8 gcc-4.8
	conda install --channel=numba llvmlite
	pip install -r requirements.txt

create_env:
	conda create --name pcl

tests:
	pytest tests/*
