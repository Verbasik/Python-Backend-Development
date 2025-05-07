/**
 * Простой калькулятор для выполнения базовых арифметических операций.
 */
public class Calculator {
    /**
     * Складывает два числа.
     * @param a первое число
     * @param b второе число
     * @return сумма a и b
     */
    public int add(int a, int b) {
        return a + b;
    }

    /**
     * Вычитает второе число из первого.
     * @param a уменьшаемое
     * @param b вычитаемое
     * @return разность a и b
     */
    public int subtract(int a, int b) {
        return a - b;
    }

    /**
     * Умножает два числа.
     * @param a первый множитель
     * @param b второй множитель
     * @return произведение a и b
     */
    public int multiply(int a, int b) {
        return a * b;
    }

    /**
     * Делит первое число на второе.
     * @param a делимое
     * @param b делитель (не должен быть равен 0)
     * @return частное a и b
     * @throws ArithmeticException если b равно 0
     */
    public double divide(int a, int b) throws ArithmeticException {
        if (b == 0) {
            throw new ArithmeticException("Division by zero");
        }
        return (double) a / b;
    }

    /**
     * Проверяет, является ли число четным.
     * @param number число для проверки
     * @return true, если число четное, иначе false
     */
    public boolean isEven(int number) {
        return number % 2 == 0;
    }
}