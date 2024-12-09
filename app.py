import os
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import zipfile
from io import BytesIO

# Helper function to fetch the content of the page
def fetch_page(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return BeautifulSoup(response.content, "html.parser"), None
        else:
            return None, f"Failed to fetch the URL. Status code: {response.status_code}"
    except Exception as e:
        return None, str(e)

# Function to handle the image extraction and zip download
def extract_images(images, parsed_url):
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    image_urls = []
    for img_url in images:
        if img_url.startswith('http'):
            image_urls.append(img_url)
        else:
            image_urls.append(base_url + img_url)
    return image_urls

# App title
st.title("My Web Scraping App")

# Input URL
url = st.text_input("Enter the URL to scrape:")

# Keyword search input
keyword = st.text_input("Enter a keyword to search for (optional):")

# Sidebar options
with st.sidebar:
    st.header("Options")
    extract_headings = st.checkbox("Extract Headings")
    extract_links = st.checkbox("Extract Links")
    extract_paragraphs = st.checkbox("Extract Paragraphs")
    extract_images_option = st.checkbox("Extract Images")

# Scrape button
if st.button("Scrape"):
    if url:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            st.error("Invalid URL. Please enter a valid one (e.g., https://example.com).")
        else:
            # Fetch the page content
            soup, error = fetch_page(url)
            if error:
                st.error(error)
            else:
                st.success("Successfully fetched the page!")

                # URL Preview
                title = soup.title.string if soup.title else "No Title Found"
                st.write(f"**Page Title:** {title}")

                # Initialize extracted data
                headings, links, paragraphs, images = [], [], [], []

                # Extract data based on user selection
                if extract_headings:
                    headings = [h.text.strip() for h in soup.find_all(['h1', 'h2', 'h3'])]
                    st.subheader("Headings")
                    st.write(headings)

                if extract_links:
                    links = [(a.text.strip(), a['href']) for a in soup.find_all('a', href=True)]
                    st.subheader("Links")
                    st.write(links)

                if extract_paragraphs:
                    paragraphs = [p.text.strip() for p in soup.find_all('p')]
                    st.subheader("Paragraphs")
                    st.write(paragraphs)

                # Extract images if the option is selected
                if extract_images_option:
                    images = [img['src'] for img in soup.find_all('img', src=True)]
                    st.subheader("Images")
                    image_urls = extract_images(images, parsed_url)
                    for img_url in image_urls:
                        if img_url.startswith('http'):
                            st.image(img_url, caption=img_url, use_container_width=True)
                        else:
                            st.warning(f"Invalid image URL: {img_url}")

                # Keyword Search
                if keyword:
                    st.subheader(f"Results for Keyword: {keyword}")
                    keyword_results = {
                        "Headings": [h for h in headings if keyword.lower() in h.lower()],
                        "Paragraphs": [p for p in paragraphs if keyword.lower() in p.lower()],
                        "Links": [link for link in links if keyword.lower() in link[0].lower()]
                    }
                    for section, results in keyword_results.items():
                        if results:
                            st.write(f"**{section}:**")
                            st.write(results)

                # Word Cloud Feature
                if extract_paragraphs and paragraphs:
                    st.subheader("Word Cloud from Paragraphs")
                    all_text = " ".join(paragraphs)
                    wordcloud = WordCloud(
                        width=800, 
                        height=400, 
                        background_color="white"
                    ).generate(all_text)

                    # Display the word cloud
                    plt.figure(figsize=(10, 5))
                    plt.imshow(wordcloud, interpolation="bilinear")
                    plt.axis("off")
                    st.pyplot(plt)

                # Create a Zip file to store all images if extract_images is selected
                if extract_images_option and images:
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for idx, img_url in enumerate(image_urls):
                            try:
                                img_data = requests.get(img_url).content
                                img_name = f"image_{idx + 1}.jpg"
                                zip_file.writestr(img_name, img_data)
                            except Exception as e:
                                st.warning(f"Error downloading image {img_url}: {e}")

                    # Provide a download button for the zip file
                    zip_buffer.seek(0)
                    st.download_button(
                        label="Download All Images as ZIP",
                        data=zip_buffer,
                        file_name="images.zip",
                        mime="application/zip"
                    )

                # Download buttons for other data
                if headings:
                    st.download_button(
                        label="Download Headings as Text",
                        data="\n".join(headings),
                        file_name="headings.txt",
                        mime="text/plain"
                    )

                if links:
                    links_df = pd.DataFrame(links, columns=["Link Text", "URL"])
                    st.download_button(
                        label="Download Links as CSV",
                        data=links_df.to_csv(index=False),
                        file_name="links.csv",
                        mime="text/csv"
                    )

                if paragraphs:
                    st.download_button(
                        label="Download Paragraphs as Text",
                        data="\n".join(paragraphs),
                        file_name="paragraphs.txt",
                        mime="text/plain"
                    )

    else:
        st.warning("Please enter a valid URL.")
