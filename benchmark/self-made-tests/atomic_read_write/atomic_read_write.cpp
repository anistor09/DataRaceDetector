#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <stdatomic.h>

volatile unsigned long long test = 0;
uint64_t *ptr;
_Atomic int sync_var = 0;

void *a(void *obj)
{
      *ptr = 5;
      usleep(1);
      printf("Thread A reads: %lld\n", test);
      usleep(1);
      atomic_store_explicit(&sync_var, 1, memory_order_release);
      return NULL;
}

void *b(void *obj)
{
    usleep(1);
    usleep(1);
    usleep(1);
    usleep(1);
    usleep(1);
    int temp = atomic_load_explicit(&sync_var, memory_order_acquire);
    if (temp != 0) { // ensure the value is used
        usleep(1);
    }
    usleep(1);
    *ptr = 4;
    usleep(1);
    printf("Thread B reads: %lld\n", test);
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
}