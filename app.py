    import os
from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd
from sklearn.cluster import KMeans
from bs4 import BeautifulSoup
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    user_input = request.json['query']
    url = "https://www.flipkart.com/search?q=" + user_input
    try:
        products, best = scrape_products(url)
        return jsonify({'products': products, 'best_product': best})
    except Exception as e:
        return jsonify({'error': str(e)})

def scrape_products(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    name, price, rating, image_urls, links = [], [], [], [], []

    products = soup.find_all('div', attrs={'class': '_75nlfW'})
    for product in products:
        try:
            name_tag = product.find('div', attrs={'class': 'KzDlHZ'})
            price_tag = product.find('div', attrs={'class': 'Nx9bqj _4b5DiR'})
            rating_tag = product.find('div', attrs={'class': 'XQDdHH'})
            image_tag = product.find('img')
            link_tag = product.find('a', href=True)

            if name_tag and price_tag and image_tag and link_tag:
                name.append(name_tag.text.strip())
                price.append(price_tag.text.replace('₹', '').replace(',', '').strip())
                rating.append(float(rating_tag.text.strip()) if rating_tag else 0)
                image_urls.append(image_tag['src'])
                links.append("https://www.flipkart.com" + link_tag['href'])
        except:
            continue

    df = pd.DataFrame({'Name': name, 'Price': price, 'Rating': rating, 'Image': image_urls, 'Link': links})
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Price'])

    if df.empty:
        return [], {}

    kmeans = KMeans(n_clusters=3, random_state=42)
    df['Cluster'] = kmeans.fit_predict(df[['Price']])

    cluster_to_suggest = df['Cluster'].value_counts().idxmin()
    suggested_products = df[df['Cluster'] == cluster_to_suggest].head(3)
    best_product = df.loc[df['Rating'].idxmax()].to_dict()

    return suggested_products.to_dict(orient='records'), best_product

if __name__ == '__main__':

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=True)

