from groq import Groq
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv
import logging
import json
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

client = Groq(api_key=GROQ_API_KEY)
newsapi = NewsApiClient(api_key=NEWSAPI_KEY)

def fetch_latest_economic_news():
    try:
        logger.info("Fetching latest Pakistan economic news")
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        response = newsapi.get_everything(
            q='Pakistan economy',
            language='en',
            sort_by='publishedAt',
            from_param=from_date,
            to=to_date,
            page_size=5
        )
        articles = response.get('articles', [])
        if not articles:
            logger.warning("No recent economic news found")
            return "No recent economic news available."
        
        news_summary = "Recent Pakistan Economic News:\n"
        for article in articles:
            title = article.get('title', 'No title')
            description = article.get('description', 'No description')
            published_at = article.get('publishedAt', 'Unknown date')
            news_summary += f"- {title} ({published_at}): {description}\n"
        logger.info(f"Fetched news: {news_summary}")
        return news_summary
    except Exception as e:
        logger.error(f"NewsAPI error: {str(e)}")
        return f"Error fetching news: {str(e)}"

def handle_economy_query(question):
    system_prompt = """
    You are an expert on Pakistan's economy. Answer questions related to Pakistan's 
    macroeconomic indicators, GDP, inflation, fiscal policy, trade, or economic news. 
    Use the provided news context for recent updates. If the query is not related to 
    Pakistan's economy, respond with:
    'Please ask a question related to Pakistan's economy.'
    """
    
    try:
        # Fetch latest news if the query asks for recent updates
        news_context = ""
        if any(keyword in question.lower() for keyword in ["latest", "recent", "news", "update"]):
            news_context = fetch_latest_economic_news()
        
        payload = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": f"{system_prompt}\nNews Context: {news_context}"},
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
        logger.error(f"Economy query error: {str(e)}")
        if hasattr(e, 'response'):
            logger.error(f"Error response: {e.response.text}")
        return f"Error processing economy query: {str(e)}"