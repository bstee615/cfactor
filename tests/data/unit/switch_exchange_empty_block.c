int main(int argc, char **argv)
{
    int x = 0;
    switch (argc)
    {
    case 1:
    case 2:
        break;
    case 3:
        x = 10;
        x ++;
        break;
    default:
        return argc;
    }
    return x;
}