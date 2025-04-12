#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>
#include <unistd.h>

volatile unsigned long long x_val = 0, y_val = 0;
uint64_t *x, *y;

void *a(void *obj)
{
    usleep(1); // 10 microseconds

    printf("expected was 0, but x is %lu\n", *x);

    if (*x == 0) {
        *x = 315;
        printf("Compare and exchange succeeded\n");
    } else {
        printf("Compare and exchange failed\n");
    }

    printf("Then x = %llu\n", x_val);
    printf("expected: 0");
    return NULL;
}

void *b(void *obj)
{
    usleep(100); // 1 microsecond

    unsigned long long v3 = *y;
    *y = 2;

    unsigned long long v4 = *x;
    *x = 5;

    printf("v3 = %llu, v4 = %llu\n", v3, v4);
    printf("Auxiliar_print x = %llu, y = %llu\n", x_val, y_val);
    return NULL;
}

int main()
{
    pthread_t t1, t2;
    x = (uint64_t *)&x_val;
    y = (uint64_t *)&y_val;
    printf("Main thread: creating 2 threads\n");
    pthread_create(&t1, NULL, a, NULL);
    pthread_create(&t2, NULL, b, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("Main thread is finishing\n");


    return 0;
}