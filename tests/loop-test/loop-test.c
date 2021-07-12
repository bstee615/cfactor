int main()
{
    int x = 0;
    int y = 0;
    while (x < 10) {
        x += 1;
        if (x > 2) {
            y -= 1;
            x += 2;
        }
    }
    return x - y;
}
