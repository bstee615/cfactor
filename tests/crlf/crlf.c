int main(int argc, char *argv[])
{
	unsigned i;
	char buff[512];
	char sys[512];
	if (fgets(buff,512 - SIZE_CMD,stdin))
	{
		strcpy(sys, cmd);
		strcat(sys, buff);
		for (i=0;i<5;++i) {
			fprintf(stderr, "system() failed");
		}
	}
	return 0;
}
