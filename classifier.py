"""
classifier.py
-------------
Trains and uses a TF-IDF + Naive Bayes document classifier.

Categories: Finance, Resume, AI, Research, Personal, Other

The classifier is trained on a small hand-crafted seed corpus.
For real-world use you can replace / augment this corpus with
actual labelled documents.
"""

import logging
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seed training corpus
# Each tuple is (text, label).
# The texts are intentionally keyword-rich so the model learns quickly even
# with a tiny training set.
# ---------------------------------------------------------------------------
TRAINING_DATA = [
    # Finance
    ("invoice payment receipt bank account balance transaction credit debit tax revenue expenses budget quarterly earnings profit loss financial statement", "Finance"),
    ("annual report revenue profit loss earnings per share dividend stock market investment portfolio financial forecast balance sheet cash flow", "Finance"),
    ("tax return income deduction irs w2 federal state refund withholding payroll salary wages gross net fiscal year", "Finance"),
    ("mortgage loan interest rate amortization principal payment lender borrower credit score refinance down payment property insurance", "Finance"),
    ("budget spreadsheet monthly expenses rent utilities groceries savings emergency fund debt repayment net worth financial planning", "Finance"),

    # Resume
    ("resume curriculum vitae work experience education skills objective summary references bachelor master degree university college GPA", "Resume"),
    ("professional experience software engineer manager analyst developer intern employment history responsibilities achievements linkedin", "Resume"),
    ("skills python java c++ communication leadership teamwork problem solving microsoft office project management certified", "Resume"),
    ("cover letter application position job opening hiring company team role responsibilities qualifications salary expectation", "Resume"),
    ("career objective seeking position motivated dynamic team player years experience proficient detail oriented results driven", "Resume"),

    # AI
    ("artificial intelligence machine learning deep learning neural network model training dataset accuracy loss epoch optimizer", "AI"),
    ("natural language processing transformer BERT GPT attention mechanism tokenization embedding classification sentiment analysis", "AI"),
    ("computer vision convolutional neural network image recognition object detection segmentation ResNet ImageNet feature extraction", "AI"),
    ("reinforcement learning agent reward policy environment state action Q-learning deep Q-network exploration exploitation", "AI"),
    ("large language model prompt engineering fine tuning few shot zero shot inference hallucination alignment RLHF", "AI"),

    # Research
    ("abstract introduction methodology results conclusion references hypothesis experiment data analysis statistical significance p-value", "Research"),
    ("literature review peer reviewed journal publication citation index impact factor scholarly article empirical study findings", "Research"),
    ("research paper study participants sample size control group variable measurement observation qualitative quantitative", "Research"),
    ("university academic thesis dissertation committee defense graduate research grant funding proposal IRB ethics approval", "Research"),
    ("experiment protocol procedure lab report hypothesis null alternative standard deviation mean variance confidence interval", "Research"),

    # Personal
    ("dear diary today feeling happy sad birthday party family vacation trip holiday memories childhood friend", "Personal"),
    ("personal letter love family friend miss you hope well thinking of you best wishes warm regards sincerely", "Personal"),
    ("journal entry reflection gratitude mood thoughts feelings anxiety stress mindfulness meditation self-care routine", "Personal"),
    ("wedding anniversary birthday party invitation celebration guest list RSVP venue catering decoration photos memories", "Personal"),
    ("grocery list shopping errands laundry appointment doctor dentist reminder home maintenance personal tasks", "Personal"),

    # Other
    ("user manual installation guide troubleshooting FAQ instructions setup configuration system requirements steps procedure", "Other"),
    ("meeting agenda minutes action items follow up stakeholders project status update timeline milestone deliverable", "Other"),
    ("legal contract agreement terms conditions clause party obligation liability warranty disclaimer jurisdiction governing law", "Other"),
    ("recipe ingredients instructions cooking baking temperature oven stove kitchen food meal prep serving size", "Other"),
    ("news article event report announcement press release spokesperson comment statement update information coverage", "Other"),
]

CATEGORIES = ["Finance", "Resume", "AI", "Research", "Personal", "Other"]


class DocumentClassifier:
    """
    Wraps a scikit-learn TF-IDF → MultinomialNB pipeline.

    Usage
    -----
    clf = DocumentClassifier()
    clf.train()
    label = clf.predict("your document text here")
    """

    def __init__(self):
        self.pipeline: Pipeline | None = None
        self._is_trained = False

    def train(self) -> None:
        """Build and fit the TF-IDF + Naive Bayes pipeline on the seed corpus."""
        texts: List[str] = [text for text, _ in TRAINING_DATA]
        labels: List[str] = [label for _, label in TRAINING_DATA]

        self.pipeline = Pipeline([
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),   # unigrams + bigrams
                    sublinear_tf=True,    # apply log(1+tf)
                    min_df=1,
                    stop_words="english",
                ),
            ),
            ("clf", MultinomialNB(alpha=0.5)),
        ])

        self.pipeline.fit(texts, labels)
        self._is_trained = True
        logger.info("Classifier trained on %d samples.", len(texts))

    def predict(self, text: str) -> str:
        """
        Classify a single document text.

        Parameters
        ----------
        text : str
            The full extracted text of the document.

        Returns
        -------
        str
            One of the CATEGORIES labels.
        """
        if not self._is_trained:
            raise RuntimeError("Classifier has not been trained. Call train() first.")

        if not text or not text.strip():
            logger.warning("Empty text passed to classifier; defaulting to 'Other'.")
            return "Other"

        prediction = self.pipeline.predict([text])[0]
        probabilities = self.pipeline.predict_proba([text])[0]
        confidence = max(probabilities)

        logger.debug(
            "Predicted '%s' with confidence %.2f%%", prediction, confidence * 100
        )

        # Fall back to 'Other' when the model is uncertain
        if confidence < 0.20:
            logger.debug("Low confidence (%.2f) — returning 'Other'.", confidence)
            return "Other"

        return prediction
