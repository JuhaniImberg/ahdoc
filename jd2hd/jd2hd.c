#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#define ERROR(i, ...)                                                   \
    if(i) {                                                             \
        fprintf(stderr, "ERROR %s:%d %s -> %s (%d)\n",                  \
                __FILE__, __LINE__, __func__, strerror(errno), errno);  \
        fprintf(stderr, __VA_ARGS__);                                   \
        fprintf(stderr, "\n");                                          \
        exit(i);                                                        \
    }

int main(int argv, char **argc) {
    ERROR(argv < 2, "%s needs some arguments", argc[0]);
    FILE *fp;
    int a, b, c, e, i, p;
    for(i = 1; i < argv; i++) {
        a = b = c = ' ';
        p = 0;
        fp = fopen(argc[i], "r+");
        ERROR(fp == NULL, "No such file \"%s\"", argc[1]);
        while((c = fgetc(fp)) != EOF) {
            if(a == '/' && b == '*' && c == '*' && p == 0) {
                e = fseek(fp, -1, SEEK_CUR);
                ERROR(e != 0, "fseek failed");
                fputc('!', fp);
                e = fseek(fp, 0, SEEK_CUR);
                ERROR(e != 0, "fseek failed");
            }
            if (c == '\n') {
                p = 1;
            } else {
                p = 0;
            }
            a = b;
            b = c;
        }
        e = fclose(fp);
        ERROR(e != 0, "fclose failed");
    }
    return 0;
}
