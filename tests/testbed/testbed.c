/*
Description: A chroot() is performed without a chdir().
Keywords: Unix C Size0 Complex0 Api Chroot

Copyright 2005 Fortify Software.

Permission is hereby granted, without written agreement or royalty fee, to
use, copy, modify, and distribute this software and its documentation for
any purpose, provided that the above copyright notice and the following
three paragraphs appear in all copies of this software.

IN NO EVENT SHALL FORTIFY SOFTWARE BE LIABLE TO ANY PARTY FOR DIRECT,
INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE
USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF FORTIFY SOFTWARE HAS
BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMANGE.

FORTIFY SOFTWARE SPECIFICALLY DISCLAIMS ANY WARRANTIES INCLUDING, BUT NOT
LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE, AND NON-INFRINGEMENT.

THE SOFTWARE IS PROVIDED ON AN "AS-IS" BASIS AND FORTIFY SOFTWARE HAS NO
OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR
MODIFICATIONS.
*/

#include <fcntl.h>
#include <unistd.h>
#include <string.h>

#define DIR	"/tmp"
#define FILE	"/etc/passwd"

int switchtest(char a)
{
    char *x;
    int y = 1;
    int z = 0;
    switch(a)
    {
        case 'z':
        case 'a':
        case 'b':
        y = 10;
        if (y == 10 && y > 4 && x == 5) {
            x = "5";
            break;
        }
        y = 3;
        break;
        case 'c':
        y --;
        z = 3;
        z += 4;
        break;
        default:
        x = "1";
        y ++;
        z = 55;
        break;
    }
    return strlen(x) * y + z;
}

int looptest()
{
    int x = 0;
    for (int i = 0; i < 10; i ++) {
        x += 1;
    }
    return x;
}

void
test(char *str)
{
	int fd;

	if(chroot(DIR) < 0)			/* BAD */
		return;
	fd = open(FILE, O_RDONLY);		/* BAD */
	if(fd >= 0)
		close(fd);
}

int
main(int argc, char **argv)
{
	char *userstr;

	if(argc > 1) {
		userstr = argv[1];
		test(userstr);
	}

    int s = switchtest(argv[2][0]);
    int l = looptest();

	return s + l;
}

