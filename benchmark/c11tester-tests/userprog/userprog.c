#include <stdio.h>
#include <threads.h>
#include <unistd.h>

#include "librace.h"

volatile int x_val = 0;
volatile int y_val = 0;
int z;

int *x = (int *)&x_val;
int *y = (int *)&y_val;

static void a(void *obj)
{
    usleep(1000); // 1 millisecond

    int r1 = *y;
    *x = r1;
//  z = 1;
    printf("r1=%d %d\n", r1, x_val);
}

static void b(void *obj)
{
    usleep(1000); // 1 millisecond

    int r2 = *x;
    *y = 42;
//  z = 2;
    printf("r2=%d %d\n", r2, y_val);
}

int main(int argc, char **argv)
{
    thrd_t t1, t2;

    *x = 30;
    *y = 0;

    printf("Main thread: creating 2 threads\n");
    thrd_create(&t1, (thrd_start_t)&a, NULL);
    thrd_create(&t2, (thrd_start_t)&b, NULL);

    thrd_join(t1);
    thrd_join(t2);
    printf("Main thread is finished\n");

    return 0;
}