int main(int argc, char **argv)
{
    int x = 0;
    switch (argc)
    {
    case 1:
    case 2:
        x = 5;
        break;
    default:
        return argc;
    case 3:
        x = 10;
        x ++;
        break;
    }
    return x;
}