
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <thread>
#include <string> 
#include <unistd.h>   
#include <iostream>
#include <fstream>
#include <vector>
#include <string>

using namespace std;

//structture that will keep track of the thread data, TA: colin inspired 
struct thread_data{
    int id;
    int start;
    int end;
};
//These are our global variable that we will store the results in
int array_input[10000];
int counter_composite = 0;

//lets create a mutex in order to synchronize the counter for composite numbers 
pthread_mutex_t lock;


//This takes the inputs:
//determines which numbers and composite or not 
bool isComposite(int n)
{
	// Corner cases
	if (n <= 1) return false;
	if (n <= 3) return false;

	// This is checked so that we can skip
	// middle five numbers in below loop
	if (n%2 == 0 || n%3 == 0) return true;

	for (int i=5; i*i<=n; i=i+6)
		if (n%i == 0 || n%(i+2) == 0)
		return true;

	return false;
}

//This is our thread function that will calculate the composite numbers
void * thread_function(void * a){
    struct thread_data * data = (struct thread_data *) a;
    int mystart = data->start;
    int myend = data->end;
    //int myid = data->id;


    //this loop will run through out the input given by the user and will increase 
    //the counter of the composite numbers  
    for(int i = mystart; i<myend; i++){

    
        if(isComposite(array_input[i]) == true){
             //lets use the mutex in oder to update the counter
            pthread_mutex_lock(&lock);    
            counter_composite ++;
            pthread_mutex_unlock(&lock);
        }
    

    }
    pthread_exit(NULL);
}



// Driver Program to test above function
int main(int argc, char* argv[])

{
    // lets take input some input from the user. if we dont have the correct input we exit and ask to run again.
    if(argc < 2){
        printf("You not enter the correct ammount of argument vectors, try again, run program again");
        exit(1);
    }

    //lets now take the input from the comand line and store it in variables
    int argc1 = atoi(argv[1]);
    int argc2 = atoi(argv[2]);

    //lets now use the comand line input and store it into variables we will be using 
    int nthreads = argc1;
    int threadresults[nthreads];

    //lets now check if the mutex fails.
    if(pthread_mutex_init(&lock,NULL) != 0){
        printf("\n mutex initiation fail\n");
        return 1;

    }


    //lets now create the random integer array to be computed and the seed will be taken from the comand line
    srand(argc2);
    for(int i = 0; i<10000; i++){
        array_input[i] = rand() % 50000;

    }

    //this will destribute the work for each thread as equally as possible, TA collin Week 8
    //it will first dived by the number of threads and then take the remainder
    int clunksize = (sizeof(array_input)/sizeof(int)) / nthreads; // 10/4 = 2
    int clunkover = (sizeof(array_input)/sizeof(int)) % nthreads; //10 % 4 = 2

    
    //the following data struct will give each thread a set of numbers to execute accorind to the distribution 
    //above of the number of thread provided

    //starting at the first index to the array and adding the correspoinding set
    //of numbers with the computation above 
    //heavily spired by: TA collin week8
    int prevend = 0;

    struct thread_data data[nthreads];

    for(int i = 0; i<nthreads; i++){
        data[i].start = prevend;
        if(i < clunkover){
            data[i].end = data[i].start + clunksize + 1;
        }
        else{
            data[i].end = data[i].start + clunksize;
        }
        prevend = data[i].end;
        data[i].id = i;
        printf("Thread %d will have %d to %d\n", i, data[i].start, data[i].end);
    }
    
    //each thread in the thread pool will be created, given an id, and a set of numbers to check in the thread function.
    //once the thread has done executing we will join the thread and return the result
    pthread_t pool[nthreads];

    for(int i = 0; i<nthreads; i++){
        pthread_create(&pool[i], NULL, thread_function, (void *) &data[i]);
    }

    //we will join alll in order to safely exit 
    for(int i = 0; i<nthreads; i++){
        pthread_join(pool[i], NULL);
    }

    
    //here we destroy the mutex and print out our result
    pthread_mutex_destroy(&lock);
    printf("Number of composite values is %d\n",counter_composite);
    

	return 0;
}
