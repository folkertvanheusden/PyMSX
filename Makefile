CXXFLAGS=-Ofast -ggdb3

all: gencompare

gencompare: gencompare.o
	$(CXX) -o gencompare gencompare.o -lz80ex -ggdb3

clean:
	rm -f gencompare gencompare.o
