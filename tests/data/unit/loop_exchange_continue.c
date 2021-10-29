int main()
{
    int x = 0;
    for (int i = 0; i < 10; i ++)
    {
        if (i % 2 == 0)
        {
            continue;
        }
        x += 1;
    }
    return x;
}