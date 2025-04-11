#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

volatile unsigned long long test = 0;
uint64_t *ptr;

// Global mutex and condition variable for notify/wait
pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t cond = PTHREAD_COND_INITIALIZER;

void *a(void *obj)
{
    pthread_mutex_lock(&lock);
    usleep(1);
    *ptr = 4;                
    pthread_cond_signal(&cond); 
    pthread_mutex_unlock(&lock);

    usleep(1);
    printf("Thread A reads: %llu\n", test);
    return NULL;
}

void *b(void *obj)
{
    pthread_mutex_lock(&lock);
    // force the writes to be synchronized
    while (*ptr != 4) {
        pthread_cond_wait(&cond, &lock);
    }
    usleep(1);
    *ptr = 5;  
    pthread_mutex_unlock(&lock);

    usleep(1);
    printf("Thread B reads: %llu\n", test);
    return NULL;
}

int main()
{
    pthread_t t1, t2;
    ptr = (uint64_t *)&test;

    printf("Main thread: creating 2 threads\n");
    pthread_create(&t1, NULL, a, NULL);
    pthread_create(&t2, NULL, b, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    printf("Main thread is finishing\n");
    return 0;
}
