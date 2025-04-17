import speech_recognition as sr
import pyttsx3
import os
import time
import requests
import pandas as pd
from sklearn.cluster import KMeans
from bs4 import BeautifulSoup
from IPython.display import display, HTML
import webbrowser
import warnings

#Hiding warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Initialize pyttsx3 for speech synthesis
engine = pyttsx3.init()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("I am listening..")
        audio = r.listen(source, phrase_time_limit=5)
    data = ""
    try:
        data = r.recognize_google(audio, language='en-US')
        print("You said: " + data)
    except sr.UnknownValueError:
        print("I cannot hear you")
    except sr.RequestError:
        print("Request Failed")
    return data

def respond(text):
    print(text)
    engine.say(text)
    engine.runAndWait()

def voice_assistant(data):
    if "hello" in data.casefold():
        respond("What should I search?")
        query = listen()
        print(query)
        url = "https://www.flipkart.com/search?q=" + query
        web_scrap(url)

    if "goodbye" in data:
        respond("Goodbye! Have a pleasant shopping")
        return False

    return True

def web_scrap(url):
    try:
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
            respond("No products found. Please try again.")
            return

        # KMeans clustering
        kmeans = KMeans(n_clusters=3, random_state=42)
        df['Cluster'] = kmeans.fit_predict(df[['Price']])

        # Get top affordable products
        cluster_to_suggest = df['Cluster'].value_counts().idxmin()
        suggested_products = df[df['Cluster'] == cluster_to_suggest].head(3)

        # Display HTML table with images
        html = "<h3>Top Affordable Products</h3><table border='1' style='border-collapse:collapse;'>"
        html += "<tr><th>Image</th><th>Product Name</th><th>Price (₹)</th><th>Rating</th></tr>"

        for _, row in suggested_products.iterrows():
            html += f"<tr><td><img src='{row['Image']}' width='100'></td>"
            html += f"<td>{row['Name']}</td><td>{int(row['Price'])}</td><td>{row['Rating']}</td></tr>"

        html += "</table>"
        display(HTML(html))

        respond("The top affordable products are displayed above.")

        # Best product
        best_product = df.loc[df['Rating'].idxmax()]
        respond(f"The overall best product in Flipkart is: {best_product['Name']} priced at ₹{int(best_product['Price'])} with a rating of {best_product['Rating']}.")

        # Open best product link
        webbrowser.open(best_product['Link'])

    except Exception as e:
        print(f"Error: {e}")
        respond("Something went wrong while fetching product details.")

# Entry point
time.sleep(1)
respond("Welcome to our virtual voice assistant. How can I help you?")
listening = True
while listening:
    data = listen()
    listening = voice_assistant(data)