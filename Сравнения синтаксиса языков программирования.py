                                                 # Python
def factorial(n):
    """Вычисление факториала числа"""
    if n < 0:
        raise ValueError("Факториал не определён для отрицательных чисел")
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

# Пример использования
number = 5
print(f"{number}! = {factorial(number)}")

# ========= Вывод: 5! = 120 =============

                                                  


                                                      # Java
public class Factorial {
    public static long factorial(int n) {
        if (n < 0) {
            throw new IllegalArgumentException("Факториал не определён для отрицательных чисел");
        }
        if (n == 0 || n == 1) {
            return 1;
        }

        long result = 1;
        for (int i = 2; i <= n; i++) {
            result *= i;
        }
        return result;
    }

    public static void main(String[] args) {
        int number = 5;
        System.out.println(number + "! = " + factorial(number));
    }
}

# ========= Вывод: 5! = 120 =============




                                                # C++
#include <iostream>
#include <stdexcept>

long long factorial(int n) {
    if (n < 0) {
        throw std::invalid_argument("Факториал не определён для отрицательных чисел");
    }
    if (n == 0 || n == 1) {
        return 1;
    }

    long long result = 1;
    for (int i = 2; i <= n; ++i) {
        result *= i;
    }
    return result;
}

int main() {
    int number = 5;
    try {
        std::cout << number << "! = " << factorial(number) << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Ошибка: " << e.what() << std::endl;
    }
    return 0;
}

# ========= Вывод: 5! = 120 =============
