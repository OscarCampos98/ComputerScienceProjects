
/*
This boilerplate is provided by a combination of code from all the TAs and the textbook
 Alex! (alejandro.garcia@ucalgary.ca)
*/

#include <stdio.h>   
#include <pthread.h>  
#include <string> 
#include <unistd.h>   
#include <pthread.h>
#include <sys/types.h>
#include <semaphore.h>
#include <chrono>

using namespace std;
/*
//This is a monitor representing the waiter for our A3 Part 1
*/
struct WaiterMonitor
{
    //How many chopsticks are available - this should be user input between 5 and 10 (inclusive)
    int chopsticks_available;
    double total_time = 0;
	
    //Mutex-semaphore used to restrict threads entering a method in this monitor
    //Keep in mind many threads may be inside a method in this monitor, but at most ONE should be executing (the rest should be waiting)
    sem_t mutex_sem;
	
    //Mutex-semaphore and counter used to keep track of how many threads are waiting inside a method in this monitor (besides those waiting for a condition)
    sem_t next_sem;
    int next_count;

    //Semaphore and counter to keep track of threads waiting for the 'at least one chopstick available' condition
        //These should be the philosopher threads waiting on the right chopstick
    sem_t condition_can_get_1_sem;
    int condition_can_get_1_count;

    //Semaphore and counter to keep track of threads waiting for the 'at least two chopsticks available' condition
        //These should be the philosopher threads waiting on the left chopstick
    sem_t condition_can_get_2_sem;
    int condition_can_get_2_count;

    void init()
    {
        //Ive hard-coded the number of chopsticks (You may not do this!)
        //chopsticks_available = 2;
        //Mutex to gain access to (any) method in this monitor is initialized to 1
        sem_init(&mutex_sem, 0, 1);
        
        //'Next' semaphore - the semaphore for threads waiting inside a method of this monitor - is initialized to 0 (meaning no threads are initially in a method, as is logical)
        sem_init(&next_sem, 0, 0);
        next_count = 0;

        //Condition semaphores are intialized to 0 (meaning no threads are initially waiting on these conditions, as is logical)
        sem_init(&condition_can_get_1_sem, 0, 0);
        condition_can_get_1_count = 0;
        sem_init(&condition_can_get_2_sem, 0, 0);
        condition_can_get_2_count = 0;
    }
    
    //this function will destroy the conditional variables and the mutex
    void destroy()
    {
        sem_destroy(&mutex_sem);
        sem_destroy(&condition_can_get_1_sem);
        sem_destroy(&condition_can_get_2_sem);
    }

    //This is the manual implementation of pthread_cond_wait() using semaphores
    void condition_wait(sem_t &condition_sem, int &condition_count)
    {
		//condition count is the number of threads waiting on the condition, increment it since the thread calling this method is about to wait
        condition_count++;
		//If there is a waiting thread INSIDE a method in this monitor, they get priority, so post to that semaphore
        if (next_count > 0)
            sem_post(&next_sem);
		//Otherwise, post to the general entry semaphore (the mutex, that is)
        else
            sem_post(&mutex_sem);
		//Wait for this condition to be posted to (Note that as soon as someone posts to this condition, they will halt as this thread has priority!)
        sem_wait(&condition_sem);
		//If I reach here, I have finished waiting :)
        condition_count--;
    }

    //This is the manual implementation of pthread_cond_signal() using semaphores
    void condition_post(sem_t &condition_sem, int &condition_count)
    {
		//If there are any threads waiting on the condition I want to post...
        if (condition_count > 0)
        {
			//...Then they have priority (they were waiting before me), I shall wait in the next_sem gang
            next_count++;
			//Post to the condition_sem gang so they can continue
            sem_post(&condition_sem);
			//Wait for someone to post to next_sem
            sem_wait(&next_sem);
            next_count--;
        }
    }
    void request_left_chopstick()
    {
        //A thread needs mutex access to enter any of this monitors' method!!!
        sem_wait(&mutex_sem);

        //Okay so we got mutex access...but what if there are less than 2 chopsticks available when I am requesting the left chopstick?...
        while(chopsticks_available < 2)
            //...Then wait for the 'at least two chopsticks available' semaphore per the waiter-implementation specifications!
            condition_wait(condition_can_get_2_sem, condition_can_get_2_count);

        //If we're here, then at least two chopsticks are available, use up one of them
        chopsticks_available--;

        if(chopsticks_available >= 1)
        {
            //If at least a chopstick remains, post to the 'at least one chopstick available' condition
            condition_post(condition_can_get_1_sem, condition_can_get_1_count);

             if(chopsticks_available >= 2)
             {
                //If at least two chopsticks remain, post to the 'at least two chopsticks available' condition
                condition_post(condition_can_get_2_sem, condition_can_get_2_count);
             }
        }

        //Threads waiting for next_sem are waiting INSIDE one of this monitor's methods...they get priority!
        if (next_count > 0){
            sem_post(&next_sem);
        }else{
            sem_post(&mutex_sem);
        }
    }

