import pandas as pd
import openpyxl
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba

# Function to load stop words from the file
def load_stopwords(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        stopwords = set(file.read().split())
    return stopwords

# Load the DataFrame from JSON
loaddf = pd.read_json("vector_all.json")
print("Load DataFrame from JSON Done")

# Load Chinese stop words
stopwords_file = "hit_stopwords.txt"
stopwords = load_stopwords(stopwords_file)
print("Load Chinese stop words Done")

# Generate a word cloud image
chinese_font_path = "jf-openhuninn-2.0.ttf"

def create_word_cloud(index, string):
    wordcloud = WordCloud(
        background_color="white",
        width=600,
        height=400,
        margin=2,
        font_path=chinese_font_path,
        prefer_horizontal=1,
        colormap="Set2",
        stopwords=stopwords,  # Pass the loaded stop words
    ).generate(string)
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    save_path = f"images/{index}.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')

# Function to tokenize and remove stop words
def tokenize_and_remove_stopwords(string):
    words = jieba.cut(string)
    return " ".join(w for w in words if w not in stopwords)

print("Start to tokenize and remove stop words")

# Tokenize and remove stop words for the 'content' column
loaddf["jieba_cut"] = loaddf["content"].apply(lambda x: tokenize_and_remove_stopwords(x))

print("Tokenize and remove stop words Done")

# Now you can use the 'loaddf' DataFrame with the 'jieba_cut' column, which contains the tokenized content without Chinese stop words.

print("Start to create word cloud")
loaddf.apply(lambda x: create_word_cloud(x.name, x["jieba_cut"]), axis=1)
print("Create word cloud Done")