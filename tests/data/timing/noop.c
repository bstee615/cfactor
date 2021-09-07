int main()
{
    int x = 0;
    int y;
    y = 5;
    for (; x < 10; x += 2) {
        y ++;
    }
    if (y < 10) {
        return x;
    }
    else {
        y += 5
    }
    return y;
}