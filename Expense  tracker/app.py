from flask import Flask, render_template, request, jsonify
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob
import nltk

app = Flask(__name__)

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Initialize NLTK tools
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

# Preprocess the input text
def preprocess_text(text):
    tokens = word_tokenize(text)
    filtered_tokens = [lemmatizer.lemmatize(word.lower()) for word in tokens if word.lower() not in stop_words and word.isalpha()]
    return ' '.join(filtered_tokens)

# Analyze sentiment using TextBlob
def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

# Generate comment based on sentiment polarity
def generate_comment(polarity):
    if polarity > 0.5:
        return "Great product! I love it."
    elif polarity < -0.5:
        return "Disappointing product. I wouldn't recommend it."
    else:
        return "Neutral product. It's average."

# Route for the homepage
@app.route('/')
def home():
    return render_template('index.html')

# Route for sentiment analysis and comment generation
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    text = data.get('text', '')

    # Preprocess the text, perform sentiment analysis
    filtered_text = preprocess_text(text)
    sentiment = analyze_sentiment(filtered_text)
    comment = generate_comment(sentiment)

    # Return the sentiment and the generated comment
    return jsonify({'sentiment': sentiment, 'comment': comment})

if __name__ == '__main__':
    app.run(debug=True)
