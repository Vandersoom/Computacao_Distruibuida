from celery import shared_task
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from stocks.models import Stock
import re

logger = logging.getLogger(__name__)

@shared_task
def get_stock_price(stock_name):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    # Adicionar user-agent para evitar detecção de bot
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(
            options=options,
            service=ChromeService(ChromeDriverManager().install())
        )
        
        # Configurar um timeout maior para esperas
        wait = WebDriverWait(driver, 15)
        
        # Mapear códigos de ações brasileiras para símbolos do Google Finance
        stock_mapping = {
            'PETR4': 'PETR4:BVMF',  # Petrobras PN
            'PETR3': 'PETR3:BVMF',  # Petrobras ON
            'VALE3': 'VALE3:BVMF',  # Vale
            'ITUB4': 'ITUB4:BVMF',  # Itaú
            'BBDC4': 'BBDC4:BVMF',  # Bradesco
        }
        
        # Obter o símbolo correto para o Google Finance
        symbol = stock_mapping.get(stock_name.upper(), f"{stock_name.upper()}:BVMF")
        
        # Acessar diretamente o Google Finance
        url = f'https://www.google.com/finance/quote/{symbol}'
        logger.info(f"Acessando URL: {url}")
        driver.get(url)
        
        # Esperar para carregar a página
        sleep(3)
        
        # Salvar screenshot para debug
        screenshot_path = f'/tmp/{stock_name}_finance.png'
        driver.save_screenshot(screenshot_path)
        logger.info(f"Screenshot salvo em: {screenshot_path}")
        
        # Tentar encontrar o preço no Google Finance
        price_text = None
        
        try:
            # Seletor principal do Google Finance
            price_element = wait.until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "YMlKec") and contains(@class, "fxKbKc")]'))
            )
            price_text = price_element.text
            logger.info(f"Preço encontrado no seletor principal: {price_text}")
        except Exception as e:
            logger.info(f"Não foi possível encontrar o preço com o seletor principal: {str(e)}")
            
            # Tentar seletores alternativos
            selectors = [
                '//div[contains(@class, "YMlKec")]',
                '//div[contains(@class, "kf1m0")]',
                '//span[@jsname="vWLAgc"]',
                '//div[@aria-label="Last price"]',
                '//div[contains(@class, "P6K39c") and contains(@class, "W9Ufie")]//div[contains(@class, "YMlKec")]'
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        for element in elements:
                            text = element.text.strip()
                            logger.info(f"Texto encontrado: '{text}'")
                            
                            # Verificar se o texto parece um preço
                            if re.search(r'(\d+[,.]\d+|\d+)', text):
                                price_text = text
                                logger.info(f"Possível preço encontrado: {price_text}")
                                break
                        
                        if price_text:
                            break
                except Exception as e:
                    logger.info(f"Erro ao usar seletor {selector}: {str(e)}")
                    continue
        
        # Se não encontrou no Google Finance, tentar com a busca normal do Google
        if not price_text:
            logger.info("Tentando busca alternativa no Google")
            
            # Acessar a busca do Google
            search_url = f'https://www.google.com/search?q=preço+ação+{stock_name.replace(":", "+")}'
            logger.info(f"Acessando URL alternativa: {search_url}")
            driver.get(search_url)
            
            sleep(3)
            
            # Salvar screenshot para debug
            search_screenshot = f'/tmp/{stock_name}_search.png'
            driver.save_screenshot(search_screenshot)
            logger.info(f"Screenshot da busca salvo em: {search_screenshot}")
            
            # Tentar encontrar o preço na página de busca
            search_selectors = [
                '//div[contains(@data-attrid, "Price")]//span',
                '//div[contains(@class, "BNeawe") and contains(@class, "iBp4i")]',
                '//div[contains(@class, "BNeawe") and contains(@class, "tAd8D") and contains(@class, "AP7Wnd")]',
                '//span[contains(text(), "R$")]',
                '//div[contains(text(), "R$")]'
            ]
            
            for selector in search_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        for element in elements:
                            text = element.text.strip()
                            logger.info(f"Texto encontrado na busca: '{text}'")
                            
                            # Verificar se o texto parece um preço
                            if re.search(r'(\d+[,.]\d+|\d+)', text):
                                price_text = text
                                logger.info(f"Possível preço encontrado na busca: {price_text}")
                                break
                        
                        if price_text:
                            break
                except Exception as e:
                    logger.info(f"Erro ao usar seletor de busca {selector}: {str(e)}")
                    continue
        
        # Se ainda não encontrou, tentar extrair do HTML da página
        if not price_text:
            logger.info("Tentando extrair preço do HTML da página")
            page_source = driver.page_source
            
            # Padrões comuns de preço
            price_patterns = [
                r'R\$\s*(\d+[,.]\d+)',
                r'(\d+[,.]\d+)\s*reais',
                r'(\d+[,.]\d+)'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_source)
                if matches:
                    price_text = matches[0]
                    logger.info(f"Preço encontrado via regex: {price_text}")
                    break
        
        # Se ainda não encontrou, definir valor padrão
        if not price_text:
            logger.warning(f"Não foi possível encontrar o preço para {stock_name}")
            price_text = "0.0"
        
        # Limpar e converter o valor do preço
        price = price_text.replace('R$', '').replace('$', '').strip()
        
        # Lidar com formatos diferentes de número
        if ',' in price and '.' in price:
            # Formato brasileiro com separador de milhar (ex: 1.234,56)
            price = price.replace('.', '').replace(',', '.')
        elif ',' in price:
            # Formato brasileiro sem separador de milhar (ex: 123,45)
            price = price.replace(',', '.')
        
        # Extrair apenas o primeiro número encontrado
        price_match = re.search(r'\d+\.\d+|\d+', price)
        if price_match:
            price = price_match.group()
        else:
            price = "0.0"
            
        logger.info(f"Preço final para {stock_name}: {price}")
        
        # Fechar o navegador
        driver.quit()
        
        # Salvar no banco de dados
        try:
            Stock.objects.create(
                name=stock_name,
                price=float(price)
            )
            logger.info(f"Registro criado para {stock_name}: {price}")
        except Exception as db_error:
            logger.error(f"Erro ao salvar no banco de dados: {str(db_error)}")
        
        return price
        
    except Exception as e:
        logger.error(f"Erro na execução da task: {str(e)}")
        # Garantir que o driver seja fechado em caso de erro
        try:
            driver.quit()
        except:
            pass
        return f"Erro: {str(e)}"