    void request_right_chopstick()
    {
        //thread need mutex acces to enter the moniter
		sem_wait(&mutex_sem);

        //lets check that there is at least a single chopstick is avalible to pick up.
		while(chopsticks_available < 1){
			condition_wait(condition_can_get_1_sem, condition_can_get_1_count);

		}
        //decreament the global counter of chopsticks 
		chopsticks_available --;

		if (chopsticks_available >= 1){
            //If at least a chopstick remains, post to the 'at least one chopstick available' condition
			condition_post(condition_can_get_1_sem, condition_can_get_1_count);
            //If at least 2 chopstick remains, post to the 'at least 2 chopstick available' condition
			if(chopsticks_available >= 2){
				condition_post(condition_can_get_2_sem, condition_can_get_2_count);

			}
		}

        
        //Threads waiting for next_sem are waiting INSIDE one of this monitor's methods...they get priority!
        if (next_count > 0){
            sem_post(&next_sem);
        }else{
            sem_post(&mutex_sem);
        } 
    }

    void return_chopsticks()
    {
        //mutex that allow us to emter the struck to modify
        sem_wait(&mutex_sem);
		

		//since we are not requesting any chopstick we will return the chopsticks by 
		//incrementing the counter of the avalible chopsticks 
		chopsticks_available = chopsticks_available + 2;
    
        if (chopsticks_available >= 2){
			condition_post(condition_can_get_2_sem, condition_can_get_2_count);
			if(chopsticks_available >= 1){
				condition_post(condition_can_get_1_sem, condition_can_get_1_count);

			}
		}
		
        //Threads waiting for next_sem are waiting INSIDE one of this monitor's methods...they get priority!
        if (next_count > 0){
            sem_post(&next_sem);
        }else{
            sem_post(&mutex_sem);
        }    
    }

     void average_time(double a){
        
        //this mutex will allow us to modify the struct and the average total time
        sem_wait(&mutex_sem);
        
        double temp_time = a;
        //lets now add the time to the total time 
        total_time = temp_time + total_time;

        
        //Threads waiting for next_sem are waiting INSIDE one of this monitor's methods...they get priority!
         if (next_count > 0){
            sem_post(&next_sem);
        }else{
            sem_post(&mutex_sem);
        }  
    }


};

struct WaiterMonitor waiter;

//Function for the threads
void * thread_function(void * arg){

	//casting a integer ointer to a int
    int id = *((int*)arg);
    srand(time(NULL) + id);

    //initializing time in order to compute the time for each philosopher to wait
    for(int i = 0; i < 3; i++)
    {

        printf("Philosopher %d is thinking\n", id);
        int think_time = 1 + (rand() % 5);
        sleep(think_time);

        //we start our timer
        double start = time(NULL);

        printf("Philospher %d is hungry\n", id);

        waiter.request_left_chopstick();

        printf("Philospher %d has picked up left chopstick\n", id);

        //Get the right chopstick
        waiter.request_right_chopstick();


        printf("Philospher %d has picked up right chopstick\nPhilosopher %d is eating\n", id, id);
        //printf("chopsticks avalible %d\n", waiter.chopsticks_available);

        //end timer here
        double end = time(NULL);
        double duration = end -start;
        //we will pass the duration to our function that will keep track of the over all time
        waiter.average_time(duration);

        //Eat
        sleep(5);

        printf("Philospher %d is done eating\n", id);
        


        //Return our chopsticks
        waiter.return_chopsticks();
        printf("chopsticks avalible %d\n", waiter.chopsticks_available);
        
    
    }
    pthread_exit(NULL);
}

int main(int argc, char *argv[]){

    //this section will take the number from the user, this number is the number of chopsticks 
    int chop; 
    double average_time;
    
    //lets take the input of from the user of how many chopsticks they need
    printf("Enter the number of chopsticks, please:\n");
    scanf("%d", &chop);
    while (chop <= 4 || chop >= 11){
        //chop = 0;
        printf("You have enter a number that is not in range, TRY AGAIN, THANSK:\n");
        scanf("%d", &chop);
    }
    //we call the struct and modify the nunmber of the chopsticks avalible.
    waiter.chopsticks_available = chop;

   
    waiter.init();
    //initialization of philosophers, in total 5 phil 
    pthread_t philosopher_1;
    pthread_t philosopher_2;
    pthread_t philosopher_3;
    pthread_t philosopher_4;
    pthread_t philosopher_5;
    
    //thread id for each of the threads
    int id1 = 1;
    int id2 = 2;
    int id3 = 3;
    int id4 = 4;
    int id5 = 5;

    //create the threads with their corresponding id. each thread will run the thread function
    pthread_create(&philosopher_1, NULL, thread_function, (void*) &id1);
    pthread_create(&philosopher_2, NULL, thread_function, (void*) &id2);
    pthread_create(&philosopher_3, NULL, thread_function, (void*) &id3);
    pthread_create(&philosopher_4, NULL, thread_function, (void*) &id4);
    pthread_create(&philosopher_5, NULL, thread_function, (void*) &id5);

    //join each thread so they can end safely
    pthread_join(philosopher_1, NULL);
    pthread_join(philosopher_2, NULL);
    pthread_join(philosopher_3, NULL);
    pthread_join(philosopher_4, NULL);
    pthread_join(philosopher_5, NULL);

    //finaly we will print the total average of the thinking time.
    average_time = waiter.total_time;
    printf("the over all time in seconds: %fs\n", average_time);
    average_time = average_time /15.0;

    //lets now print the result 
    printf("The average time for each philosopher is the following in s: %f seconds\n", average_time);

    //lets now safely destroy the semaphore and condition varial and the mutex
    waiter.destroy();
}
