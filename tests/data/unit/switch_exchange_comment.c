int main(int argc, char **argv)
{
    int x = 0;
    switch (argc)
    {
    case 1:
    case 2:
        x = 5;
        break;
        /*Wow, this comment is confusing!*/
    case 3:
        // include me ;-;
        x = 10;
        x ++;
        break;
    default:
        return argc;
    }
    return x;
}