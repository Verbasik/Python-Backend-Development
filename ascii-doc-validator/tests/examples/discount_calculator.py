class DiscountCalculator:
    """
    Калькулятор скидок для различных товаров и покупателей.
    """
    
    def __init__(self, base_discount_percent=0):
        """
        Инициализация калькулятора скидок с базовым процентом.
        
        Args:
            base_discount_percent: Базовый процент скидки (по умолчанию 0)
        """
        self.base_discount_percent = base_discount_percent
    
    def calculate_discount(self, price, customer_type="regular", loyalty_years=0):
        """
        Расчет скидки на основе цены, типа клиента и лет лояльности.
        
        Args:
            price: Исходная цена товара
            customer_type: Тип клиента ('regular', 'premium', 'vip')
            loyalty_years: Количество лет, которые клиент является покупателем
            
        Returns:
            float: Итоговая сумма скидки
            
        Raises:
            ValueError: Если передан неизвестный тип клиента
        """
        discount_percent = self.base_discount_percent
        
        # Добавить скидку в зависимости от типа клиента
        if customer_type == "regular":
            discount_percent += 0
        elif customer_type == "premium":
            discount_percent += 5
        elif customer_type == "vip":
            discount_percent += 10
        else:
            raise ValueError(f"Неизвестный тип клиента: {customer_type}")
            
        # Добавить скидку за лояльность (1% за каждый год, максимум 5%)
        loyalty_discount = min(loyalty_years, 5)
        discount_percent += loyalty_discount
        
        # Рассчитать итоговую сумму скидки
        discount_amount = price * (discount_percent / 100)
        
        return discount_amount
    
    def apply_discount(self, price, customer_type="regular", loyalty_years=0):
        """
        Применить скидку к цене товара.
        
        Args:
            price: Исходная цена товара
            customer_type: Тип клиента ('regular', 'premium', 'vip')
            loyalty_years: Количество лет, которые клиент является покупателем
            
        Returns:
            float: Цена товара после применения скидки
        """
        discount = self.calculate_discount(price, customer_type, loyalty_years)
        return price - discount
    
    def get_discount_percent(self, customer_type="regular", loyalty_years=0):
        """
        Получить процент скидки для указанных параметров.
        
        Args:
            customer_type: Тип клиента ('regular', 'premium', 'vip')
            loyalty_years: Количество лет, которые клиент является покупателем
            
        Returns:
            float: Процент скидки
        """
        discount_percent = self.base_discount_percent
        
        # Добавить скидку в зависимости от типа клиента
        if customer_type == "regular":
            discount_percent += 0
        elif customer_type == "premium":
            discount_percent += 5
        elif customer_type == "vip":
            discount_percent += 10
        else:
            raise ValueError(f"Неизвестный тип клиента: {customer_type}")
            
        # Добавить скидку за лояльность (1% за каждый год, максимум 5%)
        loyalty_discount = min(loyalty_years, 5)
        discount_percent += loyalty_discount
        
        return discount_percent


# Пример использования
if __name__ == "__main__":
    calculator = DiscountCalculator(base_discount_percent=2)
    
    # Пример расчета для обычного клиента
    regular_price = 1000
    regular_discount = calculator.calculate_discount(regular_price)
    regular_final = calculator.apply_discount(regular_price)
    
    # Пример расчета для премиум клиента с 3 годами лояльности
    premium_price = 1000
    premium_discount = calculator.calculate_discount(premium_price, "premium", 3)
    premium_final = calculator.apply_discount(premium_price, "premium", 3)
    
    # Пример расчета для VIP клиента с 7 годами лояльности
    vip_price = 1000
    vip_discount = calculator.calculate_discount(vip_price, "vip", 7)
    vip_final = calculator.apply_discount(vip_price, "vip", 7)
    
    # Вывод результатов
    print(f"Обычный клиент: цена {regular_price}, скидка {regular_discount}, итого {regular_final}")
    print(f"Премиум клиент (3 года): цена {premium_price}, скидка {premium_discount}, итого {premium_final}")
    print(f"VIP клиент (7 лет): цена {vip_price}, скидка {vip_discount}, итого {vip_final}")