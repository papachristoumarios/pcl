INSTALL_PREFIX=/usr/local
CC=gcc
CCFLAGS=-fPIC -shared -Wall -Werror

compiler: pcl/builtins.c
	$(CC) pcl/builtins.c -o pcl/libbuiltins.so $(CCFLAGS)
	cp pcl/libbuiltins.so $(INSTALL_PREFIX)/lib/libbuiltins.so
	pip install -e .

depend: requirements.txt
	apt-get install -y llvm-8 gcc-4.8
	conda install --channel=numba llvmlite
	pip install -r requirements.txt

create_env:
	conda create --name pcl

test:
	cd tests && pytest -s * 

clean:
	rm -rf pcl/libbuiltins.so
	pip uninstall pcl
