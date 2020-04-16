CC=gcc
CCFLAGS=-fPIC -shared -Wall -Werror

compiler: pcl/builtins.c
	$(CC) pcl/builtins.c -o pcl/libbuiltins.so $(CCFLAGS)
	pip install -e .

depend: requirements.txt
	apt-get install -y llvm-8 gcc-4.8
	conda install --channel=numba llvmlite
	pip install -r requirements.txt

create_env:
	conda create --name pcl

tests:
	pytest tests/*

clean:
	rm -rf pcl/libbuiltins.so
