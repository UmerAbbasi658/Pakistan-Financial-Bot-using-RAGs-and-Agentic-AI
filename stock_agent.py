import requests
from bs4 import BeautifulSoup
from groq import Groq
import os
from dotenv import load_dotenv
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def fetch_market_summary():
    try:
        logger.info("Fetching PSX market summary from https://www.psx.com.pk/market-summary/")
        url = "https://www.psx.com.pk/market-summary/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Note: Class names are placeholders; adjust after HTML inspection
        summary = "PSX Market Summary ({}):\n".format(datetime.now().strftime('%Y-%m-%d'))
        
        # KSE-100 Index
        kse100 = soup.find('div', class_='index-data')
        if kse100:
            index_value = kse100.find('span', class_='value').text.strip() if kse100.find('span', class_='value') else 'N/A'
            change = kse100.find('span', class_='change').text.strip() if kse100.find('span', class_='change') else 'N/A'
            summary += f"KSE-100 Index: {index_value}, Change: {change}\n"
        else:
            summary += "KSE-100 Index: Data unavailable\n"

        # Turnover
        turnover = soup.find('div', class_='turnover-data')
        if turnover:
            volume = turnover.find('span', class_='volume').text.strip() if turnover.find('span', class_='volume') else 'N/A'
            value = turnover.find('span', class_='traded-value').text.strip() if turnover.find('span', class_='traded-value') else 'N/A'
            summary += f"Market Turnover: Volume: {volume}, Value: {value}\n"
        else:
            summary += "Market Turnover: Data unavailable\n"

        # Top Gainers/Losers
        gainers = soup.find('div', class_='top-gainers')
        losers = soup.find('div', class_='top-losers')
        if gainers or losers:
            summary += "Top Stocks:\n"
            if gainers:
                for item in gainers.find_all('div', class_='stock', limit=3):
                    name = item.find('span', class_='name').text.strip() if item.find('span', class_='name') else 'N/A'
                    change = item.find('span', class_='change').text.strip() if item.find('span', class_='change') else 'N/A'
                    summary += f"- Gainer: {name}, Change: {change}\n"
            if losers:
                for item in losers.find_all('div', class_='stock', limit=3):
                    name = item.find('span', class_='name').text.strip() if item.find('span', class_='name') else 'N/A'
                    change = item.find('span', class_='change').text.strip() if item.find('span', class_='change') else 'N/A'
                    summary += f"- Loser: {name}, Change: {change}\n"
        else:
            summary += "Top Stocks: Data unavailable\n"

        logger.info(f"Fetched market summary: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Market summary scraping error: {str(e)}")
        return f"Error fetching PSX market summary: {str(e)}"

def handle_market_summary_query(question):
    system_prompt = """
    You are a financial expert specializing in the Pakistan Stock Market (PSX). 
    Answer questions about PSX market trends, KSE-100 index, turnover, or top gainers/losers using the provided market summary.
    If the query is not related to the PSX market summary, respond with:
    'Please ask a question related to the PSX market summary.'
    """
    
    try:
        summary_context = fetch_market_summary()
        payload = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": f"{system_prompt}\nPSX Market Summary: {summary_context}"},
                {"role": "user", "content": question}
            ],
            "max_tokens": 300,
            "temperature": 0.7
        }
        logger.info(f"Sending Groq request: {json.dumps(payload)}")
        response = client.chat.completions.create(**payload)
        answer = response.choices[0].message.content
        logger.info(f"Groq response: {answer}")
        return answer
    except Exception as e:
        logger.error(f"Market summary query error: {str(e)}")
        return f"Error processing market summary query: {str(e)}"