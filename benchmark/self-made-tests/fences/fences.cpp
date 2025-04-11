#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <stdatomic.h>

volatile unsigned long long test = 0;
uint64_t *ptr = NULL;

_Atomic int sync_flag = 0;

void *a(void *obj)
{
    *ptr = 4;

    // prevents the writes and reads before it to be put after it
    atomic_thread_fence(memory_order_release);
    atomic_store_explicit(&sync_flag, 1, memory_order_relaxed);

    usleep(1);
    printf("Thread A reads: %llu\n", test);
    return NULL;
}

void *b(void *obj)
{
    // Wait until flag is set
    // force the atomic read to be after the atomic write in the other thread
    while (atomic_load_explicit(&sync_flag, memory_order_relaxed) != 1) {
        usleep(1);
    }

    /// prevents the writes and reads after it to be put before it
    atomic_thread_fence(memory_order_acquire);

    // Now read test (which might be updated via ptr)
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
