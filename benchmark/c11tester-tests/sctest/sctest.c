#include <stdio.h>
#include <threads.h>
#include <stdlib.h>
#include <unistd.h> // Required for usleep

#include "librace.h"

volatile int x_val, y_val, z_val;
int *x = (int*)&x_val;
int *y = (int*)&y_val;
int *z = (int*)&z_val;

static int r1, r2, r3;

static void a(void *obj)
{
    usleep(4); // 1 millisecond
    *z = 1;
}

static void b(void *obj)
{
    usleep(3); // 1 millisecond
    *x = 1;
    *y = 1;
    r1 = *z;
    printf("x = %d, y = %d, z = %d\n", x_val, y_val, z_val);
}

static void c(void *obj)
{
    usleep(2); // 1 millisecond
    *z = 2;
    *x = 2;
    r2 = *y;
    printf("x = %d, y = %d, z = %d\n", x_val, y_val, z_val);
}

static void d(void *obj)
{
    usleep(1); // 1 millisecond
    *z = 3;
    *y = 2;
    r3 = *x;
    printf("x = %d, y = %d, z = %d\n", x_val, y_val, z_val);
}

int main(int argc, char **argv)
{
    thrd_t t1, t2, t3, t4;

    *x = 0;
    *y = 0;
    *z = 0;

    thrd_create(&t1, (thrd_start_t)&a, NULL);
    thrd_create(&t2, (thrd_start_t)&b, NULL);
    thrd_create(&t3, (thrd_start_t)&c, NULL);
    thrd_create(&t4, (thrd_start_t)&d, NULL);

    thrd_join(t1);
    thrd_join(t2);
    thrd_join(t3);
    thrd_join(t4);

    printf("\nFinal values:\n");
    printf("x = %d, y = %d, z = %d\n", x_val, y_val, z_val);
    printf("r1 = %d, r2 = %d, r3 = %d\n", r1, r2, r3);

    return 0;
}